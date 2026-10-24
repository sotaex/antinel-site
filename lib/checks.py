# -*- coding: utf-8 -*-
"""判据总表（site-spec/05 + 07）。

每条判据返回 (id, ok, detail)。红了 → 改代码，不许改判据。
判据与负控分离：负控在 tests/negctl/，用来证明「判据真的会红」。
"""
import json
import os
import posixpath
import re

from . import config as C
from . import human as H

INVISIBLE = [(0x200B, 0x200F), (0x2028, 0x202E), (0x2060, 0x2064),
             (0xFEFF, 0xFEFF), (0xE000, 0xF8FF), (0xE0000, 0xE007F)]

ALLOWED_LD = {"SoftwareApplication", "TechArticle", "FAQPage", "Dataset", "WebPage"}


def _has_invisible(s):
    for ch in s:
        o = ord(ch)
        for lo, hi in INVISIBLE:
            if lo <= o <= hi:
                return ch
    return None


def _strip_tags(h):
    return re.sub(r"<[^>]+>", "", h)


def _h1s(h):
    return re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S)


def _norm_path(href):
    """站内链接 → 归一化路径（去掉 BASE_PATH 与查询串）。"""
    if not href:
        return None
    if href.startswith(("http://", "https://", "mailto:", "#", "//", "javascript:")):
        return None
    p = href.split("#")[0].split("?")[0]
    if not p:
        return None
    if C.BASE_PATH and p.startswith(C.BASE_PATH):
        p = p[len(C.BASE_PATH):]
    if not p.startswith("/"):
        p = "/" + p
    return p


def _resolve(href, base):
    """相对链接按所在页解析成绝对站内路径。"""
    if not href or href.startswith(("http://", "https://", "mailto:", "#", "//", "javascript:")):
        return None
    p = href.split("#")[0].split("?")[0]
    if not p:
        return None
    if C.BASE_PATH and p.startswith(C.BASE_PATH + "/"):
        p = p[len(C.BASE_PATH):]
    if p.startswith("/"):
        full = p
    else:
        full = posixpath.normpath(posixpath.join(base, p))
    if (href.endswith("/") or p.endswith("/")) and not full.endswith("/"):
        full += "/"
    return full


def _md_target(url):
    """llms.txt 里的绝对 .md 地址 → 对应页面路径。"""
    p = _norm_path(url.replace(C.SITE_URL, ""))
    if p and p.endswith("/index.md"):
        p = p[:-len("/index.md")]
    return (p or "/").rstrip("/") or "/"


def _contrast(fg, bg):
    """WCAG 相对亮度对比度。"""
    def lum(h):
        h = h.lstrip("#")
        ch = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

        def f(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(ch[0]) + 0.7152 * f(ch[1]) + 0.0722 * f(ch[2])

    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def run_all(pages, machine, truth, facts, outdir, check_only=False, ds_files=None):
    results = []
    by_path = {p["path"]: p for p in pages}
    ver = truth["product_version"]
    paths = set(by_path)

    def add(jid, ok, detail):
        results.append({"id": jid, "ok": bool(ok), "detail": detail})

    # J-01 校验项计数非零
    n_ok = all([len(pages) > 0, len(facts) > 0, len(truth["rules"]) > 0,
                len(machine["llms"]) > 0, len(machine["robots"]) > 0])
    add("J-01", n_ok, "页 %d／事实 %d／规则 %d／llms %d 字节"
        % (len(pages), len(facts), len(truth["rules"]), len(machine["llms"])))

    # J-02 robots 覆盖全部令牌 + Sitemap 行
    # 光比对「文件里的令牌都在 robots 里」是同源自证：把行删掉，两边一起少，永远绿。
    # 所以另设一份必须存在的知名 AI 爬虫清单 —— 删行会立刻红。
    REQUIRED_UA = {"GPTBot", "ClaudeBot", "Google-Extended", "CCBot", "Bytespider"}
    ua = [l.strip() for l in open(os.path.join(C.DIR_DATA, "ua-tokens.txt"),
                                  encoding="utf-8").read().splitlines()
          if l.strip() and not l.strip().startswith("#")]
    missing = [t for t in ua if ("User-agent: " + t) not in machine["robots"]]
    lost = sorted(REQUIRED_UA - set(ua))
    add("J-02", not missing and not lost and "Sitemap: " in machine["robots"],
        "令牌 %d 个，缺 %d 个，必备缺 %d 个%s"
        % (len(ua), len(missing), len(lost), ("：" + "、".join(lost)) if lost else ""))

    # J-03 llms.txt 格式
    L = machine["llms"]
    h1 = re.findall(r"^# ", L, re.M)
    first_bq = L.find("> ")
    first_h2 = L.find("\n## ")
    links = re.findall(r"\]\(([^)]+)\)", L)
    pagekeys = {x.rstrip("/") or "/" for x in paths}
    dead = []
    for u in links:
        if not u.endswith(".md"):
            dead.append(u + "（非 .md）")
        elif _md_target(u) not in pagekeys:
            dead.append(u)
    groups = len(re.findall(r"^## ", L, re.M))
    nbytes = len(L.encode("utf-8"))
    # 按「部署后的大小」算。本地 BASE_PATH 为空时链接短，部署到项目页每条会多
    # /antinel-site 这 13 个字符。拿本地数判，会在本地绿、在 CI 红（2026-10-24 踩过）。
    pre = "" if C.BASE_PATH else "/antinel-site"
    ndeploy = nbytes + len(links) * len(pre.encode("utf-8"))
    add("J-03", len(h1) == 1 and 0 <= first_bq < first_h2 and groups >= 6
        and len(links) >= 20 and not dead and ndeploy <= 8192,
        "H1=%d 组=%d 链接=%d 死链=%d 字节=%d（部署后 %d）"
        % (len(h1), groups, len(links), len(dead), nbytes, ndeploy))

    # J-04 head 双链接 + .md 镜像
    # 必须认准 markdown 镜像那条（type="text/markdown"）：英文镜像上线后每页 head
    # 还多一条 hreflang 的 rel="alternate"，只查 "rel="alternate"" 会被语言链接
    # 满足——镜像链接整条没了也看不见。那正是 N-03 要注入的缺陷。
    bad = []
    for p in pages:
        if 'rel="alternate" type="text/markdown"' not in p["html"] \
                or 'rel="describedby"' not in p["html"]:
            bad.append(p["path"] + "(缺link)")
        if not p["md"].strip():
            bad.append(p["path"] + "(缺md)")
    add("J-04", not bad, "页 %d，异常 %d%s" % (len(pages), len(bad),
                                              ("：" + "、".join(bad[:3])) if bad else ""))

    # J-05 隐形字符
    hits = []
    for p in pages:
        for name, txt in (("html", p["html"]), ("md", p["md"])):
            ch = _has_invisible(txt)
            if ch:
                hits.append("%s.%s U+%04X" % (p["path"], name, ord(ch)))
    for name, txt in (("llms", machine["llms"]), ("llms-full", machine["full"]),
                      ("robots", machine["robots"])):
        ch = _has_invisible(txt)
        if ch:
            hits.append("%s U+%04X" % (name, ord(ch)))
    add("J-05", not hits, "命中 %d 处%s" % (len(hits), ("：" + "；".join(hits[:3])) if hits else ""))

    # J-06 核心数字一致（扫「N 条规则／N 类／N 道／N 类宿主」四类断言）
    rv = {c["id"]: c["value"] for c in facts}
    pats = [(r"(\d+)\s*条(?:护盾)?规则", rv["F-001"]["rules"]),
            (r"(\d+)\s*类(?:AI\s*工具)?宿主", rv["F-003"]["hosts"]),
            (r"(\d+)\s*道(?:审查门|闸门|门)", rv["F-001"]["gates"])]
    bad = []
    for p in pages:
        txt = _strip_tags(p["html"])
        for pat, want in pats:
            for m in re.finditer(pat, txt):
                if int(m.group(1)) != want:
                    bad.append("%s 「%s」≠%d" % (p["path"], m.group(0), want))
    add("J-06", not bad, "冲突 %d 处%s" % (len(bad), ("：" + "；".join(bad[:3])) if bad else ""))

    # J-07 title 唯一 + H1 唯一 + lead
    tcount, hcount, nolead = {}, {}, []
    for p in pages:
        t = p["title"]
        tcount[t] = tcount.get(t, 0) + 1
        h1 = _h1s(p["html"])
        if len(h1) != 1:
            hcount[p["path"]] = len(h1)
        if 'class="lead"' not in p["html"]:
            nolead.append(p["path"])
    dupt = [k for k, v in tcount.items() if v > 1]
    add("J-07", not dupt and not hcount and not nolead,
        "重名 title %d｜H1 数异常 %d｜缺 lead %d" % (len(dupt), len(hcount), len(nolead)))

    # J-08 sitemap 集合 == 页面集合
    locs = set(re.findall(r"<loc>(.*?)</loc>", machine["sitemap"]))
    want = {C.abs_url(p["path"]) for p in pages}
    add("J-08", locs == want, "sitemap %d 条，页 %d 条，差 %d"
        % (len(locs), len(want), len(locs ^ want)))

    # J-09 md 镜像 front-matter + H1 一致
    bad = []
    for p in pages:
        fm = re.match(r"^---\n(.*?)\n---\n", p["md"], re.S)
        if not fm:
            bad.append(p["path"] + "(缺front-matter)")
            continue
        keys = re.findall(r"^(\w+):", fm.group(1), re.M)
        need = {"title", "slug", "lang", "updated", "canonical", "product_version"}
        if not need.issubset(set(keys)):
            bad.append(p["path"] + "(front-matter 缺字段)")
    add("J-09", not bad, "异常 %d%s" % (len(bad), ("：" + "、".join(bad[:3])) if bad else ""))

    # J-10 JSON-LD
    bad = []
    for p in pages:
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', p["html"], re.S)
        if not m:
            bad.append(p["path"] + "(无 JSON-LD)")
            continue
        try:
            o = json.loads(m.group(1))
        except Exception as e:
            bad.append(p["path"] + "(解析失败:%s)" % type(e).__name__)
            continue
        if o.get("@type") not in ALLOWED_LD:
            bad.append(p["path"] + "(@type=%s)" % o.get("@type"))
        dm = o.get("dateModified")
        if dm and not re.match(r"^\d{4}-\d{2}-\d{2}", str(dm)):
            bad.append(p["path"] + "(dateModified 非 ISO)")
    add("J-10", not bad, "异常 %d%s" % (len(bad), ("：" + "、".join(bad[:3])) if bad else ""))

    # J-11 规则页 37 + 五要素。中英两份规则页各查各的词：
    # 英文页标签取真源自带英文，拿中文词查它等于永远绿——也等于永远没查。
    rp = [p for p in pages if p["path"].startswith("/rules/") and p["path"] != "/rules/"]
    rp += [p for p in pages
           if p["path"].startswith("/en/rules/") and p["path"] != "/en/rules/"]
    ids = [r["id"] for r in truth["rules"]]
    slugs = {p["path"].strip("/").split("/")[-1] for p in rp}
    miss = [i for i in ids if i.lower() not in slugs]
    nzh = len([p for p in rp if p["lang"] != "en"])
    nen = len([p for p in rp if p["lang"] == "en"])
    bad = []
    for p in rp:
        h = p["html"]
        need = ("Category", "Severity", "When it fires", "What to do") \
            if p["lang"] == "en" else ("类别", "级别", "触发情形", "处置建议")
        for n in need:
            if n not in h:
                bad.append(p["path"] + "缺" + n)
        if not re.search(r"<h1>%s" % re.escape(p["path"].strip("/").split("/")[-1].upper()), h):
            bad.append(p["path"] + "缺编号")
    add("J-11", nzh == len(ids) and nen == len(ids) and not miss and not bad,
        "规则页 中 %d／英 %d／真源 %d，缺 %d，要素缺 %d"
        % (nzh, nen, len(ids), len(miss), len(bad)))

    # J-12 引用块五要素。中英两份外壳各查各的词：
    # 中文页查「产品版本／数据日期」，英文镜像页查 "product version" / "data date"。
    # 英文页若还按中文查，引用块永远缺两项——那不是产品坏了，是量具只认一种语言。
    bad = []
    for p in pages:
        h = p["html"]
        m = re.search(r'<div class="cite">(.*?)</div>', h, re.S)
        if not m:
            bad.append(p["path"] + "(无引用块)")
            continue
        c = m.group(1)
        need = ((C.FINGERPRINT, C.LICENSE_TEXT, "product version", "data date", C.SITE_URL)
                if p["lang"] == "en" else
                (C.FINGERPRINT, C.LICENSE_TEXT, "产品版本", "数据日期", C.SITE_URL))
        for x in need:
            if x not in c:
                bad.append("%s 缺 %s" % (p["path"], x[:12]))
    add("J-12", not bad, "异常 %d%s" % (len(bad), ("：" + "、".join(bad[:3])) if bad else ""))

    # J-13 数据集四件
    src = open(os.path.join(C.DIR_SOURCES, "rules.default.json"), "rb").read()
    import hashlib
    ok13 = hashlib.sha256(src).hexdigest() == truth["rules_sha256"]
    for c in facts:
        if c["id"] == "F-007":
            ok13 = ok13 and c["value"]["assertions"] == truth["selfproof"]["assertions_total"]
    add("J-13", ok13, "规则镜像与真源逐字节一致=%s；数据集四件已生成"
        % ("是" if ok13 else "否"))

    # J-14a 内部链接全部可达
    known = set(paths) | {"/llms.txt", "/llms-full.txt", "/llms-en.txt",
                          "/robots.txt", "/sitemap.xml",
                          "/404.html", "/.well-known/security.txt",
                          "/assets/site.css", "/assets/copy.js", "/assets/favicon.svg",
                          "/datasets/", "/datasets/rules@%s.json" % ver,
                          "/datasets/facts.json", "/datasets/hosts@%s.json" % ver,
                          "/datasets/verdicts.json"}
    dead = []
    known_slash = {k.rstrip("/") + "/" for k in known}
    for p in pages:
        base = p["path"] if p["path"].endswith("/") else p["path"].rsplit("/", 1)[0] + "/"
        for href in re.findall(r'href="([^"]+)"', p["html"]):
            q = _resolve(href, base)
            if q is None:
                continue
            if q in known or q.rstrip("/") in known or q in known_slash:
                continue
            dead.append("%s → %s" % (p["path"], href))

    # J-14a 第二项：BASE_PATH 非空时，站内绝对链接必须带前缀。
    # 为什么 _resolve() 抓不到这一项：它先把 BASE_PATH 剥掉再比对，
    # 所以「漏了前缀」的链接在死链检查里看起来是好的——线上点下去全是 404，
    # 判据全绿。2026-10-24 线上实测：/steward/ 页的「规则目录」指向
    # https://sotaex.github.io/rules/，域名根下没有这个页面。
    # 生成页的链接都走 base 前缀，会漏的只有手写内容里的那一种。
    noprefix = []
    if C.BASE_PATH:
        for p in pages:
            for href in re.findall(r'href="([^"]+)"', p["html"]):
                if href.startswith("/") and not href.startswith("//") \
                        and not href.startswith(C.BASE_PATH + "/"):
                    noprefix.append("%s → %s" % (p["path"], href))
    add("J-14a", not dead and not noprefix,
        "死链 %d｜漏前缀 %d%s" % (len(dead), len(noprefix),
                                ("：" + "；".join(noprefix[:3])) if noprefix else ""))

    # J-15 llms-full
    nbytes = len(machine["full"].encode("utf-8"))
    secs = machine["full"].count("\n---\n\n# ")
    head6 = len([l for l in machine["full"].splitlines()[:8] if l.startswith(">")])
    add("J-15", nbytes <= 500 * 1024 and secs == len(pages) and head6 >= 6,
        "%d KB｜段 %d／页 %d｜头部说明 %d 行" % (nbytes // 1024, secs, len(pages), head6))

    # J-17 版本同源
    bad = []
    for p in pages:
        for m in re.finditer(r"0\.5\d\.\d", _strip_tags(p["html"])):
            if m.group(0) != ver:
                bad.append("%s:%s" % (p["path"], m.group(0)))
    for m in re.finditer(r"0\.5\d\.\d", machine["llms"] + machine["full"]):
        if m.group(0) != ver:
            bad.append("机读层:%s" % m.group(0))
    add("J-17", not bad, "异版本 %d 处%s" % (len(bad), ("：" + "、".join(bad[:3])) if bad else ""))

    # J-18 自证数字同源：从 raw 原文重新解析，与结构化字段对照。
    # （旧版拿 assertions 比 assertions_total，两个值同源，永远绿 —— 假守卫。）
    sp = truth["selfproof"]
    raw = sp.get("raw") or ""
    ma = re.search(r"assertions\s+(\d+)\s*/\s*(\d+)", raw)
    md_ = re.search(r"(\d+)\s*/\s*(\d+)\s+digests", raw)
    parsed_a = int(ma.group(2)) if ma else None
    parsed_d = int(md_.group(2)) if md_ else None
    f7 = [c for c in facts if c["id"] == "F-007"][0]["value"]
    add("J-18", parsed_a is not None and parsed_d is not None
        and parsed_a == sp.get("assertions_total") == f7["assertions"]
        and parsed_d == sp.get("digests") == f7["digests"],
        "原文解析 %s 断言／%s 摘要；快照 %s／%s；F-007 %s／%s"
        % (parsed_a, parsed_d, sp.get("assertions_total"), sp.get("digests"),
           f7["assertions"], f7["digests"]))

    # J-19 门归属同源
    bad = []
    for r in truth["rules"]:
        segs = re.findall(r"Gate\s*\d+(?:\s*/\s*\d+)*", truth["gates"].get(r["category"], ""))
        want = sorted({int(n) for s in segs for n in re.findall(r"\d+", s)})
        p = by_path.get("/rules/%s/" % r["id"].lower())
        if not p:
            bad.append(r["id"] + "(缺页)")
            continue
        got = sorted({int(n) for n in re.findall(r"Gate (\d)", p["html"])})
        if got != want:
            bad.append("%s 页 %s≠源 %s" % (r["id"], got, want))
    add("J-19", not bad, "不符 %d%s" % (len(bad), ("：" + "；".join(bad[:3])) if bad else ""))

    # J-20 宿主计数：拿快照里的文件清单当独立锚。
    # （旧版拿 len(hosts) 比 F-003，而 F-003 就是从 hosts 算出来的 —— 假守卫。）
    files = truth.get("hosts_files")
    add("J-20", bool(files) and len(truth["hosts"]) == len(files)
        == rv["F-003"]["hosts"],
        "登记文件 %s 个／解析 %d 类／F-003 写 %d"
        % (len(files) if files else "?", len(truth["hosts"]), rv["F-003"]["hosts"]))

    # J-21 发布出去的数据集与快照同源。
    # 锁本身在 load() 就前置校验（对不上直接 BLOCKED，构建不往下走），
    # 所以这里查链条的第二段：要发出去的那份 rules@ver.json，是不是快照那一份。
    import hashlib as _h
    payload = None
    for n, _d, b in (ds_files or []):
        if n.startswith("rules@"):
            payload = b
    lock = truth.get("rules_sha256") or ""
    got = _h.sha256(payload).hexdigest() if payload else ""
    add("J-21", bool(payload) and got == lock,
        "锁 %s… ｜ 待发布 %s…" % (lock[:12], (got[:12] or "缺")))

    # J-22 无占位页
    stubs = [p["path"] for p in pages if "callout stub" in p["html"]]
    add("J-22", not stubs, "占位页 %d%s" % (len(stubs), ("：" + "、".join(stubs[:5])) if stubs else ""))

    # J-23 文字对比度（WCAG AA 4.5:1）。人眼估不出来，所以量出来。
    low = []
    try:
        css = open(os.path.join(C.DIR_ASSETS, "site.css"), encoding="utf-8").read()
        blocks = re.findall(r":root\s*\{(.*?)\}", css, re.S)
        vars_ = {}
        for i, b in enumerate(blocks):
            d = dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})", b))
            vars_[i] = d
        light, dark = vars_.get(0, {}), vars_.get(1, vars_.get(0, {}))
        for mode, d in (("浅色", light), ("深色", dark)):
            bg = d.get("--paper", "#ffffff")
            for name in ("--ink", "--ink-2", "--ink-3", "--accent", "--warn"):
                fg = d.get(name)
                if not fg:
                    continue
                r = _contrast(fg, bg)
                if r < 4.5:
                    low.append("%s %s=%.2f" % (mode, name, r))
    except Exception as e:
        low.append("读不出配色：%s" % type(e).__name__)
    add("J-23", not low, "低于 4.5:1 的 %d 项%s"
        % (len(low), ("：" + "、".join(low[:4])) if low else ""))

    # ---- 人读层五条（J-24 ~ J-28）----
    # 这一组查的是「给不搞技术的人看的那几页」写得像不像话。
    # 人读页清单在 lib/human.py 的 HUMAN_PAGES，术语表在 TERMS，禁用词在 BANNED。
    # 判据只读那两张表，不在这里另写一份词表——否则改一处漏一处。
    human = [p for p in pages if p["path"] in H.HUMAN_PAGES]
    missing_human = [x for x in H.HUMAN_PAGES if x not in {p["path"] for p in pages}]
    if missing_human:
        add("J-24", False, "清单里的页不存在：%s" % "、".join(missing_human))
    else:
        # J-24 首段无术语。首段是唯一保证被读的一段，术语出现在这里，读者立刻掉队。
        # 术语表按页的语言取：中文页查 TERMS，英文镜像页查 TERMS_EN。
        # 英文页若不进这套判据，镜像页就可以随便堆术语——那正是镜像最容易烂的地方。
        bad = []
        for p in human:
            m = re.search(r'<p class="lead">(.*?)</p>', p["html"], re.S)
            if not m:
                continue
            txt = _strip_tags(m.group(1))
            hits = [t for t in H.human_terms(p["lang"]) if t in txt]
            if hits:
                bad.append("%s（%s）" % (p["path"], "、".join(hits)))
        add("J-24", not bad, "首段含术语的页 %d%s"
            % (len(bad), ("：" + "；".join(bad[:4])) if bad else ""))

        # J-25 内部编号不外露。产品自己的编号（SEC-01 这类规则号）必须留，
        # 禁的是我们自己干活用的号：J-xx 判据号、L0~L7 闸门层、B1~B5 批次、D-xx 决策号。
        INTERNAL = re.compile(r"\b(?:J-\d{2}|L[0-7]\b|B[1-5]\b|D-\d{2}|E\d{2,})\b")
        leaks = []
        for p in human:
            txt = _strip_tags(re.sub(r"<(code|pre)[^>]*>.*?</\1>", "", p["html"], flags=re.S))
            got = sorted(set(INTERNAL.findall(txt)))
            if got:
                leaks.append("%s（%s）" % (p["path"], "、".join(got)))
        add("J-25", not leaks, "内部编号外露的页 %d%s"
            % (len(leaks), ("：" + "；".join(leaks[:4])) if leaks else ""))

        # J-26 每页最多一个主按钮。两个主按钮＝读者不知道点哪个。
        many = []
        for p in human:
            n = p["html"].count('class="btn primary"')
            if n > 1:
                many.append("%s（%d）" % (p["path"], n))
        add("J-26", not many, "主按钮超过 1 个的页 %d%s"
            % (len(many), ("：" + "、".join(many[:4])) if many else ""))

        # J-27 边界段必有。只讲能做什么、不讲做不到什么，就不是监理。
        # 关键词按页的语言取：中文查 EDGE_WORDS，英文镜像页查 EDGE_WORDS_EN。
        # 比对前先把 h2 文本转小写：英文页写「Limits」而词表里是「limits」，
        # 大小写敏感会让一条真的边界段因为首字母大写被判缺失——那是量具误报。
        noedge = []
        for p in human:
            hs = re.findall(r"<h2[^>]*>(.*?)</h2>", p["html"], re.S)
            words = H.human_edge_words(p["lang"])
            if not any(w in _strip_tags(h).lower() for h in hs for w in words):
                noedge.append(p["path"])
        add("J-27", not noedge, "缺边界段的页 %d%s"
            % (len(noedge), ("：" + "、".join(noedge[:5])) if noedge else ""))

        # J-28 禁用词。全站查，不只人读页——营销词出现在任何一页都掉价。
        # 两处要让路，都是为了卡住「我们自己的话」而不是卡词面：
        #   1) 剥掉 <code>/<pre>：那里面是引述（品牌页列举我们不用哪些词）。
        #   2) 二级词（绝对／100%）往前看一小段，有否定词就算引述或否定。
        # 词表按页的语言取：中文页查 BANNED，英文镜像页查 BANNED_EN。
        DENY = ("不", "非", "没", "无", "别", "禁止", "勿", "拒绝")
        DENY_EN = ("not", "no ", "never", "cannot", "won't", "don't", "isn't",
                   "aren't", "without")
        found = []
        for p in pages:
            txt = _strip_tags(re.sub(r"<(code|pre)[^>]*>.*?</\1>", "", p["html"], flags=re.S))
            banned, soft = H.human_banned(p["lang"])
            deny = DENY_EN if p["lang"] == "en" else DENY
            for w in banned:
                if w in txt:
                    found.append("%s「%s」" % (p["path"], w))
            for w in soft:
                for m in re.finditer(re.escape(w), txt):
                    ctx = txt[max(0, m.start() - 24):m.start()].lower()
                    if not any(d in ctx for d in deny):
                        found.append("%s「%s」" % (p["path"], w))
                        break
        add("J-28", not found, "禁用词 %d 处%s"
            % (len(found), ("：" + "；".join(found[:4])) if found else ""))

        # J-29 标题层级不跳级（h2 不能直接到 h4）。屏幕阅读器按层级导航，
        # 跳级会让目录念错。纯结构问题，与文案无关。
        jump = []
        for p in pages:
            hs = [int(x) for x in re.findall(r"<h([1-6])[ >]", p["html"])]
            for a, b in zip(hs, hs[1:]):
                if b - a > 1:
                    jump.append("%s（h%d→h%d）" % (p["path"], a, b))
                    break
        add("J-29", not jump, "标题跳级的页 %d%s"
            % (len(jump), ("：" + "、".join(jump[:4])) if jump else ""))

        # J-30 人读页之间不许有长句重复。同一句话在两页出现，说明有一页在复述，
        # 读者要读两遍。规则页的元数据表不算——那是模板产物，本来就该一样。
        # 断句标点中英都收：。！？ 与 .!?。英文不按句号断，「It is what it is」
        # 这类二十字母以上的重复就查不出来。
        # 按语言分开比：这条判据防的是「一个读者在同一站里读到两遍」。
        # 中文页和它的英文镜像都写着 `antinel host-shield status`，那是同一份
        # 参考数据的两种语言，不是某一页在复述——没有读者会同时读两页。
        # 跨语言比会把这种正常情况报成重复，判据就没人信了。
        seen = {}
        dup = []
        for p in human:
            m = re.search(r'<main id="main"[^>]*>(.*?)</main>', p["html"], re.S)
            txt = _strip_tags(m.group(1) if m else p["html"])
            for s in re.split(r"[。！？.!?\n]", txt):
                s = re.sub(r"\s+", "", s)
                if len(s) < 20:
                    continue
                key = (p["lang"], s)
                if key in seen and seen[key] != p["path"]:
                    dup.append("%s＝%s" % (seen[key], p["path"]))
                seen.setdefault(key, p["path"])
        add("J-30", not dup, "跨页重复长句 %d%s"
            % (len(dup), ("：" + "；".join(dup[:3])) if dup else ""))

    # ---- J-16 英文镜像 ----
    # 三条一起查，缺一条镜像就是坏的：
    #   1. 一一对应：每个中文页都有一个 /en/ 同题页，反过来也一样。
    #      多出来或漏掉都算——「多了」同样危险，那意味着有一页没人维护。
    #   2. front-matter 的 lang 与路径一致。/en/ 下写 zh、中文页写 en，都算错。
    #   3. 数字跨语言一致：英文页写 "37 shield rules"，中文页写「37 条规则」，
    #      两边的 37 必须都等于真源。这条是镜像最容易静默错的地方——
    #      翻译时把数改了，两边各自都「看起来对」。
    zh_paths = {p["path"] for p in pages if p["lang"] != "en"}
    en_paths = {p["path"] for p in pages if p["lang"] == "en"}
    want_en = {("/en/" if p == "/" else "/en" + p) for p in zh_paths}
    want_zh = {("/" if p == "/en/" else p[3:]) for p in en_paths}
    only_zh = sorted(zh_paths - want_zh)
    only_en = sorted(en_paths - want_en)
    badlang = [p["path"] for p in pages
               if (p["path"].startswith("/en/")) != (p["lang"] == "en")]

    # 数字一致性：中文查「N 条规则／N 类宿主／N 道门」，英文查英文说法。
    # 正则各自写，但**要拿的真值同一个**（facts 里的 value），不另算一遍。
    rv = {c["id"]: c["value"] for c in facts}
    numbad = []
    for p in pages:
        txt = _strip_tags(p["html"])
        pats = ([(r"(\d+)\s*条(?:护盾)?规则", rv["F-001"]["rules"]),
                 (r"(\d+)\s*类(?:AI\s*工具)?宿主", rv["F-003"]["hosts"]),
                 (r"(\d+)\s*道(?:审查门|闸门|门)", rv["F-001"]["gates"])]
                if p["lang"] != "en" else
                [(r"(\d+)\s*shield rules", rv["F-001"]["rules"]),
                 (r"(\d+)\s*kinds of AI tool hosts", rv["F-003"]["hosts"]),
                 (r"(\d+)\s*review gates", rv["F-001"]["gates"])])
        for pat, want in pats:
            for m in re.finditer(pat, txt):
                if int(m.group(1)) != want:
                    numbad.append("%s 「%s」≠%d" % (p["path"], m.group(0), want))
    add("J-16", not (only_zh or only_en or badlang or numbad),
        "镜像 中 %d／英 %d｜缺对应 中 %d 英 %d｜lang 错 %d｜数字跨语言冲突 %d"
        % (len(zh_paths), len(en_paths), len(only_zh), len(only_en),
           len(badlang), len(numbad)))


    failed = [r for r in results if not r["ok"]]
    return {"results": results, "failed": len(failed),
            "passed": len(results) - len(failed), "total": len(results)}


def negctl_status():
    p = os.path.join(C.ROOT, "tests", "negctl", "last-run.json")
    if not os.path.isfile(p):
        return {"ran": 0, "total": 0, "pass": 0, "note": "未跑"}
    try:
        d = json.load(open(p, encoding="utf-8"))
        return {"ran": d.get("ran", 0), "total": d.get("total", 0),
                "pass": d.get("pass", 0), "note": d.get("note", "")}
    except Exception:
        return {"ran": 0, "total": 0, "pass": 0, "note": "读数失败"}


def report(res):
    nc = negctl_status()
    lines = ["", "判据：%d 绿 / %d 红 ｜ 活力证据 %d/%d（负控）｜ 占位页由 J-22 单列"
             % (res["passed"], res["failed"], nc["pass"], nc["total"])]
    for r in res["results"]:
        lines.append("  %s %-6s %s" % ("✓" if r["ok"] else "✗", r["id"], r["detail"]))
    return "\n".join(lines)
