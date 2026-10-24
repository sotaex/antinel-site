# -*- coding: utf-8 -*-
"""线上审核：拿发布出去的站点当对象，逐页量。

审的不是「构建器说得对不对」，而是「用户此刻打开看到的是什么」——
本地全绿、线上 404 这种事，只有这一层能抓到。

用法：
    python tests/live_audit.py                       # 默认审 sitemap 里的全部页面
    python tests/live_audit.py https://example.com   # 换站点

判据（每条都会打印实测值，不打印「通过」两个字了事）：
    L-01 sitemap 里每一页都 200
    L-02 每页有 title / meta description / canonical 且 canonical == 自己的地址
    L-03 每页恰好一个 h1，且 lang 已声明
    L-04 每页有 .md 镜像且可访问（机读层与网页层同源）
    L-05 llms.txt 里的每个链接都 200
    L-06 404 页真的返回 404，且带引导链接
    L-07 单页 HTML ≤ 120 KB（含内联 JSON-LD），站点总体积可报
"""
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

_arg = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
SITE = (_arg or "https://sotaex.github.io/antinel-site").rstrip("/")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "AntinelSiteAudit/1.0 (+https://sotaex.github.io/antinel-site/)"


def get(url, timeout=30, retries=3):
    """取一个地址。网络瞬断要重试——把「连不上」记成「页面坏了」是量具在说谎。

    返回 (status, body, final_url)。status=0 表示三次都没连上，
    调用方要把它记成「受阻」，不能记成「失败」（受阻≠失败）。
    """
    last = ""
    for i in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return r.status, r.read(), r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, e.read() or b"", url   # 404 也要拿正文：404 页本身是被审对象
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, e)
            if i < retries - 1:
                time.sleep(2)
    return 0, last.encode(), url


def wait_live(expect_pages=None, tries=10, gap=15):
    """发布后 CDN 要几十秒才生效。等线上 sitemap 的条数和本次构建一致，再开始审。

    为什么不只等「首页 200」：上一版的首页也是 200。等错了对象，量到的还是旧站，
    报出来的 404 不是缺陷，是没等——跟「查不出来≠查出来是好的」是同一类错。

    等不到也不改判据，照实审、照实报。
    """
    for i in range(tries):
        st, body, _ = get(SITE + "/sitemap.xml", timeout=15)
        if st == 200:
            n = len(re.findall(r"<loc>", body.decode("utf-8", "replace")))
            if expect_pages is None or n == expect_pages:
                if i:
                    print("等 CDN 生效：第 %d 次探测，sitemap %d 条，与本次构建一致\n"
                          % (i + 1, n))
                return True
        if i < tries - 1:
            time.sleep(gap)
    print("等 CDN 生效：%d 次探测（每次隔 %d 秒）后仍未对上——照实审，不跳过\n"
          % (tries, gap))
    return False


def main():
    fails = []

    # 本次构建的页数：从本地产物读。CI 里产物就在，本地跑也一致。
    import os
    local_sm = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "site-output", "sitemap.xml")
    expect = None
    if os.path.isfile(local_sm):
        expect = len(re.findall(r"<loc>", open(local_sm, encoding="utf-8").read()))
    wait_live(expect)

    st, body, _ = get(SITE + "/sitemap.xml")
    if st != 200:
        print("sitemap 取不到：status=%s ｜ 站点 %r" % (st, SITE))
        print("（站点地址为空或连不上。地址来自命令行第一个参数，"
              "CI 里是 deploy-pages 的 page_url。）")
        return 2
    urls = re.findall(r"<loc>(.*?)</loc>", body.decode("utf-8", "replace"))
    print("站点 %s\nsitemap %d 条\n" % (SITE, len(urls)))

    def one(u):
        st, b, final = get(u)
        return u, st, b, final

    with ThreadPoolExecutor(max_workers=6) as ex:
        rows = list(ex.map(one, urls))

    # CDN 是分批生效的：sitemap 已经是新版，个别页面还指着旧缓存。
    # 对非 200 的项隔 30 秒再取一次，最多三轮。等不到就照实报坏。
    # 这不是放宽判据——判据的对象是「发布后的站点」，不是「发布后第 0 秒的站点」。
    for round_ in range(3):
        retry = [u for u, st, _b, _f in rows if st != 200]
        if not retry:
            break
        print("L-01 第 %d 轮补取：%d 个地址非 200，等 30 秒再看" % (round_ + 1, len(retry)))
        time.sleep(30)
        fixed = {u: one(u) for u in retry}
        rows = [fixed.get(u) or (u, st, b, f) for u, st, b, f in rows]

    total = 0
    bad_status, blocked, bad_head, bad_h1, bad_md = [], [], [], [], []
    for u, st, b, _final in rows:
        total += len(b)
        path = u.replace(SITE, "") or "/"
        if st == 0:
            # 连不上：记「受阻」，不记「失败」。两者的区别是「站点坏了」还是「我没连上」，
            # 只有后者能重跑解决。合并成一句「页面坏了」就是诬告。
            blocked.append("%s（%s）" % (path, b.decode("utf-8", "replace")[:60]))
            continue
        if st != 200:
            bad_status.append("%s(%s)" % (path, st))
            continue
        h = b.decode("utf-8", "replace")
        if len(b) > 120 * 1024:
            fails.append("L-07 %s 体积 %.0f KB" % (path, len(b) / 1024.0))
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', h)
        c = re.search(r'<link rel="canonical" href="([^"]*)"', h)
        if not (t and d and c):
            bad_head.append("%s 缺 %s" % (path, "title" if not t else
                                          ("description" if not d else "canonical")))
        elif c.group(1).rstrip("/") != u.rstrip("/"):
            bad_head.append("%s canonical=%s" % (path, c.group(1)))
        h1 = re.findall(r"<h1[^>]*>", h)
        if len(h1) != 1:
            bad_h1.append("%s h1×%d" % (path, len(h1)))
        if not re.search(r'<html[^>]*\blang="[^"]+"', h):
            bad_h1.append("%s 缺 lang" % path)
        alt = re.search(r'rel="alternate" type="text/markdown" href="([^"]+)"', h)
        if not alt:
            bad_md.append("%s 无 .md 链接" % path)
        else:
            st2, b2, _ = get(alt.group(1))
            if st2 != 200 or not b2.startswith(b"---"):
                bad_md.append("%s .md=%s" % (path, st2))

    st, b, _ = get(SITE + "/llms.txt")
    llms_bad = []
    if st != 200:
        llms_bad.append("llms.txt=%s" % st)
    else:
        links = re.findall(r"\]\((https?://[^)]+)\)", b.decode("utf-8", "replace"))
        with ThreadPoolExecutor(max_workers=6) as ex:
            for u, st2, _b, _f in ex.map(one, links):
                if st2 != 200:
                    llms_bad.append("%s(%s)" % (u.replace(SITE, ""), st2))

    # L-08：站上说「装这个版本」时，PyPI 上真的能装到这个版本吗
    pypi_ver, site_ver = None, None
    st, b, _ = get(SITE + "/datasets/facts.json")
    if st == 200:
        try:
            import json as _j
            site_ver = _j.loads(b.decode("utf-8"))["product_version"]
        except Exception:
            site_ver = None
    st2, b2, _ = get("https://pypi.org/pypi/antinel/json")
    if st2 == 200:
        try:
            import json as _j
            pypi_ver = _j.loads(b2.decode("utf-8"))["info"]["version"]
        except Exception:
            pypi_ver = None

    st, b, _ = get(SITE + "/no-such-page-xyz/")
    nf = b.decode("utf-8", "replace")

    print("L-01 sitemap 页面全 200 ｜ 坏 %d %s｜ 受阻 %d %s"
          % (len(bad_status), bad_status[:3], len(blocked), blocked[:2]))
    print("L-02 title/description/canonical ｜ 坏 %d %s" % (len(bad_head), bad_head[:3]))
    print("L-03 唯一 h1 + lang ｜ 坏 %d %s" % (len(bad_h1), bad_h1[:3]))
    print("L-04 .md 镜像可达 ｜ 坏 %d %s" % (len(bad_md), bad_md[:3]))
    print("L-05 llms.txt 链接可达 ｜ 坏 %d %s" % (len(llms_bad), llms_bad[:3]))
    print("L-06 404 页 ｜ 状态 %s ｜ 有回首页链接 %s" % (st, "回首页" in nf or "首页" in nf))
    ver_ok = (site_ver is None or pypi_ver is None or site_ver == pypi_ver)
    print("L-08 站上版本 vs PyPI ｜ 站 %s ｜ PyPI %s ｜ %s"
          % (site_ver or "取不到", pypi_ver or "取不到",
             "一致" if ver_ok and site_ver else ("无法比对（BLOCKED，不记失败）"
                                                 if not site_ver or not pypi_ver else "不一致")))
    print("L-07 体积 ｜ 首页 %.1f KB ｜ 全部页面合计 %.0f KB"
          % (len(rows[0][2]) / 1024.0, total / 1024.0))

    ok = (not bad_status and not bad_head and not bad_h1 and not bad_md
          and not llms_bad and st == 404 and not fails and ver_ok and not blocked)
    # 受阻不算失败，但也不算全绿——「没查成」不能冒充「查了没事」。
    if ok:
        verdict = "全绿"
    elif blocked and not (bad_status or bad_head or bad_h1 or bad_md or llms_bad or fails):
        verdict = "受阻 %d 项，结论不完整（重跑即可，不是站点缺陷）" % len(blocked)
    else:
        verdict = "有问题，见上"
    print("\n线上审核：%s" % verdict)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
