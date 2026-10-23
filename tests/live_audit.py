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
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SITE = (sys.argv[1] if len(sys.argv) > 1 else "https://sotaex.github.io/antinel-site").rstrip("/")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "AntinelSiteAudit/1.0 (+https://sotaex.github.io/antinel-site/)"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b"", url      # 404 也要拿正文：404 页本身是被审对象
    except Exception as e:
        return 0, str(e).encode(), url


def main():
    fails = []

    st, body, _ = get(SITE + "/sitemap.xml")
    if st != 200:
        print("sitemap 取不到：%s" % st)
        return 2
    urls = re.findall(r"<loc>(.*?)</loc>", body.decode("utf-8", "replace"))
    print("站点 %s\nsitemap %d 条\n" % (SITE, len(urls)))

    def one(u):
        st, b, final = get(u)
        return u, st, b, final

    with ThreadPoolExecutor(max_workers=6) as ex:
        rows = list(ex.map(one, urls))

    total = 0
    bad_status, bad_head, bad_h1, bad_md = [], [], [], []
    for u, st, b, _final in rows:
        total += len(b)
        path = u.replace(SITE, "") or "/"
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

    st, b, _ = get(SITE + "/no-such-page-xyz/")
    nf = b.decode("utf-8", "replace")

    print("L-01 sitemap 页面全 200 ｜ 坏 %d %s" % (len(bad_status), bad_status[:3]))
    print("L-02 title/description/canonical ｜ 坏 %d %s" % (len(bad_head), bad_head[:3]))
    print("L-03 唯一 h1 + lang ｜ 坏 %d %s" % (len(bad_h1), bad_h1[:3]))
    print("L-04 .md 镜像可达 ｜ 坏 %d %s" % (len(bad_md), bad_md[:3]))
    print("L-05 llms.txt 链接可达 ｜ 坏 %d %s" % (len(llms_bad), llms_bad[:3]))
    print("L-06 404 页 ｜ 状态 %s ｜ 有回首页链接 %s" % (st, "回首页" in nf or "首页" in nf))
    print("L-07 体积 ｜ 首页 %.1f KB ｜ 全部页面合计 %.0f KB"
          % (len(rows[0][2]) / 1024.0, total / 1024.0))

    ok = (not bad_status and not bad_head and not bad_h1 and not bad_md
          and not llms_bad and st == 404 and not fails)
    print("\n线上审核：%s" % ("全绿" if ok else "有问题，见上"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
