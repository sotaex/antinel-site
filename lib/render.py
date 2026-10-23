# -*- coding: utf-8 -*-
"""页面外壳渲染：head 契约、页头、页脚引用块、JSON-LD。

模板占位用 {{key}}，只替换映射里存在的 key —— 正文里没被消费掉的
{{facts.…}} 不会被误替换，而是留到校验阶段报错。
"""
import json
import os
import re

from . import config as C

RE_TOKEN = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")


def fill(tpl, mapping):
    def rep(m):
        k = m.group(1)
        return str(mapping[k]) if k in mapping else m.group(0)
    return RE_TOKEN.sub(rep, tpl)


def _tpl(name):
    with open(os.path.join(C.DIR_TEMPLATES, name), encoding="utf-8") as f:
        return f.read()


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def trim(s, n=118):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def cite_block(title, path, updated, version):
    """页脚引用块：五要素齐全（J-12）。"""
    url = C.abs_url(path)
    return (
        '<div class="cite">\n'
        '  <p class="cite-head">引用本页</p>\n'
        '  <p>Antinel 监理项目组.《%s》. %s, 产品版本 %s, 数据日期 %s. %s.</p>\n'
        '  <p>命名空间公钥指纹：%s（与 GitHub README 钉定一致）。</p>\n'
        '</div>' % (esc(title), url, version, updated, C.LICENSE_TEXT, C.FINGERPRINT))


def jsonld(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def ld_software(version, desc):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Antinel 监理 (AgentState by Antinel)",
        "applicationCategory": "SecurityApplication",
        "operatingSystem": "Windows, macOS, Linux",
        "softwareVersion": version,
        "description": desc,
        "license": "https://opensource.org/licenses/Apache-2.0",
        "codeRepository": "https://github.com/sotaex/agentstate",
        "inLanguage": ["zh-CN"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "CNY"},
    })


def ld_article(headline, path, updated, about):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "dateModified": updated,
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "about": about,
        "url": C.abs_url(path),
        "inLanguage": "zh-CN",
        "isPartOf": {"@type": "WebSite", "name": "Antinel 监理", "url": C.abs_url("/")},
    })


def ld_faq(pairs):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in pairs],
    })


def ld_dataset(name, version, path, desc):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": name,
        "version": version,
        "description": desc,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "url": C.abs_url(path),
        "creator": {"@type": "Organization", "name": "Antinel 监理项目组"},
    })


def ld_webpage(path, title, desc):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": C.abs_url(path),
        "inLanguage": "zh-CN",
        "isPartOf": {"@type": "WebSite", "name": "Antinel 监理", "url": C.abs_url("/")},
    })


def page(*, path, title, description, content, updated, version,
         jsonld_obj, lang="zh-CN", cite_title=None):
    """组装整页 HTML。path 形如 /facts/ 或 /。"""
    base = C.BASE_PATH
    md_url = C.abs_url(path.rstrip("/") + "/index.md") if path != "/" else C.abs_url("/index.md")
    mapping = {
        "lang": lang,
        "title": esc(title),
        "description": esc(description),
        "canonical": C.abs_url(path),
        "md_url": md_url,
        "llms_url": C.abs_url("/llms.txt"),
        "jsonld": jsonld_obj,
        "css": (base or "") + "/assets/site.css",
        "base": base,
        "content": content,
        "cite": cite_block(cite_title or title, path, updated, version),
    }
    return fill(_tpl("base.html"), mapping)
