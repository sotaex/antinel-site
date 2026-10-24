# -*- coding: utf-8 -*-
"""负控（negative control）：证明判据真的会红。

纪律（见 site-spec/07、08）：
  1. 先绿：干净副本跑一遍，必须全绿。
  2. 注入：改一处，目标判据必须变红 —— 不改就红的判据是假判据。
  3. 还原：撤销改动，必须重新全绿 —— 还原不了就说明改动不可逆，负控作废。

不做这三步的「负控」只是一次性快照，不是守卫。

用法：
    python tests/negctl/run.py            # 全跑
    python tests/negctl/run.py N-05 N-09  # 只跑指定几条

结果写 tests/negctl/last-run.json，构建期 J-16 会读它报「活力证据 X/N」。
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(HERE, "_work")
RUN = os.path.join(WORK, "run")
OUT = os.path.join(HERE, "last-run.json")

COPY = ["gen.py", "lib", "templates", "assets", "data", "content"]

LINE = re.compile(r"^\s*([\u2713\u2717])\s+(J-\d+[ab]?)\s+(.*)$")


def _files(rel):
    """把一个目录/文件展开成 (相对路径, 绝对路径) 列表。"""
    src = os.path.join(ROOT, rel)
    if os.path.isfile(src):
        return [(rel, src)]
    out = []
    for root, _d, fs in os.walk(src):
        for f in fs:
            p = os.path.join(root, f)
            out.append((os.path.relpath(p, ROOT), p))
    return out


def setup_work():
    """准备副本：只在不存在时拷一次。全程不删任何东西（宿主删除守卫会拦）。"""
    if os.path.isdir(RUN) and os.path.isfile(os.path.join(RUN, "gen.py")):
        return
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(RUN, exist_ok=True)
    for rel in COPY:
        for r, src in _files(rel):
            dst = os.path.join(RUN, r)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def restore_all():
    """还原 = 从仓根把源码与内容逐个覆盖回去。不删除，只覆盖。"""
    for rel in COPY:
        for r, src in _files(rel):
            dst = os.path.join(RUN, r)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def run_check():
    """在副本里跑 gen.py --check，返回 {判据: (ok, detail)} 与退出码。"""
    env = dict(os.environ)
    env["SITE_OUT"] = os.path.join(WORK, "_out")
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    p = subprocess.run([sys.executable, "gen.py", "--check"], cwd=RUN, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    res = {}
    for ln in (p.stdout or "").splitlines():
        m = LINE.match(ln)
        if m:
            res[m.group(2)] = (m.group(1) == "\u2713", m.group(3).strip())
    return res, p.returncode, (p.stdout or "") + (p.stderr or "")


# ---------------------------------------------------------------- 工具

def patch(rel, old, new, count=1):
    """按字面替换改一处；找不到就报错（防止补丁静默失效）。"""
    p = os.path.join(RUN, rel)
    s = open(p, encoding="utf-8").read()
    if old not in s:
        raise RuntimeError("注入失败：%s 里找不到锚点 %r" % (rel, old[:40]))
    open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, count))


def patch_json(rel, fn):
    p = os.path.join(RUN, rel)
    d = json.load(open(p, encoding="utf-8"))
    fn(d)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def append(rel, text):
    p = os.path.join(RUN, rel)
    s = open(p, encoding="utf-8").read()
    open(p, "w", encoding="utf-8", newline="\n").write(s + text)


def rename_away(rel):
    p = os.path.join(RUN, rel)
    os.replace(p, p + ".away")          # replace 可覆盖上一次留下的 .away


# ---------------------------------------------------------------- 注入动作
# 每条：编号、目标判据、人话说明、注入函数

def n01():
    """robots 少一条爬虫令牌。"""
    p = os.path.join(RUN, "data", "ua-tokens.txt")
    lines = [l for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]
    keep = [l for l in lines if l.strip() != "GPTBot"]      # 删掉一个「必须有」的
    if len(keep) == len(lines):
        raise RuntimeError("ua-tokens.txt 里没有 GPTBot，锚点失效")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(keep) + "\n")


def n02():
    """llms.txt 分组标题降级成三级，组数为 0。"""
    patch("gen.py", 'lines += ["", "## " + name]', 'lines += ["", "### " + name]')


def n03():
    """页面 head 去掉 .md 镜像链接。"""
    patch("templates/base.html", 'rel="alternate"', 'rel="alternate-off"')


def n04():
    """正文里插一个零宽空格。"""
    append("content/steward.md", "\n这一行末尾有一个看不见的字符：\u200b\n")


def n05():
    """正文里写一个错的规则数（36 ≠ 真值）。"""
    append("content/compare.md", "\n本站共 36 条护盾规则，分八类。\n")


def n06():
    """两页标题撞名（改正文 front-matter，title 以正文为准）。"""
    patch("content/brand.md", "title: 品牌与用词", "title: 常见问题")


def n07():
    """sitemap 多一条不存在的地址。"""
    patch("gen.py", '    sm += ["</urlset>", ""]',
          '    sm += ["  <url><loc>%s/ghost/</loc></url>" % (C.SITE_URL + C.BASE_PATH),'
          ' "</urlset>", ""]')


def n08():
    """md 镜像 front-matter 少 canonical。"""
    patch("gen.py", '"product_version: %s\\n---\\n\\n%s\\n"',
          '"pv: %s\\n---\\n\\n%s\\n"')


def n09():
    """JSON-LD 换成未登记的类型。"""
    patch("lib/render.py", '"@type": "TechArticle"', '"@type": "Thing"')


def n10():
    """规则页少一个要素（类别改叫分类）。"""
    patch("gen.py", "<dt>类别</dt>", "<dt>分类</dt>")


def n11():
    """引用块少指纹。"""
    patch("lib/render.py", "C.FINGERPRINT", '""')


def n12():
    """规则镜像改一个字节。"""
    p = os.path.join(RUN, "data", "sources", "rules.default.json")
    b = bytearray(open(p, "rb").read())
    b[-1] = b[-1] ^ 0x01
    open(p, "wb").write(bytes(b))


def n13():
    """正文加一个指向不存在页面的链接。"""
    append("content/compare.md", "\n见[这个页面不存在](/no-such-page/)。\n")


def n14():
    """llms-full 少拼一页。"""
    patch("gen.py", "    for p in pages:\n        body = re.sub",
          "    for p in pages[:-1]:\n        body = re.sub")


def n15():
    """正文里写死一个旧版本号。"""
    patch("content/brand.md", "**{{product_version}}**", "**0.55.2**")


def n16():
    """自证断言数改掉。"""
    patch_json("data/sources/truth.json",
               lambda d: d["selfproof"].update({"assertions_total": 999}))


def n17():
    """门归属改成恒定 Gate 1。"""
    patch("gen.py", '    segs = re.findall(r"Gate\\s*\\d+(?:\\s*/\\s*\\d+)*", v)',
          '    segs = ["Gate 1"]')


def n18():
    """宿主登记少一类。"""
    patch_json("data/sources/truth.json", lambda d: d["hosts"].pop())


def n19():
    """待发布的规则数据集被换成了另一份内容。"""
    patch("gen.py",
          '    rules_raw = open(os.path.join(C.DIR_SOURCES, "rules.default.json"), "rb").read()',
          '    rules_raw = open(os.path.join(C.DIR_SOURCES, "rules.default.json"), "rb").read() + b" "')


def n20():
    """删掉一页正文，留成占位页。"""
    rename_away("content/gates.md")


def n21():
    """次要文字调淡到对比度不足。"""
    patch("assets/site.css", "--ink-3: #5f6a78;", "--ink-3: #b9bfc6;")


def _resha():
    import hashlib
    p = os.path.join(RUN, "data", "sources", "rules.default.json")
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def n22():
    """首段塞一个术语。"""
    patch("content/steward.md",
          "一句话：监理不生产内容，也不替你做决定。",
          "一句话：监理不生产内容，也不替你管宿主。")


def n23():
    """人读页正文里露出内部判据号。"""
    append("content/compare.md", "\n这一条的写法沿用 J-99 的老规矩。\n")


def n24():
    """首页出现第二个主按钮。"""
    patch("gen.py",
          '\'<p><a class="linkmore" href="%s/docs/quickstart/">两分钟查一次 →</a></p>\\n\'',
          '\'<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">两分钟查一次</a></p>\\n\'')


def n25():
    """把一页的边界段标题改成不表边界的话。"""
    patch("content/gates.md", "## 门不等于隔离", "## 门和隔离的关系")


def n26():
    """人读页正文里出现营销词。"""
    append("content/compare.md", "\n用上它，你就是业界第一。\n")


def n27():
    """正文里塞一个跳级的标题（h2 直接到 h4）。"""
    patch("content/gates.md", "## 四道门各自挡什么",
          "## 四道门各自挡什么\n\n#### 跳级的小标题\n")


def n28():
    """同一句长话抄到两页上。"""
    line = "\n这句话是为了测试跨页重复而特意写下的同一串字符，长度肯定超过二十个字。\n"
    append("content/compare.md", line)
    append("content/license.md", line)


CONTROLS = [
    ("N-01", "J-02", "robots 少一条爬虫令牌", n01),
    ("N-02", "J-03", "llms.txt 少一个分组", n02),
    ("N-03", "J-04", "页面缺 .md 镜像链接", n03),
    ("N-04", "J-05", "正文插入零宽空格", n04),
    ("N-05", "J-06", "核心数字与事实不一致", n05),
    ("N-06", "J-07", "两页标题撞名", n06),
    ("N-07", "J-08", "sitemap 多一条幽灵地址", n07),
    ("N-08", "J-09", "md 镜像缺 front-matter 字段", n08),
    ("N-09", "J-10", "JSON-LD 用了未登记类型", n09),
    ("N-10", "J-11", "真源少一条规则", n10),
    ("N-11", "J-12", "引用块缺指纹", n11),
    ("N-12", "J-13", "规则镜像改一字节（应在装载时就 BLOCKED）", n12, "blocked"),
    ("N-13", "J-14a", "正文指向不存在页面", n13),
    ("N-14", "J-15", "llms-full 少拼一页", n14),
    ("N-15", "J-17", "正文写死旧版本号", n15),
    ("N-16", "J-18", "自证断言数被改", n16),
    ("N-17", "J-19", "门归属被写死", n17),
    ("N-18", "J-20", "宿主登记少一类", n18),
    ("N-19", "J-21", "待发布数据集被换成另一份", n19),
    ("N-20", "J-22", "正文缺失留成占位页", n20),
    ("N-21", "J-23", "次要文字调淡到对比度不足", n21),
    ("N-22", "J-24", "人读页首段塞一个术语", n22),
    ("N-23", "J-25", "人读页正文露出内部判据号", n23),
    ("N-24", "J-26", "首页出现第二个主按钮", n24),
    ("N-25", "J-27", "边界段标题改成不表边界的话", n25),
    ("N-26", "J-28", "人读页正文出现营销词", n26),
    ("N-27", "J-29", "正文塞一个跳级标题", n27),
    ("N-28", "J-30", "同一句长话抄到两页上", n28),
]


def main(argv):
    want = {a.upper() for a in argv if a.upper().startswith("N-")}
    todo = [c for c in CONTROLS if not want or c[0] in want]

    setup_work()
    restore_all()
    base, rc, log = run_check()
    if not base:
        print("基线跑不出判据，判据自己坏了：\n" + log[-2000:])
        return 2
    base_red = [k for k, v in base.items() if not v[0]]
    print("基线：%d 条判据，红 %d 条%s"
          % (len(base), len(base_red), ("：" + "、".join(base_red)) if base_red else ""))
    if base_red:
        print("基线不绿，负控无意义（先修红，再跑负控）。")
        return 2

    details = []
    for item in todo:
        cid, crit, desc, fn = item[:4]
        expect = item[4] if len(item) > 4 else "red"
        restore_all()
        try:
            fn()
        except Exception as e:
            details.append({"id": cid, "criterion": crit, "desc": desc,
                            "inject_ok": False, "red_ok": False, "restore_ok": False,
                            "detail": "注入失败：%s" % e})
            print("  ✗ %s 注入失败：%s" % (cid, e))
            continue
        after, rc2, log2 = run_check()
        if expect == "blocked":
            # 预期在装载阶段就被挡住（退出码非 0，且一条判据都没跑出来）
            red_ok = rc2 != 0 and not after
            detail = "装载阶段 BLOCKED（rc=%d）" % rc2 if red_ok else \
                "没有被挡住：rc=%d，跑了 %d 条判据" % (rc2, len(after))
        else:
            got = after.get(crit)
            red_ok = bool(got and not got[0])
            detail = (got[1] if got else "判据没出现") if red_ok else \
                ("注入后 %s 仍绿（说明它没看见）" % crit if got else "%s 根本没跑出来" % crit)
        # 还原 = 从仓根把文件覆盖回去，再跑一遍必须全绿
        restore_all()
        again, rc3, _log3 = run_check()
        restore_ok = bool(again) and all(v[0] for v in again.values())
        ok = red_ok and restore_ok
        details.append({"id": cid, "criterion": crit, "desc": desc,
                        "inject_ok": True, "expect": expect, "red_ok": red_ok,
                        "restore_ok": restore_ok, "detail": detail})
        print("  %s %s → %s｜%s｜还原%s｜%s"
              % ("✓" if ok else "✗", cid, crit,
                 "变红" if red_ok else "没红", "回绿" if restore_ok else "未回绿",
                 detail[:60]))

    passed = sum(1 for d in details if d["red_ok"] and d["restore_ok"])
    doc = {
        "schema": "antinel-site-negctl/1",
        "ran": len(details),
        "total": len(CONTROLS),
        "pass": passed,
        "baseline_criteria": len(base),
        "note": "每条三步：基线全绿 → 注入后目标判据变红 → 还原后全绿",
        "details": details,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("\n负控：%d/%d 通过（注入必红、还原必绿）" % (passed, len(details)))
    print("结果写 %s" % OUT)
    return 0 if passed == len(details) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
