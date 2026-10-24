# -*- coding: utf-8 -*-
"""人读层文案的唯一真源。

三条纪律（对应 site-spec/09）：
1. 同一件事只有一个叫法。术语表 TERMS 就是那份「唯一叫法」清单。
2. 首次出现就地解释。TERMS 的值就是那句解释，第二次起可直接用简称。
3. 六档的措辞只在这里写一次。首页、/verdicts/、/checkup/ 都从这里取，
   免得三处各写一份，然后静默不一致。

行文照 ASD-STE100 的路子：短句、动词开头、一句一件事、不用形容词。
"""

# ---------------------------------------------------------------- 六种结论
# name   人话名（读者看到的）
# short  一句「这意味着什么」
# todo   看到了该做什么
# code   英文代号，给工程师对接日志用，降为副标
VERDICTS_HUMAN = {    "PACK": {
        "name": "它自己记着：打包过",
        "short": "工具写下了「上次打包后的体积」。包有没有出去，看下一档。",
        "todo": "先查它最近传过什么。",
    },
    "SENT": {
        "name": "它自己记着：发出去过",
        "short": "工具写下了「已上传」「已被接受」。这一档最该看。",
        "todo": "拿这一档去问工具方，或者先停用它。",
    },
    "SYNC": {
        "name": "它自己记着：在同步",
        "short": "它跟某个服务端保持同步。同步不等于把整个项目传上去。",
        "todo": "看同步的目录里有没有客户资料。",
    },
    "CLEAN": {
        "name": "查过了，没找到记录",
        "short": "扫到了，这次没找到证据。不等于清白。",
        "todo": "换一个时间范围，再查一次。",
    },
    "BLIND": {
        "name": "没查到（这一项没查成）",
        "short": "你电脑上有它，我们没找到它的记录。别当没事。",
        "todo": "手动打开它的配置目录看一眼。",
    },
    "NA": {
        "name": "跟它无关",
        "short": "更新程序之类，不涉及数据外传。",
        "todo": "不用管。",
    },
}

# 为什么只能说「它自己记着」——只解释一次，全站引用
VERDICT_WHY = ("为什么说「它自己记着」：我们读的是工具自己写下的记录，"
               "不是亲眼看见的动作。所以最重的结论也只能说到「它自己承认发过」。")

# 英文镜像的六档。中文的六档在 VERDICTS_HUMAN，两份各自维护，
# 但**档位、代号、优先级顺序完全一致**（J-16 查跨语言一致性）。
# 英文不逐字翻中文——按 ASD-STE100 重写；「self-reported」是这里唯一
# 选定的叫法，全站不再换成 admitted / confessed / claimed。
VERDICTS_HUMAN_EN = {
    "PACK": {
        "name": "It recorded that it packed",
        "short": "The tool wrote down a last pack size. Whether the pack left the machine is the next verdict.",
        "todo": "Check what it sent recently.",
    },
    "SENT": {
        "name": "It recorded that it sent",
        "short": "The tool wrote down \"uploaded\" or \"accepted\". This is the verdict to look at first.",
        "todo": "Ask the tool vendor about it, or stop using the tool for now.",
    },
    "SYNC": {
        "name": "It recorded that it syncs",
        "short": "It keeps a sync session with a server. A sync is not the same as sending the whole project.",
        "todo": "Look at the synced folders for customer data.",
    },
    "CLEAN": {
        "name": "Checked, no record found",
        "short": "The scan ran and found no self-reported record this time. That is not a clean bill.",
        "todo": "Widen the time range and scan again.",
    },
    "BLIND": {
        "name": "Not checked (the scanner could not reach it)",
        "short": "The tool is on your machine, but the scanner did not reach its records. Do not treat this as fine.",
        "todo": "Open its config folder by hand and look.",
    },
    "NA": {
        "name": "Not applicable",
        "short": "Updaters and similar. They do not move your data out.",
        "todo": "Nothing to do.",
    },
}

# 英文镜像的「为什么只能说它自己记着」。同一句话，两种语言，各写各的。
VERDICT_WHY_EN = ("Why we say \"it recorded\": we read the records the tool wrote itself. "
                  "We did not watch the action happen. So the heaviest verdict we can "
                  "give is still \"it recorded that it sent\".")

# ---------------------------------------------------------------- 术语表
# 键＝旧说法（也是 J-24 的黑名单），值＝首次出现时给的那句解释
TERMS = {
    "宿主": "你电脑上那些 AI 工具，比如 Claude Code、Cursor",
    "钩子": "装进 AI 工具里的检查点，每次调用先过它",
    "审计链": "只加不改的流水账，改一个字节都能算出来",
    "判据": "机器自动执行的检查",
    "口径": "按什么标准算",
    "复跑": "你自己再算一遍",
    "闸门": "关卡",
    "护盾规则": "检查规则",
    "裁决": "结论",
    "金丝雀": "埋一个假文件当诱饵，谁读它谁暴露",
    "安全区": "划一块地，管得更严",
    "出口账本": "谁在往外连",
    "门闸": "在往外传的那一步拦住",
    "完备矩阵": "四十个「这类问题查过没有」的格子",
    "证据键": "工具记下的字段名",
    "锚点": "定位点",
    "fail-open": "记不下来的时候先放行，并且告诉你",
}

# ---------------------------------------------------------------- 英文镜像的人读层词表
# 中文的表在上面，英文的表在这里。两份各自维护，但**职责完全对应**：
# TERMS_EN 是 J-24 的英文术语黑名单，BANNED_EN 是 J-28 的英文营销词，
# EDGE_WORDS_EN 是 J-27 的英文边界段关键词。
# 为什么不能只查中文表：英文页若不进这套判据，就等于人读层只约束中文站，
# 镜像页可以随便写——那正是「镜像」最容易烂掉的地方。
TERMS_EN = {
    "host": "an AI tool that runs on your machine, such as Claude Code or Cursor",
    "hook": "a checkpoint installed inside an AI tool; every call passes through it first",
    "audit chain": "an append-only log; change one byte and it shows",
    "canary file": "a decoy file planted on purpose; whoever reads it gives itself away",
    "safe zone": "a folder you mark for stricter checks",
    "egress ledger": "the log of who connects outbound",
    "verdict": "the one conclusion a tool gets after a check",
    "re-run": "run the same check yourself and compare",
    "fail-open": "when it cannot record, it lets the action through and tells you",
    "evidence key": "a field name the tool itself wrote down",
}
# 为什么这张表比中文的 TERMS 短，且不含 "steward" 和 "gate"：
# 1. "steward" 是产品概念，有自己的页面（/en/steward/），跟中文表不收录「监理」同理。
# 2. "gate" 不收，因为它是 "gates"／"mitigate"／"investigate" 的子串，
#    按子串匹配会误报——会误报的检查器用两次就没人信（项目纪律）。
#    四道门的解释在 /en/gates/ 那一页，不靠首段注释。
# 3. 中文表收录「闸门」而不收「门」，是同一条道理：收的是真行话，不是常用词。

# 一级：营销专属词，无条件禁。中文那张表是词，英文这张表按短语查——
# 英文的营销味全在短语里（"military-grade"、"battle-tested"），
# 单个单词禁不完，也不该禁（"secure" 本身不是营销词）。
BANNED_EN = ["military-grade", "battle-tested", "world-class", "best-in-class",
             "game-changer", "cutting-edge", "state-of-the-art", "revolutionary",
             "unbreakable", "bulletproof", "hacker-proof", "100% secure",
             "zero risk", "risk-free", "guaranteed safe", "fully automatic",
             "set and forget", "one-click fix", "magic bullet", "silver bullet"]

# 二级：技术语境也常用，只在肯定语境算营销。
BANNED_SOFT_EN = ["absolute", "100%", "guaranteed", "totally safe", "completely safe",
                  "always safe", "never fails"]

# 人读页必须出现的「边界」段：h2 命中任一关键词即算。
# 与中文 EDGE_WORDS 对应——中文查「做不到／不拦」，英文查 "cannot" / "does not"。
EDGE_WORDS_EN = ("cannot", "can not", "does not", "do not", "will not", "not a ",
                  "no legal", "outside", "limits", "boundaries", "won't")


def human_terms(lang):
    """按语言取术语表。缺语言直接报错，不给默认值。"""
    return TERMS_EN if lang == "en" else TERMS


def human_banned(lang):
    return (BANNED_EN, BANNED_SOFT_EN) if lang == "en" else (BANNED, BANNED_SOFT)


def human_edge_words(lang):
    return EDGE_WORDS_EN if lang == "en" else EDGE_WORDS


# ---------------------------------------------------------------- 禁止词
# 「不像营销」的机检部分。见 site-spec/09 §8。
# 一级：营销专属词，无条件禁。
BANNED = ["极致", "领先", "革命性", "颠覆", "神器", "必装",
          "一键搞定", "全网最强", "你的数据正在被偷",
          "无懈可击", "业界第一", "顶级", "震撼", "秒杀", "唯一选择"]

# 二级：技术语境里也常用（「绝对路径」「不是 100% 保证」），只在肯定语境算营销。
# 判据会往前看一小段上下文，出现「不／非／没／无／别」就放过——那是引述或否定。
BANNED_SOFT = ["绝对", "100%", "零风险", "包治"]

# ---------------------------------------------------------------- 用词统一
# 一件事一个词。左边是不要用的，右边是统一用的。
WORDS = [
    ("扫描", "检查"),
    ("盘查", "检查"),
    ("留痕", "记录"),
    ("记账", "记录"),
    ("判定", "判断"),
    ("您", "你"),
    ("用户", "你"),
]

# 人读页清单：这些页按「给不搞技术的人看」的标准写，也受 J-24～J-28 约束。
# /audit/、/brand/、/facts/、/rules/*、/docs/agent/ 不在内：那几页的读者是要验的人。
# 英文镜像同题同标准——/en/ 下的同一批页一并进清单。
# 为什么必须进：镜像页最容易烂，因为「那是翻译，差不多就行」。
# 不进清单，J-24～J-30 就只管中文站，英文页堆术语、写营销词、缺边界段全放过。
HUMAN_PAGES = ["/", "/why/", "/sample/", "/steward/", "/gates/", "/monitor/",
               "/checkup/", "/threat-model/", "/completeness/", "/compare/",
               "/license/", "/faq/", "/changelog/",
               "/en/", "/en/why/", "/en/sample/", "/en/steward/", "/en/gates/",
               "/en/monitor/", "/en/checkup/", "/en/threat-model/",
               "/en/completeness/", "/en/compare/", "/en/license/", "/en/faq/",
               "/en/changelog/"]

# 人读页必须出现的「边界」段：h2 命中任一关键词即算。
# 这张表是词面清单，不是语义判断——所以宁可多收几种写法，也别让一条真的边界段
# 因为换个说法就被判成缺失。新增页面换了说法，就往这里加一条。
EDGE_WORDS = ("做不到", "边界", "拦不住", "不拦", "不做什么", "不回答",
              "不自称", "不等于", "不适用", "不适合", "不能当", "先不用")


def v(key, field, lang="zh"):
    """取六档人话文案。缺 key 直接报错，不给默认值（默认值会让漏写静默通过）。"""
    d = (VERDICTS_HUMAN_EN if lang == "en" else VERDICTS_HUMAN)[key]
    return d[field]


def vwhy(lang="zh"):
    return VERDICT_WHY_EN if lang == "en" else VERDICT_WHY


def explain(term):
    """术语的首次出现解释。没有登记的术语直接报错，逼着补表。"""
    if term not in TERMS:
        raise KeyError("术语表里没有「%s」——先补 lib/human.py 的 TERMS" % term)
    return TERMS[term]
