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
    """规则页少一个要素（类别改叫分类），中英两边各改一处。

    锚点跟着代码走：标签早已收进 page_rule 的 L 字典，不再是裸 <dt>类别</dt>。
    J-11 按语言取词表后，只改中文只能证明中文那条分支会红——英文分支
    （37 页）也得有人证明它看得见，否则那半边是没负控的判据。
    """
    patch("gen.py", '"cat": "类别"', '"cat": "分类"')
    patch("gen.py", '"cat": "Category"', '"cat": "Class"')


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


def n29():
    """英文镜像少一页：把 /en/verdicts/ 的注册摘掉，中文那页就没有对应了。

    这是 J-16 的第一条（一一对应）。摘法必须是真的「不生成那一页」——
    把标题改掉不算，那样页还在，只是名字变了，判据不该红。
    """
    patch("gen.py",
          '    h, m = page_verdicts_en(truth)\n'
          '    add("/en/verdicts/", "The six verdicts · Antinel Steward",',
          '    h, m = page_verdicts_en(truth)\n'
          '    if False:\n'
          '        add("/en/verdicts/", "The six verdicts · Antinel Steward",')


def n30():
    """英文镜像写错一个数字：37 条规则写成 36 条。

    这是 J-16 的第三条（数字跨语言一致）。中文那边是对的，只有英文错——
    两边各自「看起来都对」，只有跨语言比一遍才发现。
    """
    append("content/en/faq.md",
           "\nAntinel Steward ships with 36 shield rules in total, all of them "
           "documented on this site.\n")


def n31():
    """分享预览图被挪走：og:image 还在，图没了。

    这一类缺陷没有任何「看起来坏了」的表象——页面照常打开，只是别人
    分享这个链接时只剩一句标题。J-14a 第三项就是为它设的。
    """
    rename_away(os.path.join(RUN, "assets", "og-cover.png"))


def n32():
    """正文写死一个**当前族**的旧版本号（0.60.1）。

    ★ 为什么单立一条：N-15 注入的是 0.55.2，正落在旧判据 `0\\.5\\d\\.\\d`
      的口径里，所以它一直绿——而产品已经走到 0.60，那条判据对新族
      完全看不见。同一条判据、同一个注入动作、只换了一个值，结论就反了。
      这正是「负控只喂老形状的样本」那一族的漏洞：负控绿不代表判据有牙，
      只代表它对**那一族的输入**有牙。
    """
    patch("content/brand.md", "**{{product_version}}**", "**0.60.1**")


def n33():
    """在代码示例里写死一个旧版本号（0.60.1）。

    ★ 为什么单立一条：J-17 原来扫之前先把 <code>/<pre> 与 ``` 围栏整段剥掉，
      理由是「代码示例不是产品版本声明」。而 `hook_protocol_version` 恰恰
      就是写死在示例里的 0.33.1，烂了两个月，全站判据一条没红。示例也是
      承诺：读者照着抄，抄到的就是一个不存在的数。
      N-32 注入的是正文，这条注入的是代码块——同一条判据、同一个错值，
      只换落点，结论必须一样。
    """
    patch("content/docs/agent.md", '"python": "3.13.x"',
          '"python": "3.13.x", "checked_in": "0.60.1"')


def n34():
    """英文正文句末写一个旧版本号，后面紧跟句号（0.60.1.）。

    ★ 为什么单立一条：J-17 的正则收尾原来是 `(?![\\d.])`，为的是挡掉
      0.60.12 / 1.0.60.1 这类更长的串——代价是英文里最自然的写法
      「… published as 0.60.1.」永远匹配不到。挡长串与漏句号，原来选了挡长串。
      这条注入的就是那个被漏掉的形状。
    """
    append("content/en/license.md", "\nThe previous release was published as 0.60.1.\n")


def n35():
    """真源快照里的规则被清空：J-01（输入计数非零）必须当场红。

    ★ 为什么补这一条：30 条判据里只有 J-01 一直没有反例。它是全站唯一一条
      「输入空了也得说话」的底线，而按纪律，没有反例的判据一律算没牙——
      哪怕它看起来永远绿。注入只清快照里的 rules 列表，不动规则镜像本身，
      所以不会先被 J-13 的字节锁挡在装载阶段（那样就测不到 J-01 了）。
    """
    p = os.path.join(RUN, "data", "sources", "truth.json")
    d = json.load(open(p, encoding="utf-8"))
    d["rules"] = []
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def n36():
    """中文正文塞一句 80 字的长句：J-31（句长上限）必须当场红。

    ★ 句长不是文风偏好。这一页的读者是要判断「这东西该不该装」的人，
      一句话读到第五个逗号就掉队了，后面写什么都没用。
      ASD-STE100 给描述句的上限是 25 词；本站还达不到（J-32 记着差多少），
      但 70 字这条红线不许越。
    """
    append("content/faq.md",
           "\n这一句是为了验证句长判据真的会红而写的，它故意连着用逗号，"
           "把好几件本来可以分开说的事情串在同一句里，读者读到一半就会忘记"
           "前面说了什么，读到最后也不知道重点在哪里。\n")


def n37():
    """塞一句六十几个字的话：只有 J-32（长句存量）该红，J-31 应当仍然绿。

    ★ 为什么单立一条：J-31 管硬上限，J-32 管存量封顶。只测 J-31 的话，
      「只差一点点」的那一段没人守——而文风就是这样一点点滑回去的。
      这条同时证明两条判据不是同一件事：同一个注入，只有一条红。
    """
    append("content/faq.md",
           "\n这一句大概有六十几个字，它没有越过七十字的红线，但越过了"
           "五十字的存量线，所以只有长句存量那一条会红，句长上限那一条"
           "仍然是绿的。\n")


def n38():
    """英文术语注解退回旧写法（不越过词尾）：J-33 必须当场红。

    ★ 这是真回归，不是造的样本。2026-10-29 线上实测 /en/faq/ 渲染成
      「six verdict(the one conclusion a tool gets after a check)s」——
      词被括号劈成两半，读者看到的是一个不存在的词。
      把改动退回去（`lang="en"` → `lang="zh"`），缺陷必须重现。
      只塞一个假字符串测不到这条：缺陷在渲染层，不在正文里。
    """
    patch("gen.py",
          'MD.explain_first(body, H.TERMS_EN, paren="()", lang="en")',
          'MD.explain_first(body, H.TERMS_EN, paren="()", lang="zh")')


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
    ("N-10", "J-11", "规则页少一个要素（类别改名），中英两边各注入一处", n10),
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
    ("N-29", "J-16", "英文镜像少一页（中文页没有对应）", n29),
    ("N-30", "J-16", "英文镜像写错规则数（跨语言不一致）", n30),
    ("N-31", "J-14a", "分享预览图被挪走（og:image 失去目标）", n31),
    ("N-32", "J-17", "正文写死当前族的旧版本号（0.60.1）", n32),
    ("N-33", "J-17", "代码示例里写死旧版本号（0.60.1）", n33),
    ("N-34", "J-17", "英文正文句末写死旧版本号（0.60.1.）", n34),
    ("N-35", "J-01", "真源快照的规则被清空（计数自检要红）", n35),
    ("N-36", "J-31", "中文正文写一句 80 字的长句", n36),
    ("N-37", "J-32", "中文正文写一句六十几个字的话（只该红存量那条）", n37),
    ("N-38", "J-33", "英文术语注解退回旧写法（括号把词切开）", n38),
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
