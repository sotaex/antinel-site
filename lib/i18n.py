# -*- coding: utf-8 -*-
"""外壳文案的中英两份：导航、页脚、引用块、语言切换。

为什么单独立文件：这些东西不属于「内容」，属于「外壳」。内容在
content/*.md 与生成器里，外壳在这里。改导航不用翻内容文件。

一条纪律：中文是主站，英文是镜像。镜像不等于逐字翻译——英文按
ASD-STE100 重写，同一件事一个叫法，但**数字、编号、命令、字段名
与中文站完全一致**（J-16 的跨语言一致性就查这个）。
"""

ZH = "zh-CN"
EN = "en"

SHELL = {
    ZH: {
        "brand_sub": "监理",
        "nav_label": "主导航",
        "nav_open": "打开导航",
        "nav": [
            ("/why/", "这事跟我有关吗"),
            ("/steward/", "它是什么"),
            ("/cost/", "要花多少"),
            ("/help/", "怎么开始"),
            ("/facts/", "证据"),
        ],
        "skip": "跳到正文",
        "footer_links": [
            ("/help/", "从哪开始"),
            ("/answers/", "客户会问你的五个问题"),
            ("/who/", "谁在做"),
            ("/cost/", "免费与付费"),
            ("/sample/", "一页纸样例"),
            ("/docs/", "文档"),
            ("/datasets/", "数据集"),
            ("/changelog/", "变更日志"),
            ("/license/", "许可与中立"),
            ("/brand/", "品牌与用词"),
            ("mailto:contact@antinel.com", "contact@antinel.com"),
        ],
        "llms_label": "llms.txt",
        "cite_head": "引用本页",
        "cite_body": "Antinel 监理项目组.《%s》. %s, 产品版本 %s, 数据日期 %s. %s.",
        "cite_key": "命名空间公钥指纹：%s（与 GitHub README 钉定一致）。",
        "langswitch": "English",
        "langswitch_href": "/en/",
        "og_site": "Antinel 监理",
        "site_name": "Antinel 监理",
    },
    EN: {
        "brand_sub": "Steward",
        "nav_label": "Main navigation",
        "nav_open": "Open navigation",
        "nav": [
            ("/en/why/", "Is this about me?"),
            ("/en/steward/", "What it is"),
            ("/en/cost/", "What it costs"),
            ("/en/help/", "How to start"),
            ("/en/facts/", "Evidence"),
        ],
        "skip": "Skip to content",
        "footer_links": [
            ("/en/help/", "Where to start"),
            ("/en/answers/", "Five questions your customer will ask"),
            ("/en/who/", "Who runs this"),
            ("/en/cost/", "Free and paid"),
            ("/en/sample/", "Sample report"),
            ("/en/docs/", "Docs"),
            ("/en/datasets/", "Datasets"),
            ("/en/changelog/", "Changelog"),
            ("/en/license/", "License"),
            ("/en/brand/", "Brand"),
            ("mailto:contact@antinel.com", "contact@antinel.com"),
        ],
        "llms_label": "llms-en.txt",
        "cite_head": "Cite this page",
        "cite_body": "Antinel Steward Project. \"%s\". %s, product version %s, "
                     "data date %s. %s.",
        "cite_key": "Namespace public key fingerprint: %s (pinned to the GitHub README).",
        "langswitch": "中文",
        "langswitch_href": "/",
        "og_site": "Antinel Steward",
        "site_name": "Antinel Steward",
    },
}


def shell(lang):
    return SHELL[EN if lang == EN else ZH]
