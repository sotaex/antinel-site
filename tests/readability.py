# -*- coding: utf-8 -*-
"""人读层可读性量具（诊断用，不是判据）。

判据在 lib/checks.py（J-24~J-28），只卡几条硬线。这个脚本出的是分布：
每页多少术语、多少内部编号、句子多长、有没有重复叫法。

用法：
    python tests/readability.py            # 全部人读页
    python tests/readability.py /steward/  # 只看一页

为什么要有这个：判据只回答「过没过」，量具回答「差多少」。改文案时看量具。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import config as C          # noqa: E402
from lib import human as H           # noqa: E402

OUT = os.environ.get("SITE_OUT") or os.path.join(C.ROOT, "site-output")


def strip(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
    h = re.sub(r"<[^>]+>", "", h)
    return re.sub(r"[ \t]+", " ", h)


def sentences(txt):
    parts = re.split(r"[。！？；\n]+", txt)
    return [p.strip() for p in parts if len(p.strip()) >= 4]


def page_text(path):
    p = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" \
        else os.path.join(OUT, "index.html")
    if not os.path.isfile(p):
        return None
    h = open(p, encoding="utf-8").read()
    m = re.search(r'<main id="main"[^>]*>(.*?)</main>', h, re.S)
    return strip(m.group(1) if m else h)


def main(argv):
    want = [a for a in argv if a.startswith("/")]
    pages = want or H.HUMAN_PAGES
    rows = []
    for path in pages:
        txt = page_text(path)
        if txt is None:
            rows.append((path, None, 0, 0, 0, 0))
            continue
        terms = {t: txt.count(t) for t in H.TERMS if t in txt}
        internal = re.findall(r"\b(?:J-\d{2}|L[0-7]\b|B[1-5]\b|D-\d{2}|E\d{2,})\b", txt)
        bad = {w: txt.count(w) for w in H.BANNED if w in txt}
        sents = sentences(txt)
        avg = sum(len(s) for s in sents) / len(sents) if sents else 0
        rows.append((path, len(txt), sum(terms.values()), len(internal), sum(bad.values()), avg))

    print("%-18s %6s %6s %6s %6s %6s" % ("页面", "字数", "术语", "内部号", "禁用词", "均句长"))
    print("-" * 56)
    tot = [0, 0, 0, 0]
    for path, n, t, i, b, a in rows:
        if n is None:
            print("%-18s   页面不存在" % path)
            continue
        flag = " ←" if (t > 12 or i > 0 or b > 0) else ""
        print("%-18s %6d %6d %6d %6d %6.1f%s" % (path, n, t, i, b, a, flag))
        tot = [tot[0] + n, tot[1] + t, tot[2] + i, tot[3] + b]
    print("-" * 56)
    print("合计：%d 字｜术语 %d 次｜内部编号 %d 处｜禁用词 %d 处｜%d 页"
          % (tot[0], tot[1], tot[2], tot[3], len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
