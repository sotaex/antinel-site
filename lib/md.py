# -*- coding: utf-8 -*-
"""受限 Markdown 渲染（标准库，无第三方）。

支持：# ~ ####、段落、有序/无序列表、围栏代码块、管道表、引用块、分隔线、
**粗体**、`行内码`、[链接](url)、以及原样透传的 HTML 块（用于提示框）。
标题可写 `## 标题 {#自定义锚点}`；不写则按 ASCII 规则生成，生成不出就用 h-N。
"""
import html
import re

RE_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
RE_HEAD = re.compile(r"^(#{1,4})\s+(.*)$")
RE_UL = re.compile(r"^(\s*)[-*]\s+(.*)$")
RE_OL = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
RE_HR = re.compile(r"^\s*(---|\*\*\*|___)\s*$")
RE_TBL_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
RE_ANCHOR = re.compile(r"\s*\{#([A-Za-z0-9_\-]+)\}\s*$")


def parse_front(text):
    """返回 (meta dict, body)。meta 支持 key: value 与 key: [a, b]。"""
    m = RE_FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            items = [x.strip().strip("'\"") for x in v[1:-1].split(",")]
            meta[k] = [x for x in items if x]
        else:
            meta[k] = v.strip("'\"")
    return meta, text[m.end():]


def slugify_ascii(s):
    s = re.sub(r"`|\*|\[|\]|\(|\)", "", s)
    s = re.sub(r"[^A-Za-z0-9 \-_.]", "", s).strip()
    s = re.sub(r"[\s_.]+", "-", s).strip("-").lower()
    return s


def _inline(s):
    # 行内码先抽出，避免里面的 * [ ] 被后续规则改写
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    s = re.sub(r"`([^`]+)`", stash, s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), s)

    def unstash(m):
        return "<code>%s</code>" % html.escape(codes[int(m.group(1))], quote=False)

    return re.sub(r"\x00(\d+)\x00", unstash, s)


def _table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if not cells:
        return ""
    w = max(len(r) for r in cells)
    cells = [r + [""] * (w - len(r)) for r in cells]
    out = ['<div class="table-wrap"><table>', "<thead><tr>"]
    out += ["<th>%s</th>" % _inline(c) for c in cells[0]]
    out.append("</tr></thead><tbody>")
    for r in cells[1:]:
        out.append("<tr>" + "".join("<td>%s</td>" % _inline(c) for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render(text, start_level=2):
    """Markdown → HTML 片段。start_level 控制最小标题级别（页面正文从 h2 起）。"""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out, i, seen = [], 0, {}

    def anchor(title):
        m = RE_ANCHOR.search(title)
        if m:
            return title[:m.start()].strip(), m.group(1)
        t = title.strip()
        a = slugify_ascii(t)
        if not a:
            a = "s%d" % (len(seen) + 1)
        seen[a] = seen.get(a, 0) + 1
        if seen[a] > 1:
            a = "%s-%d" % (a, seen[a])
        return t, a

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if not s:
            i += 1
            continue

        # 围栏代码块
        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            body = html.escape("\n".join(buf), quote=False)
            out.append('<div class="code-wrap"><button class="copy" type="button" '
                       'aria-label="复制代码">复制</button>'
                       '<pre><code>%s</code></pre></div>' % body)
            continue

        # 原样透传的 HTML 块（自己写的提示框，内容受控）
        if s.startswith("<") and re.match(r"^</?[a-zA-Z]", s):
            buf = []
            while i < len(lines) and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        m = RE_HEAD.match(s)
        if m:
            lvl = max(start_level, min(4, len(m.group(1)) + start_level - 1))
            title, aid = anchor(m.group(2))
            out.append('<h%d id="%s">%s</h%d>' % (lvl, aid, _inline(title), lvl))
            i += 1
            continue

        if RE_HR.match(s):
            out.append("<hr>")
            i += 1
            continue

        # 表格：当前行含 |，下一行是分隔行
        if "|" in s and i + 1 < len(lines) and RE_TBL_SEP.match(lines[i + 1]):
            buf = [ln]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append(_table(buf))
            continue

        # 引用块
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append('<blockquote><p>%s</p></blockquote>'
                       % "<br>".join(_inline(x) for x in buf))
            continue

        # 列表（同层连续）
        if RE_UL.match(ln) or RE_OL.match(ln):
            ordered = bool(RE_OL.match(ln))
            items, base = [], None
            while i < len(lines):
                mm = RE_OL.match(lines[i]) if ordered else RE_UL.match(lines[i])
                if not mm:
                    break
                indent = len(mm.group(1))
                if base is None:
                    base = indent
                if indent != base:
                    break
                items.append(mm.group(3) if ordered else mm.group(2))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % _inline(x)
                                                      for x in items), tag))
            continue

        # 段落：连续非空行合并
        buf = []
        while i < len(lines) and lines[i].strip() and not (
                RE_HEAD.match(lines[i].strip()) or lines[i].strip().startswith("```")
                or lines[i].strip().startswith(">") or RE_UL.match(lines[i])
                or RE_OL.match(lines[i]) or RE_HR.match(lines[i].strip())):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>%s</p>" % _inline(" ".join(buf)))
        else:
            i += 1

    return "\n".join(out)


def _dep(ln, i, op, cl):
    """到位置 i 为止，左括号比右括号多几个（＞0 就是在括号里）。"""
    return ln.count(op, 0, i) - ln.count(cl, 0, i)


def explain_first(text, terms, paren="（）", lang="zh"):
    """给术语的首次出现补一句人话解释。每个术语每页只解释一次。

    只动正文段落：标题、代码块、表格、引用块一律不碰——那里插解释会毁版式。
    解释文本本身不许含别的术语（lib/human.py 的 TERMS 已保证），
    所以按长度降序替换不会自我污染。

    paren：括号样式。中文页用全角（），英文镜像页用半角 ()——
    英文正文里塞全角括号，一眼就看出是机器拼的。

    为什么放在渲染层做，而不是手改 18 个文件：手改会漏，漏了不报错。
    """
    if not terms:
        return text
    order = sorted(terms, key=len, reverse=True)
    seen = set()
    out = []
    in_code = False
    for ln in text.split("\n"):
        st = ln.strip()
        if st.startswith("```"):
            in_code = not in_code
            out.append(ln)
            continue
        if in_code or not st or st[0] in "#|>":
            out.append(ln)
            continue
        for t in order:
            if t in seen:
                continue
            i = ln.find(t)
            # 跳过已在括号里的出现：那里插解释会变成「（…（…）…）」双重括号。
            # ★ 两种括号都要数。原来只数全角括号，英文页的 `(…)` 认不出来，
            #   于是同一个词会被套第二层括号。
            while i >= 0 and (_dep(ln, i, "（", "）") > 0
                              or _dep(ln, i, "(", ")") > 0):
                i = ln.find(t, i + len(t))
            if i < 0:
                continue
            j = i + len(t)
            while j < len(ln) and ln[j] in "*_":   # 别把解释裹进加粗
                j += 1
            # ★ 英文词要越过词尾再插括号。不越过去，括号会把词切开：
            #   `verdict` ＋ `(…检查得出的那个结论…)` ＋ `s`，
            #   线上渲染成 "verdict(the one conclusion…)s"（2026-10-29 实测 /en/faq/）。
            #   中文没有词尾变化，不受影响。
            if lang == "en":
                while j < len(ln) and (ln[j].islower() or ln[j] in "'’"):
                    j += 1
                # 英文括号前要留一个空格：`hosts(an AI tool…)` 是中文写法。
                # 中文页不加，中文本来就不留。
                if j > 0 and ln[j - 1] not in " \t":
                    ln = ln[:j] + " " + ln[j:]
                    j += 1
            ln = ln[:j] + "%s%s%s" % (paren[0], terms[t], paren[1]) + ln[j:]
            seen.add(t)
        out.append(ln)
    return "\n".join(out)


def first_heading(text):
    for ln in text.splitlines():
        m = RE_HEAD.match(ln.strip())
        if m and len(m.group(1)) == 1:
            t, _ = RE_ANCHOR.sub("", m.group(2)).strip(), None
            return RE_ANCHOR.sub("", m.group(2)).strip()
    return ""


def plain(s):
    """去掉行内标记，用于判据比对。"""
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()
