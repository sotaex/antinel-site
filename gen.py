# -*- coding: utf-8 -*-
"""Antinel 监理官网 —— 唯一构建入口。

    python gen.py                  # 构建到 site-output/
    python gen.py --check          # 只校验，不写盘（CI 与本地验收用）
    python gen.py --refresh-sources# 从产品仓重取真源快照（仅开发机）

判据见 site-spec/05 与 07；红即构建失败（退出码非 0）。
"""
import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib import config as C          # noqa: E402
from lib import md as MD             # noqa: E402
from lib import render as R          # noqa: E402
from lib import sources as S         # noqa: E402
from lib import checks as K          # noqa: E402
from lib import human as H           # noqa: E402

CAT_ZH = {
    "secrets": "机密与隐私",
    "destructive": "破坏性操作",
    "network": "对外联网",
    "injection": "注入与伪装",
    "context": "环境信息探测",
    "metadata": "技能元数据",
    "supply_chain": "供应链与插件",
    "canary": "诱饵文件布防",
}

SEV_ZH = {"critical": "严重（当场拦截）", "warning": "警告（提醒放行）"}

# 英文镜像用的标签。规则页的 description / remediation / name 真源自带英文，
# 这里只补「标签」和「类别名」——不翻译正文，不引入第二份事实。
CAT_EN = {
    "secrets": "Secrets and privacy",
    "destructive": "Destructive operations",
    "network": "Outbound network",
    "injection": "Injection and disguise",
    "context": "Environment probing",
    "metadata": "Skill metadata",
    "supply_chain": "Supply chain and plugins",
    "canary": "Canary files",
}
SEV_EN = {"critical": "critical (blocked on hit)", "warning": "warning (allowed, logged)"}

HAND = [
    ("help", "从哪开始", "按你现在的处境分流：第一次装、出了状况、要核对数字，各去哪一页。"),
    ("steward", "为什么叫监理", "监理＝按事先写好的标准把关、记录、必要时叫停的独立第三方（GB/T 19668 谱系）。"),
    ("gates", "四道门", "内容安全／敏感面／元数据与出联／行为，四道门各挡什么、挡不住什么。"),
    ("monitor", "数据外传监控六机制", "自认记录／出口记录／宿主拦截／诱饵文件／安全区／报告呈现，六种机制各管一段。"),
    ("checkup", "安全体检", "只读、本地、四组输出；一次点开就知道这台机器有没有被带走东西。"),
    ("threat-model", "威胁模型与边界", "护栏不是隔离层：我们拦什么、不拦什么、为什么。"),
    ("completeness", "40 格完备矩阵", "8 类载体 × 五个动作（看／判／报／挡／记），四十个格子，哪一格还没查。"),
    ("audit", "审计链与复算", "只加不删、改一个字节就能算出来；第三方复算可以取代随包结论。"),
    ("compare", "和谁不一样", "和杀毒、沙箱、DLP、SIEM、等保的区别，一张表说清。"),
    ("license", "许可与中立", "代码 Apache-2.0／内容 CC-BY-SA-4.0／数据 CC-BY-4.0；不收通过费、不出售排名。"),
    ("brand", "品牌与用词", "Antinel 监理／Antinel Steward／包名 antinel，以及不要用的词。"),
    ("faq", "常见问题", "12 个问题，每答可独立引用。"),
    ("changelog", "变更日志", "每个版本的事实变化点。"),
]

# 英文镜像的手写页清单。slug 与中文一一对应（J-16），正文在 content/en/<slug>.md。
# 标题与描述只做 <title> 与 meta description 用；页面里的 H1 以 md 正文为准。
HAND_EN = [
    ("help", "Where to start",
     "Pick the page that fits where you are: first install, something is off, or you want to check a number."),
    ("steward", "Why we call it a steward",
     "A steward checks against written rules, records what it sees, and can stop an action."),
    ("gates", "The four gates",
     "Content safety, sensitive surface, metadata and outbound, behaviour — what each gate stops and what it cannot."),
    ("monitor", "Six ways we watch outbound data",
     "Self-reported records, the egress ledger, host gates, canary files, safe zones, and the report."),
    ("checkup", "The checkup",
     "Read-only, local, four groups of output. One click tells you if this machine leaked anything."),
    ("threat-model", "Threat model and limits",
     "A guard rail is not an isolation layer: what we stop, what we do not, and why."),
    ("completeness", "The 40-cell matrix",
     "8 carrier types × 5 actions. Forty cells, and which ones nobody has checked yet."),
    ("audit", "Audit chain and re-runs",
     "Append-only; change one byte and it shows. A third-party re-run can replace our verdict."),
    ("compare", "How it differs",
     "Against antivirus, sandboxes, DLP, SIEM, and compliance audits — one table."),
    ("license", "License and neutrality",
     "Code Apache-2.0, text CC-BY-SA-4.0, data CC-BY-4.0. No passage fee, no paid ranking."),
    ("brand", "Brand and wording",
     "Antinel Steward, package name antinel, and the words we do not use."),
    ("faq", "Questions", "12 questions. Each answer stands on its own."),
    ("changelog", "Changelog", "What changed in each version, as facts."),
]

DOCS = [
    ("install", "安装", "三步装好：装包、装钩子、重启宿主。"),
    ("quickstart", "五分钟上手", "装 → 查 → 守，全程可复制。"),
    ("commands", "命令总表", "审核／防范／账本三类命令，按意图查。"),
    ("policy", "策略与白名单", "四把钥匙；严重级永不放宽。"),
    ("agent", "给 Agent 的机读卡", "字段表、退出码、钩子契约、话术表。本页读者是 Agent。"),
    ("upgrade", "升级与卸载", "升级三步；怎么识别降级。"),
    ("troubleshooting", "故障与边界", "钩子不生效怎么办，常见信号速查。"),
]


class BuildError(RuntimeError):
    pass


# ---------------------------------------------------------------- 事实

def build_facts(truth):
    rules = truth["rules"]
    cats = {}
    for r in rules:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    crit = sum(1 for r in rules if r["severity"] == "critical")
    warn = sum(1 for r in rules if r["severity"] == "warning")
    gate_nums = sorted({n for v in truth["gates"].values()
                        for n in re.findall(r"\d+", "".join(
                            re.findall(r"Gate\s*\d+(?:\s*/\s*\d+)*", v)))})
    sp = truth["selfproof"]
    vk = list(truth["verdicts"].keys())

    # ★ F-004 / F-005 / F-006 以前是写死在这里的三个字面量，evidence 指向 README
    #   或 THREAT_MODEL.md。那是「文档这么说」，不是「我们量过」——两者在页面上
    #   长得一模一样，读者分不出来。现在三条都从快照的 measured 块取，取不到就
    #   报错：宁可构建失败，也不许把上一版的值当作这一版的实测。
    me = truth.get("measured") or {}
    std = me.get("stdlib") or {}
    sco = me.get("scoring") or {}
    for k, v in (("stdlib", std), ("scoring", sco)):
        if not v:
            raise BuildError("真源快照缺实测块 measured.%s —— 跑 "
                             "python gen.py --refresh-sources 重取" % k)
    ext = std.get("externals") or []
    f5_stmt = ("运行时零网络、纯标准库、默认安装不起常驻进程"
               if std.get("stdlib_only") == "是"
               else "默认安装不起常驻进程；运行时有外部依赖：%s" % "、".join(ext))

    claims = [
        {"id": "F-001",
         "statement": "%d 条护盾规则，分 %d 类，按 %d 道审查门组织" % (len(rules), len(cats), len(gate_nums)),
         "value": {"rules": len(rules), "categories": len(cats), "gates": len(gate_nums)},
         "evidence": "rules/default.json@%s" % truth["product_version"]},
        {"id": "F-002",
         "statement": "严重 %d 条当场拦截，警告 %d 条提醒放行" % (crit, warn),
         "value": {"critical": crit, "warning": warn},
         "evidence": "rules/default.json@%s" % truth["product_version"]},
        {"id": "F-003",
         "statement": "登记 %d 类 AI 工具宿主" % len(truth["hosts"]),
         "value": {"hosts": len(truth["hosts"])},
         "evidence": "rules/hosts/*.json@%s" % truth["product_version"]},
        {"id": "F-004",
         "statement": "产品方声明单次钩子调用时延约 65 毫秒（Windows）",
         "value": {"p50_ms": 65, "platform": "win32"},
         "evidence": "声明，未在本站复测：references/THREAT_MODEL.md。本站试过在"
                     "临时目录里端到端计时，量到 3 秒上下——那是非 git 目录触发的"
                     "超时路径，形状与用户机器不同，不作数，所以不写进这一页"},
        {"id": "F-005",
         "statement": f5_stmt,
         "value": {"network": "否", "stdlib_only": std.get("stdlib_only"),
                   "daemon": "默认无"},
         "evidence": "标准库面为实测：ast 扫描 %d 个运行时文件，比对标准库清单，"
                     "外部依赖 %d 个。常驻与联网为声明，来源是安装代码路径与"
                     "威胁模型页——那两项没有在本机做联网观测"
                     % (std.get("files_scanned", 0), len(ext))},
        {"id": "F-006",
         "statement": "计分公式 score = 100 − %d×严重 − %d×警告（按「规则×对象」去重）"
                      % (sco["critical_weight"], sco["warning_weight"]),
         "value": {"formula": "100-%dC-%dW" % (sco["critical_weight"],
                                               sco["warning_weight"]),
                   "_cw": sco["critical_weight"], "_ww": sco["warning_weight"]},
         "evidence": "实测：%s，位置 %s 第 %d 行（不是抄文档）"
                     % (sco["method"], sco["source"], sco["line"])},
        {"id": "F-007",
         "statement": "随包自证：%s 项断言全过，%s 个摘要一致" % (sp.get("assertions_total") or "?", sp.get("digests_total") or "?"),
         "value": {"assertions": sp.get("assertions_total"), "digests": sp.get("digests_total")},
         "evidence": "SKILL.md#psl-verified-evidence"},
        {"id": "F-008",
         "statement": "六档证据裁决 %s" % "/".join(vk),
         "value": {"verdicts": vk, "count": len(vk)},
         "evidence": "antinel.VERDICTS"},
        {"id": "F-009",
         "statement": "数据外传监控六机制：自认审计／出口账本／宿主门闸／金丝雀／安全区／报告呈现",
         "value": {"mechanisms": 6},
         "evidence": "使用手册 §5.1"},
        {"id": "F-010",
         "statement": "审计链只增不删；第三方复跑出不同结论即取代随包判定",
         "value": {"append_only": "是", "third_party_override": "是"},
         "evidence": "README.md#信任"},
        {"id": "F-011",
         "statement": "策略白名单不得放宽严重级拦截；审计写失败默认放行且可见",
         "value": {"critical_never_relaxed": "是", "fail_open_visible": "是"},
         "evidence": "references/THREAT_MODEL.md"},
        {"id": "F-012",
         "statement": "公开可复算：复跑全部断言、独立校验审计链",
         "value": {"public_chain": "github.com/sotaex/agentstate"},
         "evidence": "README.md#信任"},
    ]
    return claims


def subst(text, facts, truth):
    """把 {{facts.X.value.k}} / {{product_version}} 等换成真值。未知占位符 → 构建失败。"""
    idx = {c["id"]: c for c in facts}
    data_date = truth["captured_at"][:10]

    def rep(m):
        expr = m.group(1).strip()
        if expr == "product_version":
            return truth["product_version"]
        if expr == "data_date":
            return data_date
        if expr == "fingerprint":
            return C.FINGERPRINT
        if expr == "site_url":
            return C.SITE_URL + C.BASE_PATH
        mm = re.match(r"^facts\.(F-\d+)\.(statement|evidence)$", expr)
        if mm:
            c = idx.get(mm.group(1))
            if not c:
                raise BuildError("占位符指向不存在的事实：%s" % expr)
            return str(c[mm.group(2)])
        mm = re.match(r"^facts\.(F-\d+)\.value\.([A-Za-z0-9_]+)$", expr)
        if mm:
            c = idx.get(mm.group(1))
            if not c or mm.group(2) not in c["value"]:
                raise BuildError("占位符指向不存在的值：%s" % expr)
            return str(c["value"][mm.group(2)])
        raise BuildError("未知占位符：{{%s}}" % expr)

    return re.sub(r"\{\{([^}]+)\}\}", rep, text)


# ---------------------------------------------------------------- 页面

def gate_of(truth, cat):
    """门号集合，只从真源的 gates 字段解析，不另写映射表（J-19）。"""
    v = truth["gates"].get(cat, "")
    segs = re.findall(r"Gate\s*\d+(?:\s*/\s*\d+)*", v)
    return sorted({int(n) for s in segs for n in re.findall(r"\d+", s)})


def shown_values(c):
    """事实的可见值。下划线开头的键只给格式串与数据集用，不上面。

    否则 facts 页会把「65／win32／15」三格并排，读者不知道 15 是次数还是毫秒。
    机读层（/datasets/）仍然拿完整 dict —— 那里要的就是原始字段。
    """
    return [v for k, v in c["value"].items() if not k.startswith("_")]


def page_facts(facts, truth):
    data_date = truth["captured_at"][:10]
    rows = []
    for c in facts:
        vals = "／".join("<strong>%s</strong>" % R.esc(str(v)) if not isinstance(v, list)
                        else "／".join("<strong>%s</strong>" % R.esc(str(x)) for x in v)
                        for v in shown_values(c))
        rows.append('<h2 id="%s">%s　%s</h2>\n<p>值：%s。证据：<code>%s</code>。</p>'
                    % (c["id"].lower(), c["id"], R.esc(c["statement"]), vals,
                       R.esc(c["evidence"])))
    body = ('<h1>事实总览</h1>\n<p class="lead">一句话：本页是 Antinel 监理全部核心事实的唯一权威清单。'
            '每条一个锚点，逐条给出复算来源。</p>\n'
            '<p class="meta">产品版本 %s · 数据日期 %s · 引用请以本页为准</p>\n'
            '%s\n<p class="footnote">引用格式与许可见页脚。数值若与 <code>/datasets/</code> 下的'
            '机器可读文件不一致，以数据集为准。</p>' % (truth["product_version"], data_date,
                                                      "\n".join(rows)))
    md = ["# 事实总览", "",
          "一句话：本页是 Antinel 监理全部核心事实的唯一权威清单。每条一个锚点，逐条给出复算来源。",
          "", "产品版本 %s · 数据日期 %s" % (truth["product_version"], data_date), ""]
    for c in facts:
        vals = "／".join(str(v) if not isinstance(v, list) else "/".join(map(str, v))
                        for v in shown_values(c))
        md += ["## %s　%s" % (c["id"], c["statement"]), "",
               "值：%s。证据：`%s`。" % (vals, c["evidence"]), ""]
    return body, "\n".join(md)


def page_verdicts(truth):
    """六种结论。人话名从 lib/human.py 取；英文代号降为副标，给工程师对接日志用。"""
    v = truth["verdicts"]
    order = sorted(v.values(), key=lambda x: x.get("order", 99))
    rows = "".join(
        '<tr><td><span class="vicon">%s</span> <strong>%s</strong><br>'
        '<code class="sub">%s</code></td><td>%s</td><td>%s</td></tr>'
        % (R.esc(x.get("icon", "")), R.esc(H.v(x["key"], "name")), R.esc(x["key"]),
           R.esc(H.v(x["key"], "short")), R.esc(H.v(x["key"], "todo"))) for x in order)
    ev = truth["evidence_meaning"]
    evrows = "".join('<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>'
                     % (R.esc(k), R.esc(val[0]), R.esc(val[1])) for k, val in ev.items())
    body = (
        '<h1>六种结论</h1>\n'
        '<p class="lead">检查完，每个 AI 工具拿一个结论。同一个工具命中多条时，'
        '取最重的那条。</p>\n'
        '<div class="callout"><p>%s</p></div>\n'
        '<h2 id="table">六种结论</h2>\n'
        '<div class="table-wrap"><table><thead><tr><th>结论</th><th>这意味着什么</th>'
        '<th>你该做什么</th></tr></thead><tbody>%s</tbody></table></div>\n'
        '<h2 id="priority">多条命中时取哪一条</h2>\n'
        '<p>按这个顺序取最重的一条：'
        '<code>PACK</code> &gt; <code>SENT</code> &gt; <code>SYNC</code> &gt; '
        '<code>CLEAN</code>。'
        '<code>BLIND</code> 和 <code>NA</code> 不参加比较——它们不是「轻」，是「另一回事」。</p>\n'
        '<h2 id="keys">工具记下的字段，分别算什么（%d 个）</h2>\n'
        '<p>这一节给要对接日志的人。看不懂可以跳过，不影响上面的结论。</p>\n'
        '<div class="table-wrap"><table><thead><tr><th>字段名</th><th>算哪一档</th>'
        '<th>人话</th></tr></thead><tbody>%s</tbody></table></div>\n'
        '<h2 id="edge">两句话不能省</h2>\n'
        '<ul>'
        '<li>「查过了，没找到记录」不是「没有外传」。它只说明这次扫到的地方没有证据。</li>'
        '<li>「没查到」不是清白。那是这一项没查成，监理没看见，不是它没问题。</li>'
        '</ul>\n'
        % (H.VERDICT_WHY, rows, len(ev), evrows))
    md = ["# 六种结论", "",
          "检查完，每个 AI 工具拿一个结论。同一个工具命中多条时，取最重的那条。", "",
          "> " + H.VERDICT_WHY, "",
          "## 六种结论", "", "| 结论 | 代号 | 这意味着什么 | 你该做什么 |", "|---|---|---|---|"]
    for x in order:
        md.append("| %s %s | `%s` | %s | %s |"
                  % (x.get("icon", ""), H.v(x["key"], "name"), x["key"],
                     H.v(x["key"], "short"), H.v(x["key"], "todo")))
    md += ["", "## 工具记下的字段，分别算什么", "",
           "| 字段名 | 算哪一档 | 人话 |", "|---|---|---|"]
    for k, val in ev.items():
        md.append("| `%s` | %s | %s |" % (k, val[0], val[1]))
    return body, "\n".join(md)


def page_why(truth, facts):
    """给不看技术的人：一页纸，可打印（CSS 已有 @media print）。四问四答，无术语。"""
    f = {c["id"]: c for c in facts}
    v = f["F-001"]["value"]
    body = (
        '<h1>给不看技术的人</h1>\n'
        '<p class="lead">这一页只用大白话，四分钟读完。看完你会知道三件事：'
        '这事跟你有没有关系、它能给你什么、你要做什么。</p>\n'

        '<h2 id="q1">一、这事跟你有没有关系</h2>\n'
        '<p>你的团队在用 AI 写代码、写文案、做表。这些工具要在你电脑上读文件、跑命令，'
        '才能把活干完。</p>\n'
        '<p>它们读得对不对，现在没人说得清。你的电脑上没有一本账。</p>\n'
        '<p>于是有一种场面：客户或领导问一句「我们的资料会不会外流」，'
        '你答不上来。不是因为你没管，是因为你手上没有记录。</p>\n'
        '<p>这一页讲的工具，就是给你补上这本账。</p>\n'

        '<h2 id="q2">二、它到底做什么</h2>\n'
        '<p>它做三件事，都很朴素。</p>\n'
        '<dl class="qa">'
        '<dt>记</dt>'
        '<dd>每次 AI 工具要读文件、删文件、连网络，它记一条。记在你自己电脑上。</dd>'
        '<dt>拦</dt>'
        '<dd>碰到最危险的那几类动作（比如读你的密钥文件、删你的项目），它当场拦下，不让做。</dd>'
        '<dt>出纸</dt>'
        '<dd>你要交差的时候，它出一页纸：这台电脑上每个工具，有没有自己记下「上传过」。</dd>'
        '</dl>\n'
        '<p>它不改你的文件，不改你的代码，不碰你的业务。'
        '它只在你电脑上跑，自己不上网，结果不出这台电脑。</p>\n'

        '<h2 id="q3">三、凭什么信</h2>\n'
        '<p>不要信我们的说法。信这三件你能自己做的事。</p>\n'
        '<ul>'
        '<li><strong>账本改不了。</strong>每条记录带一个指纹，改一个字节就能算出来。'
        '一条命令查：<code>antinel verify</code>。</li>'
        '<li><strong>结论可以被推翻。</strong>你自己跑一遍，得出不同的结论，'
        '系统认你的，不认我们的。原记录不删不改。</li>'
        '<li><strong>标准是公开的。</strong>%s 条检查规则写在公开文件里。'
        '觉得哪条太松或太紧，改完自己算。</li>'
        '</ul>\n'
        '<p>还有一条更像实话的：我们不卖「认证」，不收「通过费」，'
        '也不接「帮我过检」的活。判断和收费分开，结论才站得住。</p>\n'

        '<h2 id="q4">四、它做不到什么</h2>\n'
        '<p>这一段放在这里，不放在页脚。</p>\n'
        '<ul>'
        '<li>有人把危险操作写进脚本再执行，它拦不住。会有记录，但不会阻止。</li>'
        '<li>它不做隔离。要物理隔离，用容器或虚拟机。</li>'
        '<li>它只认识登记过的 %s 类 AI 工具。没登记的工具，它拿不到记录。</li>'
        '<li>它出的不是检验检测报告，没有法律效力。要那种报告，找有资质的机构。</li>'
        '</ul>\n'

        '<h2 id="q5">五、你要做什么</h2>\n'
        '<p>两步。先查一次，再看结果。</p>\n'
        '<ol>'
        '<li><strong>查一次。</strong>在电脑上跑 <code>antinel ui</code>，'
        '浏览器点一下。一到两分钟出结果。只读，不改任何东西。</li>'
        '<li><strong>看结果。</strong>如果出现「它自己记着：发出去过」，'
        '就值得往下查。如果全是「查过了，没找到记录」，你至少有了一个能说的答案。</li>'
        '</ol>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">两分钟查一次</a>'
        '<a class="btn" href="%s/sample/">先看一页样例</a></p>\n'

        '<h2 id="q6">六、谁不需要它</h2>\n'
        '<p>三种人可以先不用。第一种，只用 AI 聊天、不在电脑上跑 AI 工具的人。'
        '第二种，已经把 AI 工具关在容器里、并且有网络出口管控的人。'
        '第三种，需要法律效力报告、不需要工程记录的人。</p>\n'
        % (v["rules"], f["F-003"]["value"]["hosts"], C.BASE_PATH, C.BASE_PATH))

    md = ["# 给不看技术的人", "",
          "这一页只用大白话，四分钟读完。", "",
          "## 一、这事跟你有没有关系", "",
          "你的团队在用 AI 写代码、写文案、做表。这些工具要在你电脑上读文件、跑命令，才能把活干完。",
          "", "它们读得对不对，现在没人说得清。你的电脑上没有一本账。", "",
          "客户或领导问一句「我们的资料会不会外流」，你答不上来。"
          "不是因为你没管，是因为你手上没有记录。", "",
          "## 二、它到底做什么", "",
          "- **记**：每次读文件、删文件、连网络，记一条，记在你自己电脑上。",
          "- **拦**：最危险的那几类动作当场拦下，不让做。",
          "- **出纸**：要交差的时候，出一页纸。", "",
          "## 三、凭什么信", "",
          "- 账本改不了：每条记录带指纹，`antinel verify` 一条命令查。",
          "- 结论可以被推翻：你自己跑一遍，系统认你的结论。",
          "- 标准公开：%d 条规则写在公开文件里。" % v["rules"], "",
          "## 四、它做不到什么", "",
          "- 写进脚本再执行，拦不住（有记录）。",
          "- 不做隔离，要隔离用容器。",
          "- 只认识登记过的 %d 类 AI 工具。" % f["F-003"]["value"]["hosts"],
          "- 不是检验检测报告，没有法律效力。", "",
          "## 五、你要做什么", "",
          "1. 跑 `antinel ui`，浏览器点一下，一到两分钟。",
          "2. 看结果。出现「发出去过」就往下查；全是「没找到记录」，你也有了能说的答案。", "",
          "## 六、谁不需要它", "",
          "只用 AI 聊天、不在电脑上跑工具的人；已经把工具关在容器里并有出口管控的人；"
          "需要法律效力报告的人。", ""]
    return body, "\n".join(md)


def page_sample(truth, facts):
    """一页纸样例。必须处处标明是样例，不能让人误当成自己机器的结果。"""
    f = {c["id"]: c for c in facts}
    banner = ('<div class="callout warn"><p><strong>样例数据。</strong>'
              '这一页用来说明输出长什么样，不是你电脑的检查结果。'
              '你机器上的那一页，跑一次 <code>antinel brief</code> 就有。</p></div>\n')
    body = (
        '<h1>一页纸长什么样</h1>\n'
        '<p class="lead">这是你要交差的那张纸。三段：一句话结论、逐工具清单、下一步。'
        '下面用的是样例数据。</p>\n'
        + banner +
        '<div class="sheet">\n'
        '<p class="sheet-head">样例 · 非真实数据</p>\n'
        '<h2 class="sheet-title">本机 AI 工具外传检查 · 一页纸</h2>\n'
        '<p class="sheet-meta">机器：工作站一台 ｜ 检查时间：样例 ｜ '
        '产品版本 %s ｜ 数据日期 %s</p>\n'
        '<p class="sheet-verdict">一句话结论：<strong>有 1 个工具自己记着「发出去过」，'
        '2 个只查到「在同步」，1 个查过没发现记录，2 个没查到。</strong></p>\n'
        '<div class="table-wrap"><table><thead><tr>'
        '<th>AI 工具</th><th>结论</th><th>它自己写下的</th><th>建议</th>'
        '</tr></thead><tbody>'
        '<tr><td>工具甲</td><td>🟠 它自己记着：发出去过</td>'
        '<td>「上次上传：2026-09-30」</td><td>问工具方传了什么；先停用它</td></tr>'
        '<tr><td>工具乙</td><td>🟡 它自己记着：在同步</td>'
        '<td>「上次同步：2026-10-21」</td><td>看同步目录里有没有客户资料</td></tr>'
        '<tr><td>工具丙</td><td>🟡 它自己记着：在同步</td>'
        '<td>「上次同步：2026-10-22」</td><td>同上</td></tr>'
        '<tr><td>工具丁</td><td>⚪ 查过了，没找到记录</td>'
        '<td>—</td><td>换一个时间范围再查</td></tr>'
        '<tr><td>工具戊</td><td>⚫ 没查到（这一项没查成）</td>'
        '<td>—</td><td>手动打开它的配置目录看一眼</td></tr>'
        '<tr><td>工具己</td><td>⚫ 没查到（这一项没查成）</td><td>—</td><td>同上</td></tr>'
        '</tbody></table></div>\n'
        '<p class="sheet-note">读法：「它自己记着」＝工具自己写下的记录，不是我们亲眼看见的动作。'
        '「没查到」＝这一项没查成，不等于清白。</p>\n'
        '<p class="sheet-next"><strong>下一步：</strong>'
        '① 先处理「发出去过」那一个。② 对两个「没查到」补一次人工确认。'
        '③ 把这一页存档，作为本次检查的记录。</p>\n'
        '</div>\n'
        '<h2 id="how">怎么得到你自己这一页</h2>\n'
        '<p>一条命令。只读，不上传，结果留在本机。</p>\n'
        '<div class="code-wrap"><pre><code>antinel brief</code></pre></div>\n'
        '<p>要更细的逐条记录，用 <code>antinel host-scan</code>。'
        '要在浏览器里点，用 <code>antinel ui</code>。</p>\n'
        '<h2 id="edge">这一页不能当什么用</h2>\n'
        '<p>它是工程记录，不是检验检测报告，没有法律效力。'
        '它证明的是「这台电脑上有哪些记录」，不证明「你的资料一定没出去」。</p>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">'
        '两分钟查一次</a></p>\n'
        % (truth["product_version"], truth["captured_at"][:10], C.BASE_PATH))

    md = ["# 一页纸长什么样", "",
          "> 样例数据。这一页用来说明输出长什么样，不是你电脑的检查结果。", "",
          "## 样例：本机 AI 工具外传检查 · 一页纸", "",
          "一句话结论：有 1 个工具自己记着「发出去过」，2 个只查到「在同步」，1 个查过没发现记录，2 个没查到。", "",
          "| AI 工具 | 结论 | 它自己写下的 | 建议 |",
          "|---|---|---|---|",
          "| 工具甲 | 🟠 它自己记着：发出去过 | 「上次上传：2026-09-30」 | 问工具方传了什么；先停用它 |",
          "| 工具乙 | 🟡 它自己记着：在同步 | 「上次同步：2026-10-21」 | 看同步目录里有没有客户资料 |",
          "| 工具丙 | 🟡 它自己记着：在同步 | 「上次同步：2026-10-22」 | 同上 |",
          "| 工具丁 | ⚪ 查过了，没找到记录 | — | 换一个时间范围再查 |",
          "| 工具戊 | ⚫ 没查到（这一项没查成） | — | 手动打开它的配置目录看一眼 |",
          "| 工具己 | ⚫ 没查到（这一项没查成） | — | 同上 |", "",
          "## 怎么得到你自己这一页", "",
          "```", "antinel brief", "```", "",
          "## 这一页不能当什么用", "",
          "它是工程记录，不是检验检测报告，没有法律效力。", ""]
    return body, "\n".join(md)


def page_docs_index(truth, facts):
    """文档目录。按「你现在的处境」分三条路，不按文件字母序。"""
    starts = [
        ("第一次装，只想让它跑起来", "install",
         "三条命令。装完就有一条记录在写。"),
        ("装好了，想知道它到底拦什么", "quickstart",
         "装 → 查 → 守，五分钟走一遍。"),
        ("要交给别人评审，需要字段和退出码", "agent",
         "字段表、退出码、钩子契约。这页读者是程序，人也能看。"),
    ]
    rest = [d for d in DOCS if d[0] not in ("install", "quickstart", "agent")]

    def card(slug, title, desc, label=None):
        tag = '<span class="sub">%s</span>' % R.esc(label) if label else ""
        return ('<a class="card" href="%s/docs/%s/"><h2>%s%s</h2><p>%s</p></a>'
                % (C.BASE_PATH, slug, R.esc(title), tag, R.esc(desc)))

    body = (
        '<h1>文档</h1>\n'
        '<p class="lead">七页。不用全看。先按你现在的处境挑一条路，'
        '剩下的当字典查。</p>\n'
        '<h2 id="start">先看哪一页</h2>\n'
        '<div class="cards">\n'
        + "".join(card(s, t, d) for t, s, d in starts) +
        '</div>\n'
        '<h2 id="all">其余四页</h2>\n'
        '<div class="cards">\n'
        + "".join(card(s, t, d) for s, t, d in rest) +
        '</div>\n'
        '<h2 id="machine">给程序和 Agent 看的</h2>\n'
        '<p>整站的机读入口在 <a href="%s/llms.txt"><code>/llms.txt</code></a>：'
        '一段摘要、八个分组、每条链接都指向纯文本。'
        '要一次拿全，用 <a href="%s/llms-full.txt"><code>/llms-full.txt</code></a>。'
        '要结构化数据，用 <a href="%s/datasets/">数据集</a>（JSON，带 sha256）。</p>\n'
        '<p>每一页都有一个 <code>.md</code> 镜像，把地址末尾的 <code>/</code> '
        '换成 <code>.md</code> 就是纯文本原文。</p>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/install/">从安装开始</a>'
        '<a class="btn" href="%s/docs/commands/">查命令总表</a></p>\n'
        % (C.BASE_PATH, C.BASE_PATH, C.BASE_PATH, C.BASE_PATH, C.BASE_PATH)
    )

    md = ["# 文档", "",
          "七页。不用全看。先按你现在的处境挑一条路，剩下的当字典查。", "",
          "## 先看哪一页", ""]
    for t, s, d in starts:
        md += ["- **[%s](/docs/%s/)**：%s" % (t, s, d)]
    md += ["", "## 其余四页", ""]
    for s, t, d in DOCS:
        md += ["- **[%s](/docs/%s/)**：%s" % (t, s, d)]
    md += ["", "## 给程序和 Agent 看的", "",
           "机读入口 `/llms.txt`；全量 `/llms-full.txt`；结构化数据 `/datasets/`。",
           "每页有 `.md` 镜像：地址末尾 `/` 换成 `.md`。", ""]
    return body, "\n".join(md)


def vis(s):
    """把不可见字符写成可读记号。真源里确有隐形字符（CTX-03 的字符白名单就是 U+200D），
    页面必须把它显示出来，而不是原样带进产物（J-05）。"""
    out = []
    for ch in s:
        o = ord(ch)
        if (0x200B <= o <= 0x200F) or (0x2028 <= o <= 0x202E) or \
           (0x2060 <= o <= 0x2064) or o == 0xFEFF or (0xE000 <= o <= 0xF8FF):
            out.append("[U+%04X]" % o)
        else:
            out.append(ch)
    return "".join(out)


def rule_lead(r):
    act = "当场拦截并记录" if r["severity"] == "critical" else "提醒并放行，同时记录"
    return "一句话：%s。命中时监理%s。" % (r.get("description_zh") or r.get("description", ""), act)


def page_rule(truth, r, prev_id, next_id, lang="zh"):
    r = dict(r)
    for k in ("label_zh", "name", "description_zh", "description",
              "remediation_zh", "remediation", "note"):
        if isinstance(r.get(k), str):
            r[k] = vis(r[k])
    en = (lang == "en")
    gates = gate_of(truth, r["category"])
    gate_txt = "／".join("Gate %d" % g for g in gates)
    if en:
        cat = "%s (%s)" % (CAT_EN.get(r["category"], r["category"]), gate_txt)
        sev = SEV_EN.get(r["severity"], r["severity"])
        pat_labels = (("file_patterns", "File"), ("content_patterns", "Content"),
                      ("command_patterns", "Command"), ("exclude_patterns", "Exclude"),
                      ("whitelist_domains", "Domain allowlist"),
                      ("whitelist_chars", "Character allowlist"), ("ranges", "Ranges"))
        extra_labels = (("check", "Checker"), ("detection", "Detection"))
        L = {"crumb": "Rule index", "cat": "Category", "sev": "Severity",
             "tools": "Applies to", "ver": "Version", "src": "source of truth: rules/default.json",
             "trigger": "When it fires", "remed": "What to do",
             "pat": "Match shapes (regex and fields, for recomputation)",
             "note": "Note from the stewards", "prev": "Previous", "next": "Next",
             "all": "All %d rules", "plat": "Platform", "only": "%s only"}
    else:
        cat = "%s（%s）" % (CAT_ZH.get(r["category"], r["category"]), gate_txt)
        sev = SEV_ZH.get(r["severity"], r["severity"])
        pat_labels = (("file_patterns", "文件"), ("content_patterns", "内容"),
                      ("command_patterns", "命令"), ("exclude_patterns", "排除"),
                      ("whitelist_domains", "域名白名单"), ("whitelist_chars", "字符白名单"),
                      ("ranges", "字符区间"))
        extra_labels = (("check", "检查器"), ("detection", "检测方式"))
        L = {"crumb": "规则目录", "cat": "类别", "sev": "级别",
             "tools": "适用工具", "ver": "版本", "src": "真源 rules/default.json",
             "trigger": "触发情形", "remed": "处置建议",
             "pat": "匹配形态（正则与字段，供复算）",
             "note": "监理说明", "prev": "上一条", "next": "下一条",
             "all": "全部 %d 条规则", "plat": "平台", "only": "仅 %s"}
    tools = r.get("tool_names") or r.get("apply_to_tools") or []
    pats = []
    for k, label in pat_labels:
        if r.get(k):
            pats.append((label, r[k]))
    for k, label in extra_labels:
        if r.get(k):
            pats.append((label, [r[k]]))

    pat_html = ""
    if pats:
        inner = "".join("<p class=\"patlabel\">%s</p><pre class=\"pat\">%s</pre>"
                        % (R.esc(lbl), R.esc(vis("\n".join(
                            json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x)
                            for x in lst)))) for lbl, lst in pats)
        pat_html = ('<details class="patterns"><summary>%s</summary>%s</details>'
                    % (L["pat"], inner))
    plat = ""
    if r.get("platforms"):
        names = "、".join({"nt": "Windows"}.get(p, p) for p in r["platforms"]) if not en \
            else ", ".join({"nt": "Windows"}.get(p, p) for p in r["platforms"])
        plat = "<dt>%s</dt><dd>%s</dd>" % (L["plat"], R.esc(L["only"] % names))
    note = ""
    if r.get("note"):
        note = '<h2 id="note">%s</h2>\n<p>%s</p>' % (L["note"], R.esc(r["note"]))

    nav = '<p class="navline">'
    if prev_id:
        nav += '<a href="../%s/">← %s %s</a> ｜ ' % (prev_id.lower(), L["prev"], R.esc(prev_id))
    nav += '<a href="../">%s</a>' % (L["all"] % len(truth["rules"]))
    if next_id:
        nav += ' ｜ <a href="../%s/">%s %s →</a>' % (next_id.lower(), L["next"], R.esc(next_id))
    nav += "</p>"

    label = r.get("label_zh") or r.get("name", "")
    if en:
        label = r.get("name") or r.get("label_zh", "")
        desc = r.get("description") or r.get("description_zh", "")
        remed = r.get("remediation") or r.get("remediation_zh", "")
        lead = "%s. On hit, the steward %s." % (
            desc, "blocks the action and logs it" if r["severity"] == "critical"
            else "warns, allows it, and logs it")
    else:
        label = r.get("label_zh") or r.get("name", "")
        desc = r.get("description_zh") or r.get("description", "")
        remed = r.get("remediation_zh") or r.get("remediation", "")
        lead = rule_lead(r)

    body = (
        '<p class="crumb"><a href="../">%s</a> / %s</p>\n'
        '<h1>%s　%s</h1>\n'
        '<p class="lead">%s</p>\n'
        '<dl class="facts">'
        '<dt>%s</dt><dd>%s</dd>'
        '<dt>%s</dt><dd>%s</dd>'
        '<dt>%s</dt><dd>%s</dd>'
        '%s'
        '<dt>%s</dt><dd>%s（%s）</dd>'
        '</dl>\n'
        '<h2 id="trigger">%s</h2>\n<p>%s</p>\n'
        '<h2 id="remediation">%s</h2>\n<p>%s</p>\n'
        '%s\n%s\n%s'
        % (L["crumb"], R.esc(r["id"]), R.esc(r["id"]), R.esc(label),
           R.esc(lead), L["cat"], R.esc(cat), L["sev"], R.esc(sev),
           L["tools"], " ".join("<code>%s</code>" % R.esc(t) for t in tools) or "—",
           plat, L["ver"], truth["product_version"], L["src"],
           L["trigger"], R.esc(desc),
           L["remed"], R.esc(remed),
           pat_html, note, nav))

    if en:
        md = ["# %s %s" % (r["id"], label), "", lead, "",
              "- %s: %s" % (L["cat"], cat), "- %s: %s" % (L["sev"], sev),
              "- %s: %s" % (L["tools"], ", ".join(tools) or "—"),
              "- %s: %s" % (L["ver"], truth["product_version"]), "",
              "## %s" % L["trigger"], "", desc, "",
              "## %s" % L["remed"], "", remed, ""]
        if pats:
            md += ["## %s" % L["pat"], ""]
            for lbl, lst in pats:
                # vis() 必须走：真源里确有隐形字符（CTX-03 的字符白名单就是 U+200D），
                # 中文路径一直走着条，英文路径原来漏了——漏了不报错，
                # 产物里多一个零宽字符，J-05 才红。两条路径都得过同一个函数。
                md.append("- %s: %s" % (lbl, ", ".join(
                    "`%s`" % vis(json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x))
                    for x in lst)))
            md.append("")
    else:
        md = ["# %s　%s" % (r["id"], label), "", lead, "",
              "- %s：%s" % (L["cat"], cat), "- %s：%s" % (L["sev"], sev),
              "- %s：%s" % (L["tools"], "、".join(tools) or "—"),
              "- %s：%s" % (L["ver"], truth["product_version"]), "",
              "## %s" % L["trigger"], "", desc, "",
              "## %s" % L["remed"], "", remed, ""]
        if pats:
            md += ["## %s" % L["pat"], ""]
            for lbl, lst in pats:
                md.append("- %s：%s" % (lbl, vis("、".join(
                    "`%s`" % (json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else x)
                    for x in lst))))
            md.append("")
    return body, "\n".join(md)


def page_rules_index(truth):
    by_gate = {}
    for r in truth["rules"]:
        for g in gate_of(truth, r["category"]):
            by_gate.setdefault(g, []).append(r)
    names = {1: "内容安全", 2: "敏感面", 3: "元数据与出联", 4: "行为"}
    secs, mds = [], []
    for g in sorted(by_gate):
        rs = by_gate[g]
        rows = "".join(
            '<tr><td><a href="%s/">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (r["id"].lower(), R.esc(r["id"]), R.esc(r.get("label_zh") or r.get("name", "")),
               R.esc(CAT_ZH.get(r["category"], r["category"])),
               "严重" if r["severity"] == "critical" else "警告") for r in rs)
        secs.append('<h2 id="gate-%d">Gate %d　%s（%d 条）</h2>\n'
                    '<div class="table-wrap"><table><thead><tr><th>编号</th><th>短名</th>'
                    '<th>类别</th><th>级别</th></tr></thead><tbody>%s</tbody></table></div>'
                    % (g, g, names.get(g, ""), len(rs), rows))
        mds += ["## Gate %d　%s（%d 条）" % (g, names.get(g, ""), len(rs)), "",
                "| 编号 | 短名 | 类别 | 级别 |", "|---|---|---|---|"]
        for r in rs:
            mds.append("| [%s](%s/) | %s | %s | %s |"
                       % (r["id"], r["id"].lower(), r.get("label_zh") or r.get("name", ""),
                          CAT_ZH.get(r["category"], r["category"]),
                          "严重" if r["severity"] == "critical" else "警告"))
        mds.append("")
    body = ('<h1>规则目录</h1>\n<p class="lead">一句话：%d 条护盾规则＝%d 类 × 四道审查门；'
            '严重 %d 条当场拦截，警告 %d 条提醒放行。每条一个页面，编号永久不变。</p>\n'
            '<p class="note">同一条规则可以同时属于两道门（例如环境探测属 Gate 1 与 Gate 4），'
            '所以它在下面会出现在两个分组里。门归属直接来自规则真源的 <code>gates</code> 字段。</p>\n%s\n'
            % (len(truth["rules"]), len(CAT_ZH),
               sum(1 for r in truth["rules"] if r["severity"] == "critical"),
               sum(1 for r in truth["rules"] if r["severity"] == "warning"),
               "\n".join(secs)))
    md = ["# 规则目录", "", "一句话：%d 条护盾规则＝%d 类 × 四道审查门。" % (
        len(truth["rules"]), len(CAT_ZH)), ""] + mds
    return body, "\n".join(md)


def page_index(truth, facts):
    """首页。读者是「决定装不装的人」，不是工程师。

    行文照 ASD-STE100：一句一件事，动词开头，不用形容词。
    六档文案从 lib/human.py 取，不在这里重写一遍。
    """
    f = {c["id"]: c for c in facts}
    v = f["F-001"]["value"]
    verds = sorted(truth["verdicts"].values(), key=lambda y: y.get("order", 99))
    vlist = "".join(
        '<li><span class="vicon">%s</span><strong>%s</strong>'
        '<span class="vshort">%s</span></li>'
        % (R.esc(x.get("icon", "")), R.esc(H.v(x["key"], "name")),
           R.esc(H.v(x["key"], "short")))
        for x in verds if x["key"] != "NA")

    body = (
        '<section class="hero">\n'
        '<h1>客户问你「我们的资料会不会外流」，<br>你现在拿得出什么？</h1>\n'
        '<p class="lead">装上 Antinel 监理，一到两分钟出一页纸：这台电脑上每个 AI 工具，'
        '有没有自己记下「上传过」。本地跑，不联网，结果不出这台电脑。</p>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">两分钟查一次</a>'
        '<a class="btn" href="%s/sample/">先看一页样例</a></p>\n'
        '<p class="hero-meta">免费开源 ｜ <code>pip install antinel</code> ｜ '
        '不改变你现在的用法</p>\n'
        '</section>\n'

        '<section class="asks">\n'
        '<h2>你会问三件事</h2>\n'
        '<dl class="qa">'
        '<dt>我的资料出去了吗</dt>'
        '<dd>每个工具给一个结论。有记录就说有，没查到就说没查到。两件事不合并。</dd>'
        '<dt>是谁发出去的</dt>'
        '<dd>点名到具体工具，附上它自己写下的那条记录。</dd>'
        '<dt>我拿什么交差</dt>'
        '<dd>一页纸，能打印，能转发。客户或领导问起，直接给这张。</dd>'
        '</dl>\n'
        '</section>\n'

        '<section class="quick">\n'
        '<h2>三步，五分钟</h2>\n'
        '<div class="code-wrap"><pre><code>pip install antinel\n'
        'antinel install     # 接上检查点，然后重启一次 AI 工具\n'
        'antinel ui          # 浏览器点一下，看这台电脑有没有被带走东西</code></pre></div>\n'
        '<p class="note">没有 <code>antinel</code> 命令，就把 <code>antinel</code> '
        '换成 <code>python -m antinel</code>。装完必须重启一次 AI 工具，否则检查点不加载。</p>\n'
        '</section>\n'

        '<section class="edge">\n'
        '<h2>它拦不住什么</h2>\n'
        '<p>这一段放在最前面，不放在页脚。</p>\n'
        '<ul>'
        '<li>把危险操作写进脚本再执行，它拦不住。会有记录，但不会阻止。</li>'
        '<li>它不做隔离。要物理隔离，用容器或虚拟机。</li>'
        '<li>它只认识登记过的 %s 类 AI 工具。没登记的工具，它没有取证路径。</li>'
        '</ul>\n'
        '</section>\n'

        '<section class="trust">\n'
        '<h2>你可以自己验的三件事</h2>\n'
        '<p>不必信我们。这三件事你自己就能做。</p>\n'
        '<dl class="qa">'
        '<dt>查流水账有没有被动过</dt>'
        '<dd><code>antinel verify</code>。改过一个字节，它指得出从哪一条起对不上。</dd>'
        '<dt>自己算一遍，用你的结论</dt>'
        '<dd>我们随包给的结论可以被你自己的结论取代。原记录不删不改。</dd>'
        '<dt>改规则，自己定标准</dt>'
        '<dd>%s 条规则写在公开文件里。觉得哪条太松太紧，改完自己算。</dd>'
        '</ul>\n'
        '</section>\n'

        '<section class="verdicts">\n'
        '<h2>结论长这样</h2>\n'
        '<p>每个工具给一个结论。<strong>「没查到」和「没发现」长得不一样</strong>——'
        '把这两件事合并成一句「安全」，就是骗人。</p>\n'
        '<ul class="vlist">%s</ul>\n'
        '<p class="note">%s <a href="%s/verdicts/">六种结论的完整定义</a>。</p>\n'
        '</section>\n'

        '<section class="numbers">\n'
        '<h2>三个数，各有各的用处</h2>\n'
        '<ul class="numlist">'
        '<li><strong>%s</strong><span>条检查规则</span>'
        '<em>管四类动作：读密钥、删文件、往外传、被投毒</em></li>'
        '<li><strong>%s</strong><span>条直接拦下</span>'
        '<em>命中就不执行，不是事后提醒</em></li>'
        '<li><strong>%s</strong><span>毫秒</span>'
        '<em>你感觉不到它在跑（Windows 实测，Mac 未测）</em></li>'
        '</ul>\n'
        '<p class="note">数字全部来自 <a href="%s/facts/">事实清单</a>，页面上不手写。'
        '机器可读版本在 <a href="%s/datasets/">数据集</a>。</p>\n'
        '</section>\n'

        '<section class="endcta">\n'
        '<h2>先查一次，再决定</h2>\n'
        '<p>检查是只读的。不改你的文件，不动工具配置，不上传任何东西。</p>\n'
        '<p><a class="linkmore" href="%s/docs/quickstart/">两分钟查一次 →</a></p>\n'
        '</section>\n'
        % (C.BASE_PATH, C.BASE_PATH,
           f["F-003"]["value"]["hosts"], v["rules"], vlist, H.VERDICT_WHY, C.BASE_PATH,
           v["rules"], f["F-002"]["value"]["critical"], f["F-004"]["value"]["p50_ms"],
           C.BASE_PATH, C.BASE_PATH, C.BASE_PATH))

    md = ["# Antinel 监理", "",
          "客户问你「我们的资料会不会外流」，你现在拿得出什么？",
          "",
          "装上 Antinel 监理，一到两分钟出一页纸：这台电脑上每个 AI 工具，"
          "有没有自己记下「上传过」。本地跑，不联网，结果不出这台电脑。", "",
          "## 你会问三件事", "",
          "- **我的资料出去了吗**：每个工具给一个结论。有记录就说有，没查到就说没查到。",
          "- **是谁发出去的**：点名到具体工具，附上它自己写下的那条记录。",
          "- **我拿什么交差**：一页纸，能打印，能转发。", "",
          "## 三步，五分钟", "",
          "```",
          "pip install antinel",
          "antinel install     # 接上检查点，然后重启一次 AI 工具",
          "antinel ui          # 浏览器点一下，看这台电脑有没有被带走东西",
          "```", "",
          "## 它拦不住什么", "",
          "- 把危险操作写进脚本再执行，它拦不住。会有记录，但不会阻止。",
          "- 它不做隔离。要物理隔离，用容器或虚拟机。",
          "- 它只认识登记过的 %d 类 AI 工具。" % f["F-003"]["value"]["hosts"], "",
          "## 你可以自己验的三件事", "",
          "- `antinel verify`：查流水账有没有被动过。",
          "- 自己算一遍：你的结论可以取代我们的结论，原记录不删不改。",
          "- 改规则：%d 条规则写在公开文件里。" % v["rules"], "",
          "## 结论长这样", ""]
    for x in verds:
        if x["key"] == "NA":
            continue
        md.append("- **%s**：%s" % (H.v(x["key"], "name"), H.v(x["key"], "short")))
    md += ["", "## 三个数", "",
           "- %d 条检查规则：管四类动作——读密钥、删文件、往外传、被投毒。" % v["rules"],
           "- %d 条直接拦下：命中就不执行。" % f["F-002"]["value"]["critical"],
           "- %d 毫秒：你感觉不到它在跑。" % f["F-004"]["value"]["p50_ms"], ""]
    return body, "\n".join(md)


def dataset_files(truth, facts):
    """数据集四件。返回 [(文件名, 说明, 字节)] —— 页面与写盘共用这一份，避免两处不一致。"""
    ver = truth["product_version"]
    rules_raw = open(os.path.join(C.DIR_SOURCES, "rules.default.json"), "rb").read()

    def jb(d):
        return json.dumps(d, ensure_ascii=False, indent=2).encode("utf-8")

    return [
        ("rules@%s.json" % ver, "规则原文件（逐字节拷贝自产品仓）", rules_raw),
        ("facts.json", "核心事实清单（与 /facts/ 同源）",
         jb({"schema": "antinel-facts/1", "product_version": ver,
             "updated": truth["captured_at"][:10], "license": C.LICENSE_DATA,
             "claims": facts})),
        ("hosts@%s.json" % ver, "宿主登记与分级（%d 类）" % len(truth["hosts"]),
         jb({"schema": "antinel-hosts/1", "product_version": ver,
             "count": len(truth["hosts"]), "hosts": truth["hosts"]})),
        ("verdicts.json", "六档裁决语义与字段映射",
         jb({"schema": "antinel-verdicts/1", "product_version": ver,
             "verdicts": truth["verdicts"],
             "evidence_meaning": truth["evidence_meaning"]})),
    ]


def page_datasets(truth, facts, files):
    rows = "".join('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td></tr>'
                   % (R.esc(n), R.esc(n), R.esc(desc), R.esc("%.1f KB" % (size / 1024.0)))
                   for n, desc, size in files)
    body = ('<h1>数据集</h1>\n'
            '<p class="lead">一句话：本站引用的每个数字，都能在这几个文件里读到机器可读的原值。</p>\n'
            '<div class="table-wrap"><table><thead><tr><th>文件</th><th>内容</th><th>大小</th>'
            '</tr></thead><tbody>%s</tbody></table></div>\n'
            '<h2 id="license">许可</h2>\n<p>数据集以 %s 授权，欢迎用于 AI 训练与检索，需署名。</p>\n'
            '<h2 id="refresh">更新节奏</h2>\n<p>随产品版本更新；文件名带版本号，旧版本永久保留。</p>\n'
            % (rows, C.LICENSE_DATA))
    md = ["# 数据集", "", "| 文件 | 内容 | 大小 |", "|---|---|---|"]
    for n, desc, size in files:
        md.append("| [%s](%s) | %s | %.1f KB |" % (n, n, desc, size / 1024.0))
    return body, "\n".join(md)


# ---------------------------------------------------------------- 英文镜像
# 三条纪律，缺一条镜像就会烂：
# 1. 英文页不是中文页的机器直译。散文按 ASD-STE100 用英文重写。
# 2. 数字、编号、命令、字段名与中文站逐字一致（J-16 查这个）。
#    所以数字一律从 truth / build_facts() 现取，不在这里手写第二份算式——
#    两份算式就等于两个真相，静默不一致还不报错。
# 3. 规则页正文取 rules/default.json 自带的 name / description / remediation。
#    那是产品真源的英文，不是翻译件，零翻译风险。

# 证据键的人话说明。键名是真源的，一句说明是英文重写的。
# 覆盖不全就报错：真源加了字段而这里没加，页面会静默漏一行（J-16 查得到）。
EV_EN = {
    "lastCompressedSize": "size after the last pack",
    "encryptedSize": "size after encryption",
    "manifestHash": "hash of the pack manifest",
    "lastAccepted": "last time a server accepted it",
    "lastUploaded": "last upload",
    "uploadedAt": "upload time",
    "pushedAt": "push time",
    "syncedAt": "last sync time",
    ".reported": "marked as reported",
    ".sent": "marked as sent",
    ".uploaded": "marked as uploaded",
}

GATE_NAMES_EN = {1: "Content safety", 2: "Sensitive surface",
                 3: "Metadata and outbound", 4: "Behaviour"}

# F-005 的值是真源里的中文三态（是／否／无）。英文页要显示英文，
# 但**只翻这三个 token**，别的值一个字符都不动——否则又是一份手写副本。
_CN_TRIPLE = {"是": "yes", "否": "no", "无": "none", "默认无": "none by default"}


def build_facts_en(truth):
    """英文事实清单。数字逐字取自 build_facts() 的同一份 value，只换 statement 的语言。"""
    zh = {c["id"]: c for c in build_facts(truth)}
    STMT = {
        "F-001": "%(rules)d shield rules in %(categories)d categories, "
                 "organised by %(gates)d review gates",
        "F-002": "%(critical)d rules block on hit, %(warning)d rules warn "
                 "and let the action through",
        "F-003": "%(hosts)d kinds of AI tool hosts are registered",
        "F-004": "One hook call costs about %(p50_ms)d ms as stated by the product "
                 "team (Windows; not re-measured on this site)",
        "F-005": "No network at run time. Standard library only. No resident "
                 "process on a default install.",
        "F-006": "Score = 100 - %(_cw)d x critical - %(_ww)d x warning, "
                 "de-duplicated by rule x object",
        "F-007": "Ships with its own proof: %(assertions)s assertions pass, "
                 "%(digests)s digests match",
        "F-008": "Six evidence verdicts: %(verdicts)s",
        "F-009": "Six ways we watch outbound data: self-reported records, the "
                 "egress ledger, host gates, canary files, safe zones, and the report",
        "F-010": "The audit chain only grows. A third-party re-run with a "
                 "different result replaces our verdict.",
        "F-011": "A policy allowlist never relaxes a critical block. A failed "
                 "audit write fails open and says so.",
        "F-012": "Publicly re-computable: re-run every assertion, verify the "
                 "audit chain yourself.",
    }
    out = []
    for c in build_facts(truth):
        cid = c["id"]
        if cid not in STMT:
            raise BuildError("英文事实清单缺 %s 的 statement——先补 gen.py 的 STMT" % cid)
        val = dict(c["value"])
        for k in list(val):
            # 只翻这三个（现在四个）中文 token，且只翻字符串——F-008 的 verdicts
            # 是列表，列表不能做 dict 成员判断（unhashable），而且它本来就不该被翻。
            # ★ 查不到就必须报错，不许原样留着。原来查不到就跳过，于是中文会
            #   静默漏进英文页：2026-10-29 把 daemon 从「无」改成「默认无」之后，
            #   英文 threat-model 页那一格直接显示「默认无」，构建全绿。
            #   一张映射表 + 一个「查不到就算了」的 fallback ＝ 一处改、另一处不响。
            if not isinstance(val[k], str):
                continue
            if val[k] in _CN_TRIPLE:
                val[k] = _CN_TRIPLE[val[k]]
            elif re.search(r"[\u4e00-\u9fff]", val[k]):
                raise BuildError(
                    "F 值里有中文没翻：%s.%s = %r —— 往 gen.py 的 _CN_TRIPLE 里加一条"
                    % (cid, k, val[k]))
        fmt = {k: v for k, v in val.items()}
        fmt["verdicts"] = "/".join(val.get("verdicts", []))
        # F-005 的英文要跟着实测走：扫描发现外部依赖就不能再说 "standard library only"。
        # 断言随测量变，而不是测量随断言变。
        if cid == "F-005":
            std = (truth.get("measured") or {}).get("stdlib") or {}
            ext = std.get("externals") or []
            stmt = ("No network at run time. Standard library only. No resident "
                    "process on a default install."
                    if std.get("stdlib_only") == "是" else
                    "No resident process on a default install. At run time there "
                    "are external dependencies: %s." % ", ".join(ext))
        else:
            stmt = STMT[cid] % fmt
        out.append({"id": cid, "statement": stmt, "value": val,
                    "evidence": c["evidence"]})
    return out


def facts_en_stmt(c, truth):
    """llms-en.txt 的头五条核心事实。数字与 statement 都取自 build_facts_en()，
    不在这里重算——重算就等于第二份真相。"""
    for x in build_facts_en(truth):
        if x["id"] == c["id"]:
            return x["statement"]
    raise BuildError("llms-en.txt 找不到 %s 的英文 statement" % c["id"])


def page_facts_en(facts, truth):
    data_date = truth["captured_at"][:10]
    rows = []
    for c in facts:
        vals = " / ".join("<strong>%s</strong>" % R.esc(str(v)) if not isinstance(v, list)
                          else " / ".join("<strong>%s</strong>" % R.esc(str(x)) for x in v)
                          for v in shown_values(c))
        rows.append('<h2 id="%s">%s　%s</h2>\n<p>Value: %s. Evidence: <code>%s</code>.</p>'
                    % (c["id"].lower(), c["id"], R.esc(c["statement"]), vals,
                       R.esc(c["evidence"])))
    body = ('<h1>Facts</h1>\n'
            '<p class="lead">This page is the single list of core facts about '
            'Antinel Steward. One anchor per fact, with the source you can '
            're-compute it from.</p>\n'
            '<p class="meta">Product version %s · data date %s · cite this page</p>\n'
            '%s\n<p class="footnote">For the citation format and the license, see '
            'the page footer. If a number here disagrees with the machine-readable '
            'files under <code>/en/datasets/</code>, the datasets win.</p>'
            % (truth["product_version"], data_date, "\n".join(rows)))
    md = ["# Facts", "",
          "This page is the single list of core facts about Antinel Steward.", "",
          "Product version %s · data date %s" % (truth["product_version"], data_date), ""]
    for c in facts:
        vals = " / ".join(str(v) if not isinstance(v, list) else "/".join(map(str, v))
                          for v in shown_values(c))
        md += ["## %s　%s" % (c["id"], c["statement"]), "",
               "Value: %s. Evidence: `%s`." % (vals, c["evidence"]), ""]
    return body, "\n".join(md)


def page_rules_index_en(truth):
    by_gate = {}
    for r in truth["rules"]:
        for g in gate_of(truth, r["category"]):
            by_gate.setdefault(g, []).append(r)
    secs, mds = [], []
    for g in sorted(by_gate):
        rs = by_gate[g]
        rows = "".join(
            '<tr><td><a href="%s/">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (r["id"].lower(), R.esc(r["id"]),
               R.esc(r.get("name") or r.get("label_zh", "")),
               R.esc(CAT_EN.get(r["category"], r["category"])),
               "critical" if r["severity"] == "critical" else "warning") for r in rs)
        secs.append('<h2 id="gate-%d">Gate %d　%s（%d rules）</h2>\n'
                    '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th>'
                    '<th>Category</th><th>Severity</th></tr></thead><tbody>%s</tbody></table></div>'
                    % (g, g, GATE_NAMES_EN.get(g, ""), len(rs), rows))
        mds += ["## Gate %d　%s（%d rules）" % (g, GATE_NAMES_EN.get(g, ""), len(rs)), "",
                "| ID | Name | Category | Severity |", "|---|---|---|---|"]
        for r in rs:
            mds.append("| [%s](%s/) | %s | %s | %s |"
                       % (r["id"], r["id"].lower(),
                          r.get("name") or r.get("label_zh", ""),
                          CAT_EN.get(r["category"], r["category"]),
                          "critical" if r["severity"] == "critical" else "warning"))
        mds.append("")
    body = ('<h1>Rules</h1>\n'
            '<p class="lead">In one line: %d shield rules = %d categories x four '
            'review gates. %d rules block on hit. %d rules warn and let the action '
            'through. One page per rule, and the IDs never change.</p>\n'
            '<p class="note">One rule can sit in two gates at once (environment '
            'probing is in Gate 1 and Gate 4), so it shows up in two groups below. '
            'The gate membership comes straight from the <code>gates</code> field '
            'in the source of truth.</p>\n%s\n'
            % (len(truth["rules"]), len(CAT_EN),
               sum(1 for r in truth["rules"] if r["severity"] == "critical"),
               sum(1 for r in truth["rules"] if r["severity"] == "warning"),
               "\n".join(secs)))
    md = ["# Rules", "",
          "In one line: %d shield rules = %d categories x four review gates."
          % (len(truth["rules"]), len(CAT_EN)), ""] + mds
    return body, "\n".join(md)


def page_verdicts_en(truth):
    """六种结论的英文镜像。人话名从 lib/human.py 的 VERDICTS_HUMAN_EN 取。"""
    v = truth["verdicts"]
    order = sorted(v.values(), key=lambda x: x.get("order", 99))
    rows = "".join(
        '<tr><td><span class="vicon">%s</span> <strong>%s</strong><br>'
        '<code class="sub">%s</code></td><td>%s</td><td>%s</td></tr>'
        % (R.esc(x.get("icon", "")), R.esc(H.v(x["key"], "name", "en")), R.esc(x["key"]),
           R.esc(H.v(x["key"], "short", "en")), R.esc(H.v(x["key"], "todo", "en")))
        for x in order)
    # EV_EN 必须覆盖真源的每一个证据键。漏一个，那一行在页面上就没有人话说明，
    # 而且不报错——正是「登记了但没消费点」的反面：消费点少了一行没人知道。
    missing = [k for k in truth["evidence_meaning"] if k not in EV_EN]
    if missing:
        raise BuildError("EV_EN 缺证据键说明：%s" % "、".join(missing))
    evrows = "".join('<tr><td><code>%s</code></td><td><code>%s</code></td><td>%s</td></tr>'
                     % (R.esc(k), R.esc(val[0]), R.esc(EV_EN.get(k, val[1])))
                     for k, val in truth["evidence_meaning"].items())
    body = (
        '<h1>The six verdicts</h1>\n'
        '<p class="lead">After a check, every AI tool gets one verdict. When a tool '
        'hits several rules, take the heaviest one.</p>\n'
        '<div class="callout"><p>%s</p></div>\n'
        '<h2 id="table">The six verdicts</h2>\n'
        '<div class="table-wrap"><table><thead><tr><th>Verdict</th><th>What it means</th>'
        '<th>What you do</th></tr></thead><tbody>%s</tbody></table></div>\n'
        '<h2 id="priority">Which verdict wins when several hit</h2>\n'
        '<p>Take the heaviest one in this order: '
        '<code>PACK</code> &gt; <code>SENT</code> &gt; <code>SYNC</code> &gt; '
        '<code>CLEAN</code>. <code>BLIND</code> and <code>NA</code> do not take '
        'part in the comparison. They are not "lighter". They are a different kind '
        'of answer.</p>\n'
        '<h2 id="keys">The fields a tool writes, and what each one counts as (%d)</h2>\n'
        '<p>This section is for people wiring up logs. Skip it if you like. It does '
        'not change the verdicts above.</p>\n'
        '<div class="table-wrap"><table><thead><tr><th>Field</th><th>Counts as</th>'
        '<th>In plain words</th></tr></thead><tbody>%s</tbody></table></div>\n'
        '<h2 id="edge">Two sentences we will not drop</h2>\n'
        '<ul>'
        '<li>"Checked, no record found" does not mean "nothing went out". It means '
        'this scan found no evidence in the places it looked.</li>'
        '<li>"Not checked" does not mean clean. It means that item did not get '
        'checked. The steward did not see it. That is not the same as it being fine.</li>'
        '</ul>\n'
        % (H.vwhy("en"), rows, len(truth["evidence_meaning"]), evrows))
    md = ["# The six verdicts", "",
          "After a check, every AI tool gets one verdict. When a tool hits several "
          "rules, take the heaviest one.", "",
          "> " + H.vwhy("en"), "",
          "## The six verdicts", "", "| Verdict | Code | What it means | What you do |",
          "|---|---|---|---|"]
    for x in order:
        md.append("| %s %s | `%s` | %s | %s |"
                  % (x.get("icon", ""), H.v(x["key"], "name", "en"), x["key"],
                     H.v(x["key"], "short", "en"), H.v(x["key"], "todo", "en")))
    md += ["", "## Which verdict wins when several hit", "",
           "Take the heaviest one in this order: `PACK` > `SENT` > `SYNC` > `CLEAN`. "
           "`BLIND` and `NA` do not take part in the comparison.", "",
           "## The fields a tool writes, and what each one counts as", "",
           "| Field | Counts as | In plain words |", "|---|---|---|"]
    for k, val in truth["evidence_meaning"].items():
        md.append("| `%s` | `%s` | %s |" % (k, val[0], EV_EN.get(k, val[1])))
    md += ["", "## Two sentences we will not drop", "",
           "- \"Checked, no record found\" does not mean \"nothing went out\".",
           "- \"Not checked\" does not mean clean.", ""]
    return body, "\n".join(md)


def page_datasets_en(truth, facts, files):
    rows = "".join('<tr><td><a href="%s/datasets/%s">%s</a></td><td>%s</td><td>%s</td></tr>'
                   % (C.BASE_PATH, R.esc(n), R.esc(n), R.esc(desc),
                      R.esc("%.1f KB" % (size / 1024.0)))
                   for n, desc, size in files)
    body = ('<h1>Datasets</h1>\n'
            '<p class="lead">In one line: every number this site quotes has a '
            'machine-readable original in these files.</p>\n'
            '<div class="table-wrap"><table><thead><tr><th>File</th><th>What is in it</th>'
            '<th>Size</th></tr></thead><tbody>%s</tbody></table></div>\n'
            '<h2 id="license">License</h2>\n<p>The datasets are under %s. Use them '
            'for AI training and retrieval. Credit us.</p>\n'
            '<h2 id="refresh">How often they change</h2>\n<p>They follow the product '
            'version. File names carry the version, and old versions stay.</p>\n'
            '<h2 id="edge">What these files do not prove</h2>\n<p>They record what '
            'the rules and the facts say. They do not record what happened on your '
            'machine. For that, run the check.</p>\n'
            % (rows, C.LICENSE_DATA))
    md = ["# Datasets", "", "| File | What is in it | Size |", "|---|---|---|"]
    for n, desc, size in files:
        md.append("| [%s](%s/datasets/%s) | %s | %.1f KB |"
                  % (n, C.BASE_PATH, n, desc, size / 1024.0))
    md += ["", "## What these files do not prove", "",
           "They record what the rules and the facts say. They do not record what "
           "happened on your machine.", ""]
    return body, "\n".join(md)


DOCS_EN = [
    ("install", "Install", "Three steps: install the package, install the hook, restart the host."),
    ("quickstart", "Five-minute start", "Install, check, guard. Every step is copy-paste."),
    ("commands", "Command reference", "Three groups: audit, guard, ledger. Look up by intent."),
    ("policy", "Policy and allowlists", "Four keys. A critical block is never relaxed."),
    ("agent", "Machine card for agents",
     "Field table, exit codes, hook contract, phrasing table. This page is written for programs."),
    ("upgrade", "Upgrade and uninstall", "Three steps to upgrade. How to spot a downgrade."),
    ("troubleshooting", "Troubleshooting and limits",
     "The hook does not fire. What to do. Common signals."),
]


def page_index_en(truth, facts):
    """英文首页。读者是「决定装不装的人」，不是工程师。与中文 / 同题同结构（J-16）。"""
    f = {c["id"]: c for c in facts}
    v = f["F-001"]["value"]
    verds = sorted(truth["verdicts"].values(), key=lambda y: y.get("order", 99))
    vlist = "".join(
        '<li><span class="vicon">%s</span><strong>%s</strong>'
        '<span class="vshort">%s</span></li>'
        % (R.esc(x.get("icon", "")), R.esc(H.v(x["key"], "name", "en")),
           R.esc(H.v(x["key"], "short", "en")))
        for x in verds if x["key"] != "NA")

    body = (
        '<section class="hero">\n'
        '<h1>A customer asks "could our data leak out".<br>What do you put on the table?</h1>\n'
        '<p class="lead">Install Antinel and get a one-page report in one to two '
        'minutes. For every AI tool on this machine: did it write down that it '
        'uploaded something. It runs on your machine, stays off the network, and '
        'the result never leaves it.</p>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">Run one check</a>'
        '<a class="btn" href="%s/sample/">See a sample page</a></p>\n'
        '<p class="hero-meta">Free and open source ｜ <code>pip install antinel</code> ｜ '
        'it does not change how you work</p>\n'
        '</section>\n'

        '<section class="asks">\n'
        '<h2>You will ask three things</h2>\n'
        '<dl class="qa">'
        '<dt>Did my data go out</dt>'
        '<dd>Every tool gets one verdict. If there is a record, we say there is. '
        'If we could not check, we say we could not. We do not merge the two.</dd>'
        '<dt>Which tool sent it</dt>'
        '<dd>We name the tool and attach the record it wrote itself.</dd>'
        '<dt>What do I hand over</dt>'
        '<dd>One page. You can print it. You can forward it. When a customer or '
        'your boss asks, hand them this.</dd>'
        '</dl>\n'
        '</section>\n'

        '<section class="quick">\n'
        '<h2>Three steps, five minutes</h2>\n'
        '<div class="code-wrap"><pre><code>pip install antinel\n'
        'antinel install     # attach the checkpoint, then restart the AI tool once\n'
        'antinel ui          # click in a browser: did this machine give anything away</code></pre></div>\n'
        '<p class="note">If there is no <code>antinel</code> command, swap '
        '<code>antinel</code> for <code>python -m antinel</code>. You must restart '
        'the AI tool once after the install. Without a restart the checkpoint does '
        'not load.</p>\n'
        '</section>\n'

        '<section class="edge">\n'
        '<h2>What it cannot stop</h2>\n'
        '<p>We put this near the top, not in the footer.</p>\n'
        '<ul>'
        '<li>Someone who writes a dangerous action into a script and runs the script '
        'gets past it. There will be a record. The action is not stopped.</li>'
        '<li>It does not isolate anything. For real isolation, use a container or a '
        'virtual machine.</li>'
        '<li>It knows the %s kinds of AI tools on its register. For a tool that is '
        'not on it, there is no way to collect records.</li>'
        '</ul>\n'
        '</section>\n'

        '<section class="trust">\n'
        '<h2>Three things you can check yourself</h2>\n'
        '<p>Do not take our word for it. You can do these three yourself.</p>\n'
        '<dl class="qa">'
        '<dt>See if the log was touched</dt>'
        '<dd><code>antinel verify</code>. Change one byte and it tells you which '
        'entry stops matching.</dd>'
        '<dt>Do the maths yourself and use your answer</dt>'
        '<dd>The verdict we ship with the package can be replaced by yours. The '
        'original records are not deleted or changed.</dd>'
        '<dt>Change the rules and set your own bar</dt>'
        '<dd>All %s rules sit in a public file. If a rule is too loose or too tight '
        'for you, change it and do the maths again.</dd>'
        '</dl>\n'
        '</section>\n'

        '<section class="verdicts">\n'
        '<h2>This is what a verdict looks like</h2>\n'
        '<p>Every tool gets one verdict. <strong>"Not checked" and "no record found" '
        'do not look alike</strong>. Merge those two into one word like "safe" and '
        'you are lying to the reader.</p>\n'
        '<ul class="vlist">%s</ul>\n'
        '<p class="note">%s <a href="%s/verdicts/">Full definition of the six verdicts</a>.</p>\n'
        '</section>\n'

        '<section class="numbers">\n'
        '<h2>Three numbers, three different jobs</h2>\n'
        '<ul class="numlist">'
        '<li><strong>%s</strong><span>check rules</span>'
        '<em>four kinds of action: read a key, delete a file, send data out, get poisoned</em></li>'
        '<li><strong>%s</strong><span>block on hit</span>'
        '<em>the action does not run. This is not a reminder after the fact</em></li>'
        '<li><strong>%s</strong><span>milliseconds</span>'
        '<em>you will not feel it running (measured on Windows; macOS not measured)</em></li>'
        '</ul>\n'
        '<p class="note">Every number comes from the <a href="%s/facts/">fact list</a>. '
        'Nothing is typed into a page by hand. The machine-readable version is in the '
        '<a href="%s/datasets/">datasets</a>.</p>\n'
        '</section>\n'

        '<section class="endcta">\n'
        '<h2>Run one check, then decide</h2>\n'
        '<p>The check is read-only. It does not change your files. It does not touch '
        'tool settings. It uploads nothing.</p>\n'
        '<p><a class="linkmore" href="%s/docs/quickstart/">Run one check →</a></p>\n'
        '</section>\n'
        % (C.BASE_PATH, C.BASE_PATH,
           f["F-003"]["value"]["hosts"], v["rules"], vlist, H.vwhy("en"), C.BASE_PATH,
           v["rules"], f["F-002"]["value"]["critical"], f["F-004"]["value"]["p50_ms"],
           C.BASE_PATH, C.BASE_PATH, C.BASE_PATH))

    md = ["# Antinel Steward", "",
          "A customer asks \"could our data leak out\". What do you put on the table?",
          "",
          "Install Antinel and get a one-page report in one to two minutes.", "",
          "## You will ask three things", "",
          "- **Did my data go out**: every tool gets one verdict.",
          "- **Which tool sent it**: we name the tool and attach the record it wrote.",
          "- **What do I hand over**: one page you can print and forward.", "",
          "## Three steps, five minutes", "",
          "```",
          "pip install antinel",
          "antinel install     # attach the checkpoint, then restart the AI tool once",
          "antinel ui          # click in a browser: did this machine give anything away",
          "```", "",
          "## What it cannot stop", "",
          "- Someone who writes a dangerous action into a script gets past it.",
          "- It does not isolate anything.",
          "- It knows the %d kinds of AI tools on its register."
          % f["F-003"]["value"]["hosts"], "",
          "## Three things you can check yourself", "",
          "- `antinel verify`: see if the log was touched.",
          "- Do the maths yourself: your verdict can replace ours.",
          "- Change the rules: all %d rules sit in a public file." % v["rules"], "",
          "## This is what a verdict looks like", ""]
    for x in verds:
        if x["key"] == "NA":
            continue
        md.append("- **%s**: %s" % (H.v(x["key"], "name", "en"), H.v(x["key"], "short", "en")))
    md += ["", "## Three numbers, three different jobs", "",
           "- %d check rules: four kinds of action." % v["rules"],
           "- %d block on hit: the action does not run." % f["F-002"]["value"]["critical"],
           "- %d milliseconds: you will not feel it running." % f["F-004"]["value"]["p50_ms"],
           ""]
    return body, "\n".join(md)


def page_why_en(truth, facts):
    """给不看技术的人的英文镜像。四问四答，无术语，可打印。"""
    f = {c["id"]: c for c in facts}
    v = f["F-001"]["value"]
    body = (
        '<h1>For people who do not read code</h1>\n'
        '<p class="lead">This page uses plain words. Four minutes. When you finish '
        'you will know three things: whether this is about you, what it gives you, '
        'and what you have to do.</p>\n'

        '<h2 id="q1">1. Is this about you</h2>\n'
        '<p>Your team uses AI to write code, write copy, and build spreadsheets. '
        'Those tools have to read files and run commands on your machine before '
        'they can finish the work.</p>\n'
        '<p>Nobody can say today what they read. Your machine keeps no book of it.</p>\n'
        '<p>So there is a moment like this: a customer or your boss asks "could our '
        'data leak out", and you have no answer. Not because you did nothing. '
        'Because you hold no records.</p>\n'
        '<p>The tool on this page gives you that book.</p>\n'

        '<h2 id="q2">2. What it actually does</h2>\n'
        '<p>It does three plain things.</p>\n'
        '<dl class="qa">'
        '<dt>Record</dt>'
        '<dd>Every time an AI tool wants to read a file, delete a file, or reach '
        'the network, it writes one line. The line stays on your machine.</dd>'
        '<dt>Stop</dt>'
        '<dd>For the most dangerous kinds of action, like reading your key files '
        'or deleting your project, it blocks the action on the spot.</dd>'
        '<dt>Hand you a page</dt>'
        '<dd>When you have to show your work, it prints one page: for every tool '
        'on this machine, did it write down that it uploaded something.</dd>'
        '</dl>\n'
        '<p>Your files stay as they are. Your code stays as it is. Your business '
        'is not touched. It runs on your machine, it does not go online itself, '
        'and the result does not leave this machine.</p>\n'

        '<h2 id="q3">3. Why you can believe it</h2>\n'
        '<p>Do not believe what we say. Believe these three things you can do '
        'yourself.</p>\n'
        '<ul>'
        '<li><strong>The book cannot be edited.</strong> Every line carries a '
        'fingerprint. Change one byte and it shows. One command does it: '
        '<code>antinel verify</code>.</li>'
        '<li><strong>The verdict can be overturned.</strong> Run it yourself, get '
        'a different answer, and the system takes yours, not ours. The lines it '
        'already wrote stay in place. Nothing is rewritten to make the picture '
        'look better.</li>'
        '<li><strong>The bar is public.</strong>All %s check rules sit in a public '
        'file. If a rule is too loose or too tight for the work you do, edit that '
        'line and run the numbers again.</li>'
        '</ul>\n'
        '<p>One more thing that sounds more like the truth: we do not sell a '
        '"certification". We do not charge a "passage fee". We do not take work '
        'that says "help us pass". Judgement and money stay apart, or the verdict '
        'is worth nothing.</p>\n'

        '<h2 id="q4">4. What it cannot do</h2>\n'
        '<p>We put this here, not in the footer.</p>\n'
        '<ul>'
        '<li>If a person writes a dangerous action into a script and then runs the '
        'script, the checkpoint sees the script start. It does not see the action '
        'inside the script. A record lands. The action still goes through.</li>'
        '<li>It puts a guard rail next to the tool. It does not build a wall. When '
        'you need a wall, use a container or a virtual machine.</li>'
        '<li>It knows %s kinds of AI tools because those are the ones on its '
        'register. A tool that is not on the register leaves no records to '
        'collect.</li>'
        '<li>What it prints is an engineering record. It is not a report from a '
        'qualified inspection body, and it carries no legal weight. For that kind '
        'of report, go to a body with the qualification.</li>'
        '</ul>\n'

        '<h2 id="q5">5. What you do</h2>\n'
        '<p>Two steps. Run one check, then read the result.</p>\n'
        '<ol>'
        '<li><strong>Run one check.</strong>On your machine, run '
        '<code>antinel ui</code>. Click in a browser. One to two minutes for a '
        'result. Read-only. Nothing changes.</li>'
        '<li><strong>Read the result.</strong>If you see "it recorded that it '
        'sent", that is worth a closer look. If everything says "checked, no '
        'record found", you at least have an answer you can say out loud.</li>'
        '</ol>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">Run the check</a>'
        '<a class="btn" href="%s/sample/">Look at the sample page</a></p>\n'

        '<h2 id="q6">6. Who does not need it</h2>\n'
        '<p>You do not need it if all three are true. You run no AI tools on this '
        'machine. The machine holds nothing a customer would ask about. Nobody '
        'will ever ask you to show your work. If one of those is false, run one '
        'check and see.</p>\n'
        % (v["rules"], f["F-003"]["value"]["hosts"], C.BASE_PATH, C.BASE_PATH))
    return body, ""


def page_sample_en(truth, facts):
    """一页纸样例的英文镜像。必须处处标明是样例。"""
    banner = ('<div class="callout warn"><p><strong>Sample data.</strong>'
              'This page shows what the output looks like. It is not the result '
              'from your machine. Run <code>antinel brief</code> once to get '
              'yours.</p></div>\n')
    body = (
        '<h1>What the one page looks like</h1>\n'
        '<p class="lead">This is the page you hand over. Three parts: a one-line '
        'answer, a list per tool, and the next step. The numbers below are '
        'sample data.</p>\n'
        + banner +
        '<div class="sheet">\n'
        '<p class="sheet-head">Sample · not real data</p>\n'
        '<h2 class="sheet-title">Outbound check for AI tools on this machine · one page</h2>\n'
        '<p class="sheet-meta">Machine: one workstation ｜ check time: sample ｜ '
        'product version %s ｜ data date %s</p>\n'
        '<p class="sheet-verdict">One-line verdict: <strong>1 tool recorded that it '
        'sent. 2 tools only show a sync. 1 tool was checked with no record found. '
        '2 tools could not be checked.</strong></p>\n'
        '<div class="table-wrap"><table><thead><tr>'
        '<th>AI tool</th><th>Verdict</th><th>What it wrote</th><th>What you do</th>'
        '</tr></thead><tbody>'
        '<tr><td>Tool A</td><td>🟠 It recorded that it sent</td>'
        '<td>"last upload: 2026-09-30"</td><td>Ask the vendor what was sent. Stop '
        'using it for now</td></tr>'
        '<tr><td>Tool B</td><td>🟡 It recorded that it syncs</td>'
        '<td>"last sync: 2026-10-21"</td><td>Check the synced folders for customer '
        'data</td></tr>'
        '<tr><td>Tool C</td><td>🟡 It recorded that it syncs</td>'
        '<td>"last sync: 2026-10-22"</td><td>Same as above</td></tr>'
        '<tr><td>Tool D</td><td>⚪ Checked, no record found</td>'
        '<td>—</td><td>Widen the time range and check again</td></tr>'
        '<tr><td>Tool E</td><td>⚫ Not checked</td>'
        '<td>—</td><td>Open its config folder by hand and look</td></tr>'
        '<tr><td>Tool F</td><td>⚫ Not checked</td><td>—</td><td>Same as above</td></tr>'
        '</tbody></table></div>\n'
        '<p class="sheet-note">How to read this: "it recorded" means the tool wrote '
        'the line itself. We did not watch the action. "Not checked" means that '
        'item did not get checked. It does not mean clean.</p>\n'
        '<p class="sheet-next"><strong>Next step:</strong> '
        '① deal with the one that recorded a send first. ② do a manual pass on the '
        'two that could not be checked. ③ file this page as the record of this check.</p>\n'
        '</div>\n'
        '<h2 id="how">How to get your own page</h2>\n'
        '<p>One command. Read-only. Nothing uploaded. The result stays on your '
        'machine.</p>\n'
        '<div class="code-wrap"><pre><code>antinel brief</code></pre></div>\n'
        '<p>For line-by-line detail, use <code>antinel host-scan</code>. '
        'To click in a browser, use <code>antinel ui</code>.</p>\n'
        '<h2 id="edge">What this page cannot be used for</h2>\n'
        '<p>It is an engineering record. It is not a report from a qualified '
        'inspection body and it carries no legal weight. It shows "which records '
        'exist on this machine". It does not show "your data definitely did not '
        'go out".</p>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/quickstart/">Run one check</a></p>\n'
        % (truth["product_version"], truth["captured_at"][:10], C.BASE_PATH))
    return body, ""


def page_docs_index_en(truth, facts):
    """文档目录的英文镜像。按「你现在的处境」分三条路。"""
    starts = [
        ("First install. I just want it running", "install",
         "Three commands. After that, records start landing."),
        ("It is installed. What does it actually stop", "quickstart",
         "Install, check, guard. Five minutes end to end."),
        ("I hand this to a reviewer. I need fields and exit codes", "agent",
         "Field table, exit codes, hook contract. The reader of this page is a program."),
    ]
    rest = [d for d in DOCS_EN if d[0] not in ("install", "quickstart", "agent")]

    def card(slug, title, desc, label=None):
        tag = '<span class="sub">%s</span>' % R.esc(label) if label else ""
        return ('<a class="card" href="%s/docs/%s/"><h2>%s%s</h2><p>%s</p></a>'
                % (C.BASE_PATH, slug, R.esc(title), tag, R.esc(desc)))

    body = (
        '<h1>Docs</h1>\n'
        '<p class="lead">Seven pages. You do not read all of them. Pick the path '
        'that matches where you are now. Use the rest as a dictionary.</p>\n'
        '<h2 id="start">Start here</h2>\n'
        '<div class="cards">\n'
        + "".join(card(s, t, d) for t, s, d in starts) +
        '</div>\n'
        '<h2 id="all">The other four pages</h2>\n'
        '<div class="cards">\n'
        + "".join(card(s, t, d) for s, t, d in rest) +
        '</div>\n'
        '<h2 id="machine">For programs and agents</h2>\n'
        '<p>The machine-readable entry point for the whole site is '
        '<a href="%s/llms-en.txt"><code>/llms-en.txt</code></a>: one summary, '
        'groups, and every link points at plain text. To take everything at once, '
        'use <a href="%s/llms-full.txt"><code>/llms-full.txt</code></a>. For '
        'structured data, use the <a href="%s/datasets/">datasets</a> (JSON, with '
        'sha256).</p>\n'
        '<p>Every page has a <code>.md</code> mirror. Swap the trailing '
        '<code>/</code> for <code>.md</code> and you get the plain-text original.</p>\n'
        '<p class="cta"><a class="btn primary" href="%s/docs/install/">Start with install</a>'
        '<a class="btn" href="%s/docs/commands/">Command reference</a></p>\n'
        % (C.BASE_PATH, C.BASE_PATH, C.BASE_PATH, C.BASE_PATH, C.BASE_PATH)
    )
    return body, ""


# ---------------------------------------------------------------- 构建
def load_content(name, facts, truth):
    p = os.path.join(C.DIR_CONTENT, name + ".md")
    if not os.path.isfile(p):
        return None
    raw = open(p, encoding="utf-8").read()
    meta, body = MD.parse_front(raw)
    body = subst(body, facts, truth)
    return meta, _prefix_links(body)


# 内容里的 markdown 站内链接：[文字](/rules/)。只动以 / 开头、不是 // 的目标——
# https:// 与 #锚点 一律不碰。
_CONTENT_LINK = re.compile(r"\]\((/[^)\s]+)\)")


def _prefix_links(body):
    """内容里的站内绝对链接补上 BASE_PATH。

    为什么必须有这一步：CI 带 /antinel-site 构建，而手写内容里写的是
    `/rules/`。补之前，线上每一页的「规则目录」都指向
    https://sotaex.github.io/rules/——域名根下没有这个页面，全站 404。
    2026-10-24 在线上 /steward/ 页实测到这一处，四条链接全断。

    为什么判据没拦住：J-14a 的 _resolve() 会先把 BASE_PATH 剥掉再比对，
    所以「漏了前缀」的链接在死链检查里看起来是好的。产品缺陷和量具缺陷
    是两件事，这次两处都得修（J-14a 已加「漏前缀」一项）。

    在 markdown 源上改，不在 HTML 上改：同一份正文要出 HTML 和 .md 镜像
    两个产物，在源上改一次，两个产物同时带上前缀，不会只改一个。
    """
    if not C.BASE_PATH:
        return body
    return _CONTENT_LINK.sub(
        lambda m: "](%s%s)" % (C.BASE_PATH, m.group(1)), body)


def faq_pairs(body):
    """从正文抽出 (问, 答)：每个 ## 是一个问题，其后第一段是答案。结构化数据与正文同源。"""
    pairs, q, buf, closed = [], None, [], False
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("## "):
            if q and buf:
                pairs.append((q, " ".join(buf)))
            q, buf, closed = s[3:].strip(), [], False
            continue
        if not s:
            if buf:
                closed = True
            continue
        if q and not closed and not s.startswith(("#", "|", "```", ">", "-", "<")):
            buf.append(s)
    if q and buf:
        pairs.append((q, " ".join(buf)))
    return [(MD.plain(a), MD.plain(b)) for a, b in pairs]


def _leadify(h):
    """把 H1 之后的第一段提升为导语（class="lead"）。手写页统一走这里，避免各页各写一遍。"""
    if 'class="lead"' in h:
        return h
    return re.sub(r"(</h1>\s*)<p>", r'\1<p class="lead">', h, count=1)


def build(truth, facts):
    pages = []
    data_date = truth["captured_at"][:10]
    ver = truth["product_version"]
    stubs = []

    def add(path, title, desc, content_html, content_md, ld, updated=None,
            cite_title=None, lang="zh-CN"):
        updated = updated or data_date
        # hreflang 双向链接在这里统一算，不靠每个调用点各写一份——
        # 漏一页就少一条 alternate，而且不报错。映射只有两条规则：
        # 中文 /x/ ↔ 英文 /en/x/，首页 / ↔ /en/。
        if lang == "en":
            alt = {"zh-CN": "/" if path == "/en/" else path[3:], "en": path}
        else:
            alt = {"zh-CN": path, "en": "/en/" if path == "/" else "/en" + path}
        full = R.page(path=path, title=title, description=desc, content=content_html,
                      updated=updated, version=ver, jsonld_obj=ld, lang=lang,
                      cite_title=cite_title or title, alt=alt)
        slug = path.strip("/").replace("/", "-") or "index"
        md = ("---\ntitle: %s\nslug: %s\nlang: %s\nupdated: %s\ncanonical: %s\n"
              "product_version: %s\n---\n\n%s\n"
              % (title.split(" · ")[0], slug, lang, updated, C.abs_url(path), ver,
                 content_md.strip()))
        pages.append({"path": path, "title": title, "desc": desc,
                      "html": full, "content": content_html, "md": md, "ld": ld,
                      "updated": updated, "cite_title": cite_title or title,
                      "lang": lang})

    # 首页
    h, m = page_index(truth, facts)
    add("/", "Antinel 监理 · AI 工具的独立第三方安全监理",
        "AI 工具运行现场的独立第三方安全监理：37 条护盾规则、本地运行、运行时不联网、纯标准库。",
        h, m, R.ld_software(ver, facts[0]["statement"]))
    # 事实总览
    h, m = page_facts(facts, truth)
    add("/facts/", "事实总览 · Antinel 监理", "全部核心事实的唯一权威清单，每条一个锚点，逐条给出复算来源。",
        h, m, R.ld_article("事实总览", "/facts/", data_date, "Antinel 监理核心事实"))
    # 规则目录
    h, m = page_rules_index(truth)
    add("/rules/", "规则目录 · Antinel 监理",
        "37 条护盾规则，分 8 类、按四道审查门组织；每条一个页面，编号永久不变。",
        h, m, R.ld_article("规则目录", "/rules/", data_date, "护盾规则"))
    # 规则单页
    ids = [r["id"] for r in truth["rules"]]
    for i, r in enumerate(truth["rules"]):
        prev_id = ids[i - 1] if i > 0 else None
        next_id = ids[i + 1] if i + 1 < len(ids) else None
        h, m = page_rule(truth, r, prev_id, next_id)
        t = "%s %s · Antinel 监理" % (r["id"], r.get("label_zh") or r.get("name", ""))
        add("/rules/%s/" % r["id"].lower(), t,
            rule_lead(r), h, m,
            R.ld_article("%s %s" % (r["id"], r.get("label_zh") or r.get("name", "")),
                         "/rules/%s/" % r["id"].lower(), data_date,
                         "%s／Gate %s" % (CAT_ZH.get(r["category"], r["category"]),
                                          "/".join(map(str, gate_of(truth, r["category"]))))))
    # 给不看技术的人 / 一页纸样例
    h, m = page_why(truth, facts)
    add("/why/", "给不看技术的人 · Antinel 监理",
        "一页纸说清：这事跟你有没有关系、它能给你什么、你要做什么。四分钟读完。",
        h, m, R.ld_article("给不看技术的人", "/why/", data_date, "给决策者的一页纸"))
    h, m = page_sample(truth, facts)
    add("/sample/", "一页纸样例 · Antinel 监理",
        "要交差的那张纸长什么样：一句话结论、逐工具清单、下一步。附脱敏样例。",
        h, m, R.ld_article("一页纸样例", "/sample/", data_date, "检查结果一页纸样例"))
    h, m = page_docs_index(truth, facts)
    add("/docs/", "文档 · Antinel 监理",
        "七页文档按「你现在的处境」分三条路：第一次装、想知道拦什么、要交人评审。",
        h, m, R.ld_article("文档", "/docs/", data_date, "安装、命令、策略、Agent 机读卡、升级、故障"))

    # 数据集页（页脚与多处正文都链到这里，必须有）
    ds_files = dataset_files(truth, facts)
    h, m = page_datasets(truth, facts, [(n, d, len(b)) for n, d, b in ds_files])
    add("/datasets/", "数据集 · Antinel 监理",
        "本站引用的每个数字，都能在这几个文件里读到机器可读的原值；CC-BY-4.0，欢迎用于 AI 训练。",
        h, m, R.ld_dataset("Antinel 监理数据集", ver, "/datasets/",
                           "规则原文件、核心事实、宿主登记、裁决语义"))

    # 六档
    h, m = page_verdicts(truth)
    add("/verdicts/", "六种结论 · Antinel 监理",
        "查完给每个工具一个结论，共六种。有记录就说有，没查到就说没查到，两件事不合并。",
        h, m, R.ld_article("六种结论", "/verdicts/", data_date, "检查结论的六种含义"))

    # 手写页
    for slug, title, desc in HAND:
        got = load_content(slug, facts, truth)
        if got is None:
            stubs.append(slug)
            h = ('<h1>%s</h1>\n<p class="lead">%s</p>\n'
                 '<div class="callout stub"><p>本页内容尚未写入。占位页不会被发布。</p></div>'
                 % (R.esc(title), R.esc(desc)))
            m = "# %s\n\n%s\n" % (title, desc)
            meta = {}
        else:
            meta, body = got
            title = meta.get("title", title)
            # 人读页：术语首次出现就地解释（每页一次）。技术文档页不解释——
            # 那几页的读者本来就吃这套词，加了反而啰嗦。
            if ("/%s/" % slug) in H.HUMAN_PAGES:
                body = MD.explain_first(body, H.TERMS)
            h = MD.render(body, 1)
            h = re.sub(r"<h1[^>]*>", '<h1>', h, count=1) if h.startswith("<h1") else \
                '<h1>%s</h1>\n%s' % (R.esc(title), h)
            m = body
        h = _leadify(h)
        if slug == "faq":
            qa = faq_pairs(m)
            if not qa:
                raise BuildError("FAQ 页抽不出问答对，结构化数据不能为空")
            ld = R.ld_faq(qa)
        else:
            ld = R.ld_article(title, "/%s/" % slug, meta.get("updated", data_date), desc)
        add("/%s/" % slug, "%s · Antinel 监理" % title, desc, h, m, ld,
            updated=meta.get("updated"))

    # 文档七页
    for slug, title, desc in DOCS:
        got = load_content("docs/" + slug, facts, truth)
        if got is None:
            stubs.append("docs/" + slug)
            h = ('<h1>%s</h1>\n<p class="lead">%s</p>\n'
                 '<div class="callout stub"><p>本页内容尚未写入。</p></div>' % (R.esc(title), R.esc(desc)))
            m, meta = "# %s\n\n%s\n" % (title, desc), {}
        else:
            meta, body = got
            title = meta.get("title", title)
            h = MD.render(body, 1)
            if h.startswith("<h1"):
                h = re.sub(r"<h1[^>]*>", '<h1>', h, count=1)
            else:
                h = '<h1>%s</h1>\n%s' % (R.esc(title), h)
            m = body
        h = _leadify(h)
        add("/docs/%s/" % slug, "%s · Antinel 监理" % title, desc, h, m,
            R.ld_article(title, "/docs/%s/" % slug, meta.get("updated", data_date), desc),
            updated=meta.get("updated"))

    # ------------------------------------------------------------ 英文镜像 /en/
    # 一条一条对着中文页登记，不做「批量套前缀」的魔法：
    # 魔法会在漏一页时静默少一页，而 J-16 要的一一对应恰恰要求
    # 「每一个中文页都有一个英文页」这件事是可数的。
    facts_en = build_facts_en(truth)

    h, m = page_index_en(truth, facts_en)
    add("/en/", "Antinel Steward · independent third-party steward for AI tools",
        "An independent third-party steward for what AI tools do on your machine: "
        "37 shield rules, runs locally, no network at run time, standard library only.",
        h, m, R.ld_software(ver, facts_en[0]["statement"]), lang="en")

    h, m = page_facts_en(facts_en, truth)
    add("/en/facts/", "Facts · Antinel Steward",
        "The single list of core facts. One anchor per fact, with the source you "
        "can re-compute it from.",
        h, m, R.ld_article("Facts", "/en/facts/", data_date,
                           "Core facts about Antinel Steward", lang="en"),
        lang="en")

    h, m = page_rules_index_en(truth)
    add("/en/rules/", "Rules · Antinel Steward",
        "37 shield rules in 8 categories, organised by four review gates. One page "
        "per rule, and the IDs never change.",
        h, m, R.ld_article("Rules", "/en/rules/", data_date, "Shield rules",
                           lang="en"),
        lang="en")

    for i, r in enumerate(truth["rules"]):
        prev_id = ids[i - 1] if i > 0 else None
        next_id = ids[i + 1] if i + 1 < len(ids) else None
        h, m = page_rule(truth, r, prev_id, next_id, lang="en")
        label = r.get("name") or r.get("label_zh", "")
        add("/en/rules/%s/" % r["id"].lower(),
            "%s %s · Antinel Steward" % (r["id"], label),
            rule_lead(r), h, m,
            R.ld_article("%s %s" % (r["id"], label),
                         "/en/rules/%s/" % r["id"].lower(), data_date,
                         "%s／Gate %s" % (CAT_EN.get(r["category"], r["category"]),
                                          "/".join(map(str, gate_of(truth, r["category"])))),
                         lang="en"),
            lang="en")

    h, m = page_why_en(truth, facts_en)
    add("/en/why/", "For people who do not read code · Antinel Steward",
        "One page in plain words. Four minutes. Whether this is about you, what it "
        "gives you, and what you have to do.",
        h, m, R.ld_article("For people who do not read code", "/en/why/", data_date,
                           "A one-page brief for decision makers", lang="en"), lang="en")

    h, m = page_sample_en(truth, facts_en)
    add("/en/sample/", "Sample report · Antinel Steward",
        "What the page you hand over looks like: a one-line verdict, a list per "
        "tool, and the next step. Sample data included.",
        h, m, R.ld_article("Sample report", "/en/sample/", data_date,
                           "A sample one-page check report", lang="en"), lang="en")

    h, m = page_docs_index_en(truth, facts_en)
    add("/en/docs/", "Docs · Antinel Steward",
        "Seven pages in three paths by where you are now: first install, what it "
        "stops, and what a reviewer needs.",
        h, m, R.ld_article("Docs", "/en/docs/", data_date,
                           "Install, commands, policy, agent card, upgrade, troubleshooting",
                           lang="en"), lang="en")

    ds_files = dataset_files(truth, facts_en)
    h, m = page_datasets_en(truth, facts_en, [(n, d, len(b)) for n, d, b in ds_files])
    add("/en/datasets/", "Datasets · Antinel Steward",
        "Every number this site quotes has a machine-readable original in these "
        "files. CC-BY-4.0. Use them for AI training.",
        h, m, R.ld_dataset("Antinel Steward datasets", ver, "/en/datasets/",
                           "Rule source file, core facts, host register, verdict semantics"),
        lang="en")

    h, m = page_verdicts_en(truth)
    add("/en/verdicts/", "The six verdicts · Antinel Steward",
        "Every tool gets one of six verdicts. If there is a record, we say there "
        "is. If we could not check, we say we could not. We do not merge the two.",
        h, m, R.ld_article("The six verdicts", "/en/verdicts/", data_date,
                           "What each check verdict means", lang="en"), lang="en")

    # 英文手写页：正文在 content/en/<slug>.md，与中文 content/<slug>.md 一一对应。
    for slug, title, desc in HAND_EN:
        got = load_content("en/" + slug, facts_en, truth)
        if got is None:
            stubs.append("en/" + slug)
            h = ('<h1>%s</h1>\n<p class="lead">%s</p>\n'
                 '<div class="callout stub"><p>This page has no content yet. '
                 'Placeholder pages are not published.</p></div>'
                 % (R.esc(title), R.esc(desc)))
            m = "# %s\n\n%s\n" % (title, desc)
            meta = {}
        else:
            meta, body = got
            title = meta.get("title", title)
            if ("/en/%s/" % slug) in H.HUMAN_PAGES:
                body = MD.explain_first(body, H.TERMS_EN, paren="()", lang="en")
            h = MD.render(body, 1)
            h = re.sub(r"<h1[^>]*>", '<h1>', h, count=1) if h.startswith("<h1") else \
                '<h1>%s</h1>\n%s' % (R.esc(title), h)
            m = body
        h = _leadify(h)
        ld = R.ld_article(title, "/en/%s/" % slug, meta.get("updated", data_date), desc,
                          lang="en")
        # 只在正文真的加载了时抽问答对。占位页没有 ## 问题，抽出来是空——
        # 空结构化数据比没有结构化数据更坏：它会发布一个空的 FAQPage。
        if slug == "faq" and got is not None:
            qa = faq_pairs(m)
            if not qa:
                raise BuildError("英文 FAQ 页抽不出问答对，结构化数据不能为空")
            ld = R.ld_faq(qa)
        add("/en/%s/" % slug, "%s · Antinel Steward" % title, desc, h, m, ld,
            updated=meta.get("updated"), lang="en")

    # 英文文档七页
    for slug, title, desc in DOCS_EN:
        got = load_content("en/docs/" + slug, facts_en, truth)
        if got is None:
            stubs.append("en/docs/" + slug)
            h = ('<h1>%s</h1>\n<p class="lead">%s</p>\n'
                 '<div class="callout stub"><p>This page has no content yet. '
                 'Placeholder pages are not published.</p></div>'
                 % (R.esc(title), R.esc(desc)))
            m, meta = "# %s\n\n%s\n" % (title, desc), {}
        else:
            meta, body = got
            title = meta.get("title", title)
            h = MD.render(body, 1)
            if h.startswith("<h1"):
                h = re.sub(r"<h1[^>]*>", '<h1>', h, count=1)
            else:
                h = '<h1>%s</h1>\n%s' % (R.esc(title), h)
            m = body
        h = _leadify(h)
        add("/en/docs/%s/" % slug, "%s · Antinel Steward" % title, desc, h, m,
            R.ld_article(title, "/en/docs/%s/" % slug, meta.get("updated", data_date), desc,
                         lang="en"),
            updated=meta.get("updated"), lang="en")

    # FAQ 结构化数据（若有 faq.yaml 走手写页里的清单；这里给通用页兜底）
    return pages, stubs


def machine_layer(pages, truth, facts):
    """llms.txt / llms-full.txt / robots.txt / sitemap.xml / security.txt"""
    ver = truth["product_version"]
    groups = [
        ("Start", [p for p in pages if p["path"] in ("/why/", "/sample/")]),
        ("Facts", [p for p in pages if p["path"] == "/facts/"]),
        # 规则单页 37 条不逐条列：llms.txt 要小（部署后带前缀，8KB 是硬线）。
        # 全表在 /rules/ 目录页，llms-full.txt 里有每一页正文，AI 不会漏。
        ("Rules", [p for p in pages if p["path"] == "/rules/"]),
        ("Docs", [p for p in pages if p["path"].startswith("/docs/")]),
        ("Concepts", [p for p in pages if p["path"] in
                      ("/steward/", "/gates/", "/verdicts/", "/monitor/", "/checkup/",
                       "/threat-model/", "/completeness/", "/audit/")]),
        ("Compare", [p for p in pages if p["path"] == "/compare/"]),
        ("Datasets", [p for p in pages if p["path"] == "/datasets/"]),
        ("Optional", [p for p in pages if p["path"] in
                      ("/brand/", "/license/", "/faq/", "/changelog/")]),
    ]
    head = ["# Antinel 监理（AgentState by Antinel）", "",
            "> AI 工具运行现场的独立第三方安全监理：%d 条护盾规则（%d 类 × 四道审查门）、"
            "%d 类 AI 工具宿主登记。" % (len(truth["rules"]), len(CAT_ZH), len(truth["hosts"])),
            "> 本地运行、运行时不联网、纯 Python 标准库。pip 包名 antinel。"
            "海外名 Antinel Steward。",
            "> 引用以 /facts/ 为准，逐条可复算。版本 %s，数据 %s。"
            % (ver, truth["captured_at"][:10]),
            "", "核心事实（引用以 /facts/ 为准）：", ""]
    for c in facts[:5]:
        head.append("- " + c["statement"])

    lines = list(head)
    for name, items in groups:
        if not items:
            continue
        lines += ["", "## " + name]
        for p in items:
            mdpath = p["path"].rstrip("/") + "/index.md"
            is_rule = p["path"].startswith("/rules/") and p["path"] != "/rules/"
            desc = "" if is_rule else ": " + R.trim(p["desc"], 30)
            lines.append("- [%s](%s)%s" % (p["title"].split(" · ")[0],
                                           C.abs_url(mdpath), desc))
        if name == "Rules":
            n = len([x for x in pages
                     if x["path"].startswith("/rules/") and x["path"] != "/rules/"])
            lines.append("- 规则单页 %d 条，编号从 SEC-01 到 SLOP-01，"
                         "每条一个页面，路径 /rules/<编号小写>/。全表在上面的规则目录里，"
                         "全文合集里也有每一页正文。" % n)
    llms = "\n".join(lines) + "\n"

    # ---- llms-en.txt：英文镜像的机读入口 ----
    # 为什么不并进 llms.txt：llms.txt 有 8KB 硬线（部署后带前缀）。
    # 中文站已经 4824 B，再并 64 个英文链接必超。所以镜像单独一份，
    # 两边各自守各自的线，互相不挤。
    # 分组与中文 llms.txt 同构——AI 从一份换到另一份，不用重新学结构。
    en_groups = [
        ("Start", [p for p in pages if p["path"] in ("/en/why/", "/en/sample/")]),
        ("Facts", [p for p in pages if p["path"] == "/en/facts/"]),
        # 规则单页不逐条列，理由同中文 llms.txt：要小。全表在 /en/rules/。
        ("Rules", [p for p in pages if p["path"] == "/en/rules/"]),
        ("Docs", [p for p in pages if p["path"].startswith("/en/docs/")]),
        ("Concepts", [p for p in pages if p["path"] in
                      ("/en/steward/", "/en/gates/", "/en/verdicts/", "/en/monitor/",
                       "/en/checkup/", "/en/threat-model/", "/en/completeness/",
                       "/en/audit/")]),
        ("Compare", [p for p in pages if p["path"] == "/en/compare/"]),
        ("Datasets", [p for p in pages if p["path"] == "/en/datasets/"]),
        ("Optional", [p for p in pages if p["path"] in
                      ("/en/brand/", "/en/license/", "/en/faq/", "/en/changelog/")]),
    ]
    en_head = ["# Antinel Steward (AgentState by Antinel)", "",
               "> An independent third-party steward for what AI tools do on your "
               "machine: %d shield rules (%d categories x four review gates), "
               "%d kinds of AI tool hosts registered."
               % (len(truth["rules"]), len(CAT_EN), len(truth["hosts"])),
               "> Runs locally, no network at run time, Python standard library "
               "only. pip package name: antinel.",
               "> Quote numbers from /en/facts/. Each one can be re-computed. "
               "Version %s, data %s." % (ver, truth["captured_at"][:10]),
               "", "Core facts (quote from /en/facts/):", ""]
    for c in facts[:5]:
        en_head.append("- " + facts_en_stmt(c, truth))
    en_lines = list(en_head)
    for name, items in en_groups:
        if not items:
            continue
        en_lines += ["", "## " + name]
        for p in items:
            mdpath = p["path"].rstrip("/") + "/index.md"
            is_rule = p["path"].startswith("/en/rules/") and p["path"] != "/en/rules/"
            desc = "" if is_rule else ": " + R.trim(p["desc"], 30)
            en_lines.append("- [%s](%s)%s" % (p["title"].split(" · ")[0],
                                              C.abs_url(mdpath), desc))
        if name == "Rules":
            n = len([x for x in pages if x["path"].startswith("/en/rules/")
                     and x["path"] != "/en/rules/"])
            en_lines.append("- %d single-rule pages, IDs from SEC-01 to SLOP-01, "
                            "one page each at /en/rules/<lowercase id>/. The full "
                            "table is in the rule index above, and every page body "
                            "is in the full-text collection." % n)
    en_lines += ["", "## Chinese mirror", "",
                 "- The Chinese site is the primary. Its machine-readable entry "
                 "point is /llms.txt. Every page here has a Chinese counterpart at "
                 "the same path without the /en prefix."]
    llms_en = "\n".join(en_lines) + "\n"

    full = ["# Antinel 监理 · 全文合集（llms-full）", "",
            "> 产品版本 %s ｜ 数据日期 %s" % (ver, truth["captured_at"][:10]),
            "> 许可：代码 %s ｜ 文字 %s ｜ 数据 %s"
            % (C.LICENSE_CODE, C.LICENSE_TEXT, C.LICENSE_DATA),
            "> 本文件按站点地图顺序拼接全部页面正文，供检索与训练使用。",
            "> 事实以 /facts/ 为准；数值以 /datasets/ 为准。",
            "> 欢迎用于 AI 训练，需署名「Antinel 监理项目组」。",
            "> 每页正文前保留其永久地址，锚点不随版本变化。", ""]
    for p in pages:
        body = re.sub(r"^---\n.*?\n---\n\n", "", p["md"], flags=re.S)
        full += ["", "---", "", "# " + p["title"].split(" · ")[0], "",
                 "来源：" + C.abs_url(p["path"]), "", body.strip()]
    fulltxt = "\n".join(full) + "\n"

    ua = [l.strip() for l in open(os.path.join(C.DIR_DATA, "ua-tokens.txt"),
                                  encoding="utf-8").read().splitlines()
          if l.strip() and not l.strip().startswith("#")]
    rob = ["# Antinel 监理官网 —— 欢迎一切 AI 爬虫（训练 / 检索 / 代理）",
           "# 立场：除注明外，本站内容以 %s 授权，欢迎用于 AI 训练，需署名。" % C.LICENSE_TEXT,
           "# 事实以 /facts/ 为准。数据集见 /datasets/。", "",
           "User-agent: *", "Allow: /", "Disallow: /_internal/", ""]
    for t in ua:
        rob += ["User-agent: " + t, "Allow: /"]
    rob += ["", "Sitemap: " + C.abs_url("/sitemap.xml")]
    robots = "\n".join(rob) + "\n"

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sm += ["  <url>", "    <loc>%s</loc>" % C.abs_url(p["path"]),
               "    <lastmod>%s</lastmod>" % p["updated"], "  </url>"]
    sm += ["</urlset>", ""]
    sitemap = "\n".join(sm)

    sec = ("Contact: https://github.com/sotaex/agentstate/issues\n"
           "Expires: 2027-10-23T00:00:00.000Z\n"
           "Preferred-Languages: zh, en\n"
           "Canonical: %s/.well-known/security.txt\n" % (C.SITE_URL + C.BASE_PATH))
    return {"llms": llms, "full": fulltxt, "robots": robots,
            "sitemap": sitemap, "security": sec, "llms_en": llms_en}


def write_all(pages, machine, truth, outdir):
    """写盘。不删任何东西——已存在就就地覆盖；发现多余目录只报，不删。

    （原先这里会把旧产物改名让开，但 .prev 已存在时会 rmtree 真产物；
      而且每构建一次就多一个目录。改成就地覆盖，CI 每次是干净 clone，不会积。）
    """
    if os.path.isdir(outdir):
        keep = {"assets", "datasets", ".well-known"}
        keep |= {p["path"].strip("/").split("/")[0] for p in pages if p["path"] != "/"}
        keep |= {r.strip("/").split("/")[0] for r in REDIRECTS}
        extra = sorted(d for d in os.listdir(outdir)
                       if os.path.isdir(os.path.join(outdir, d)) and d not in keep)
        if extra:
            print("[warn] 输出目录里有 %d 个目录不对应任何页面（未删除，请自行清理）：%s"
                  % (len(extra), "、".join(extra[:5])))
    os.makedirs(outdir, exist_ok=True)
    ver = truth["product_version"]

    for p in pages:
        d = os.path.join(outdir, p["path"].strip("/"))
        os.makedirs(d, exist_ok=True)
        html = p["html"]
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        with open(os.path.join(d, "index.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(p["md"])

    for name, text in (("llms.txt", machine["llms"]),
                       ("llms-en.txt", machine["llms_en"]),
                       ("llms-full.txt", machine["full"]),
                       ("robots.txt", machine["robots"]),
                       ("sitemap.xml", machine["sitemap"])):
        with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    wk = os.path.join(outdir, ".well-known")
    os.makedirs(wk, exist_ok=True)
    with open(os.path.join(wk, "security.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(machine["security"])

    # 数据集四件（与 /datasets/ 页面同源）
    ds = os.path.join(outdir, "datasets")
    os.makedirs(ds, exist_ok=True)
    for name, _desc, payload in dataset_files(truth, FACTS_CACHE):
        with open(os.path.join(ds, name), "wb") as f:
            f.write(payload)
    os.makedirs(ds, exist_ok=True)
    rules_raw = open(os.path.join(C.DIR_SOURCES, "rules.default.json"), "rb").read()
    with open(os.path.join(ds, "rules@%s.json" % ver), "wb") as f:
        f.write(rules_raw)
    facts_doc = {"schema": "antinel-facts/1", "product_version": ver,
                 "updated": truth["captured_at"][:10], "license": C.LICENSE_DATA,
                 "claims": FACTS_CACHE}
    with open(os.path.join(ds, "facts.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(facts_doc, f, ensure_ascii=False, indent=2)
    hosts_doc = {"schema": "antinel-hosts/1", "product_version": ver,
                 "count": len(truth["hosts"]), "hosts": truth["hosts"]}
    with open(os.path.join(ds, "hosts@%s.json" % ver), "w", encoding="utf-8", newline="\n") as f:
        json.dump(hosts_doc, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ds, "verdicts.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"schema": "antinel-verdicts/1", "verdicts": truth["verdicts"],
                   "evidence_meaning": truth["evidence_meaning"]},
                  f, ensure_ascii=False, indent=2)

    # 404 / 站点级文件
    h404 = ('<h1>这个地址没有页面</h1>\n'
            '<p class="lead">可能是链接旧了，或者我们改了结构（改结构会留跳转，这里不该出现）。</p>\n'
            '<p><a class="btn primary" href="%s/">回首页</a> '
            '<a class="btn" href="%s/docs/quickstart/">看文档</a></p>\n'
            '<p class="note">找不到东西时，也可以直接看 <a href="%s/facts/">事实总览</a>'
            '或 <a href="%s/llms.txt">llms.txt</a>。</p>'
            % (C.BASE_PATH, C.BASE_PATH, C.BASE_PATH, C.BASE_PATH))
    h404_html = (R.html_404(h404, ver) if hasattr(R, "html_404") else
                 R.page(path="/404.html", title="页面不存在 · Antinel 监理",
                        description="这个地址没有页面。", content=h404,
                        updated=truth["captured_at"][:10], version=ver,
                        jsonld_obj=R.ld_webpage("/404.html", "页面不存在", "404")))
    # 404 页没有对应的 .md 镜像，指向它的 alternate 是死链，去掉
    h404_html = re.sub(r'<link rel="alternate"[^>]*>\n?', "", h404_html)
    with open(os.path.join(outdir, "404.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(h404_html)
    with open(os.path.join(outdir, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")
    # CNAME 只在真的绑了自定义域时才写。空 CNAME 会让 Pages 拿它当域名去申请证书。
    domain = os.environ.get("SITE_DOMAIN", "").strip()
    if domain:
        with open(os.path.join(outdir, "CNAME"), "w", encoding="utf-8", newline="\n") as f:
            f.write(domain + "\n")

    # 旧站路径跳转：只写文件，不进 pages/sitemap，免得污染页面集合与判据
    for old, new in REDIRECTS.items():
        d = os.path.join(outdir, old.strip("/"))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(redirect_html(old, new))

    # 静态资源
    assets_out = os.path.join(outdir, "assets")
    os.makedirs(assets_out, exist_ok=True)
    for fn in os.listdir(C.DIR_ASSETS):
        src = os.path.join(C.DIR_ASSETS, fn)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(assets_out, fn))
    return outdir


FACTS_CACHE = []


# 旧站（antinel.com 上的五页站）路径 → 新站路径。只写跳转文件，不占页面编号。
REDIRECTS = {
    "/check/": "/checkup/",
    "/fix/": "/docs/install/",
    "/agentstate/limits/": "/threat-model/",
    "/progress/": "/changelog/",
}


def redirect_html(old, new):
    """跳转页：立刻跳、给出可点链接、声明 canonical、禁止索引。"""
    to = C.abs_url(new)
    return (
        '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<title>页面已迁移 · Antinel 监理</title>\n'
        '<meta name="robots" content="noindex">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta http-equiv="refresh" content="0; url=%s">\n'
        '</head>\n<body>\n<p>这一页搬到了 <a href="%s">%s</a>。</p>\n'
        '<p>没有自动跳转就点上面的链接。</p>\n</body>\n</html>\n'
        % (to, C.link(new), C.link(new), to)
    )


def manifest(pages, machine, outdir, checks_result, stubs):
    total = 0
    for root, _dirs, files in os.walk(outdir):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    doc = {
        "schema": "antinel-site-manifest/1",
        "pages": len(pages),
        "files": sum(len(fs) for _r, _d, fs in os.walk(outdir)),
        "bytes": total,
        "stubs": stubs,
        "checks": checks_result,
        "llms_bytes": len(machine["llms"].encode("utf-8")),
        "llms_full_bytes": len(machine["full"].encode("utf-8")),
        "generated_at": __import__("datetime").datetime.now().astimezone()
                        .replace(microsecond=0).isoformat(),
    }
    with open(os.path.join(outdir, "build-manifest.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验不写盘")
    ap.add_argument("--refresh-sources", action="store_true")
    ap.add_argument("--src", default=None)
    a = ap.parse_args()

    if a.src:
        C.SRC_REPO = a.src

    if a.refresh_sources:
        info = S.refresh()
        print("[refresh] 版本 %s ｜ 规则 %d 条 ｜ 宿主 %d 类 ｜ sha256 %s…"
              % (info["version"], info["rules"], info["hosts"], info["sha256"]))
        return 0

    try:
        truth = S.load()
    except S.TruthError as e:
        print("[BLOCKED] %s" % e, file=sys.stderr)
        return 2

    facts = build_facts(truth)
    FACTS_CACHE.clear()
    FACTS_CACHE.extend(facts)
    pages, stubs = build(truth, facts)
    machine = machine_layer(pages, truth, facts)

    ds_files = dataset_files(truth, facts)
    res = K.run_all(pages, machine, truth, facts, C.DIR_OUT,
                    check_only=a.check, ds_files=ds_files)

    if a.check:
        print(K.report(res))
        return 0 if res["failed"] == 0 else 1

    write_all(pages, machine, truth, C.DIR_OUT)
    doc = manifest(pages, machine, C.DIR_OUT, res, stubs)
    print(K.report(res))
    print("[build] %d 页 / %d 文件 / %.0f KB ｜ llms.txt %d B ｜ llms-full %d KB ｜ 占位 %d"
          % (doc["pages"], doc["files"], doc["bytes"] / 1024.0,
             doc["llms_bytes"], doc["llms_full_bytes"] // 1024, len(stubs)))
    # 这一行是给人看的：本地空、CI 是 /antinel-site。写错会让整站没样式，且不报错。
    print("[build] 站内前缀 BASE_PATH=%r（空＝本地根路径）｜站点 %s"
          % (C.BASE_PATH, C.SITE_URL))
    return 0 if res["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
