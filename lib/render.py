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


def cite_block(title, path, updated, version, lang="zh-CN"):
    """页脚引用块：五要素齐全（J-12）。中英两份外壳文案在 lib/i18n.py。"""
    from . import i18n
    s = i18n.shell(lang)
    url = C.abs_url(path)
    return (
        '<div class="cite">\n'
        '  <p class="cite-head">%s</p>\n'
        '  <p>%s</p>\n'
        '  <p>%s</p>\n'
        '</div>' % (esc(s["cite_head"]),
                    esc(s["cite_body"] % (title, url, version, updated, C.LICENSE_TEXT)),
                    esc(s["cite_key"] % C.FINGERPRINT)))


def jsonld(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def ld_software(version, desc):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Antinel 监理 (AgentState by Antinel)",
        "applicationCategory": "SecurityApplication",
        "operatingSystem": "Windows",   # 第一版只验证了 Windows；别写没测过的平台
        "softwareVersion": version,
        "description": desc,
        "license": "https://opensource.org/licenses/Apache-2.0",
        "codeRepository": "https://github.com/sotaex/agentstate",
        "inLanguage": ["zh-CN"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "CNY"},
    })


def ld_article(headline, path, updated, about, lang="zh-CN"):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": headline,
        "dateModified": updated,
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "about": about,
        "url": C.abs_url(path),
        "inLanguage": lang,
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


def ld_webpage(path, title, desc, lang="zh-CN"):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": C.abs_url(path),
        "inLanguage": lang,
        "isPartOf": {"@type": "WebSite", "name": "Antinel 监理", "url": C.abs_url("/")},
    })


def page(*, path, title, description, content, updated, version,
         jsonld_obj, lang="zh-CN", cite_title=None, alt=None):
    """组装整页 HTML。path 形如 /facts/ 或 /。

    alt：另一语言的同题页地址，形如 {"zh-CN": "/", "en": "/en/"}。
    给了就出 hreflang 双向链接（J-16 的机器可读部分）。
    """
    from . import i18n
    base = C.BASE_PATH
    md_url = C.abs_url(path.rstrip("/") + "/index.md") if path != "/" else C.abs_url("/index.md")
    s = i18n.shell(lang)
    nav = "\n".join('      <a href="%s%s">%s</a>' % (base, esc(href), esc(label))
                    for href, label in s["nav"])
    foot = " · ".join('<a href="%s%s">%s</a>' % (base, esc(href), esc(label))
                      for href, label in s["footer_links"])
    llms_url = C.abs_url("/llms-en.txt") if lang == i18n.EN else C.abs_url("/llms.txt")
    alt = alt or {}
    links = []
    for code, key in (("zh-CN", "zh-CN"), ("en", "en")):
        if code != lang and alt.get(key):
            links.append('<link rel="alternate" hreflang="%s" href="%s">'
                         % (code, C.abs_url(alt[key])))
    mapping = {
        "lang": lang,
        "title": esc(title),
        "description": esc(description),
        "canonical": C.abs_url(path),
        "hreflang": "\n".join(links),
        "md_url": md_url,
        "llms_url": llms_url,
        "jsonld": jsonld_obj,
        "css": (base or "") + "/assets/site.css",
        "base": base,
        "content": content,
        "cite": cite_block(cite_title or title, path, updated, version, lang),
        "og_site": esc(s["og_site"]),
        "skip": esc(s["skip"]),
        "home": "/en/" if lang == i18n.EN else "/",
        "brand_sub": esc(s["brand_sub"]),
        "nav": nav,
        "nav_label": esc(s["nav_label"]),
        "nav_open": esc(s["nav_open"]),
        # 语言切换：一个胶囊，指向另一语言的同题页。
        # /en/ 镜像已由 J-16 保证与中文页一一对应，所以这个链接不会是死链。
        # 镜像没做完之前不要放开这一行——那会给出 64 个指向 404 的入口。
        "langswitch": esc(s["langswitch"]),
        "langswitch_href": s["langswitch_href"],
        "langswitch_lang": i18n.ZH if lang == i18n.EN else i18n.EN,
        "footer_links": foot + ' · <a href="%s">%s</a>' % (llms_url, esc(s["llms_label"])),
    }
    return fill(_tpl("base.html"), mapping)
