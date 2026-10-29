# -*- coding: utf-8 -*-
"""语言读数：把 J-31 / J-32 / J-34 的存量逐条打出来。

    python tests/lang_report.py             # 全部
    python tests/lang_report.py --long      # 只看超长句
    python tests/lang_report.py --passive   # 只看被动候选

判据只报总数，而且截断到 4 条——改文案时要知道「是哪几句」。
这个工具直接 import gen.build() 与 checks.lang_stats()，不另写一份抽取逻辑：
纸上算一套、判据里一套，改完对着自己那套验，测得再顺也是假的。
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import gen as G                      # noqa: E402
from lib import checks as K          # noqa: E402
from lib import sources as S         # noqa: E402


def load_pages():
    truth = S.load()
    facts = G.build_facts(truth)
    G.FACTS_CACHE.clear()
    G.FACTS_CACHE.extend(facts)
    pages, _stubs = G.build(truth, facts)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", action="store_true", help="只看超长句")
    ap.add_argument("--passive", action="store_true", help="只看被动候选")
    ap.add_argument("--full", action="store_true", help="被动候选不截断上下文")
    a = ap.parse_args()
    both = not (a.long or a.passive)

    st = K.lang_stats(load_pages())

    if both or a.long:
        print("超长句（中文 >%d 字 / 英文 >%d 词）：%d 处"
              % (K.BUDGET_LIMIT["zh"], K.BUDGET_LIMIT["en"], len(st["long"])))
        print("硬超（中文 >%d / 英文 >%d）：%d 处"
              % (K.LONG_LIMIT["zh"], K.LONG_LIMIT["en"], len(st["hard"])))
        for path, lang, s, n in st["long"]:
            print("\n[%s] %s  %d" % (lang, path, n))
            print("    " + s)

    if both or a.passive:
        print("\n被动候选：英文 %d、中文 %d"
              % (st["passive_en"], st["passive_zh"]))
        for path, lang, frag, s in st["passive"]:
            ctx = s if a.full else (s[:70] + ("…" if len(s) > 70 else ""))
            print("\n[%s] %s  «%s»" % (lang, path, frag))
            print("    " + ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
