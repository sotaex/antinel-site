# -*- coding: utf-8 -*-
"""手机端实测：拿真浏览器量，不靠读 CSS 猜。

查三件事：
  M-01 每页在 390px 宽下没有横向溢出（scrollWidth 不超过 innerWidth）
  M-02 每页正文首屏能看到正文，不是被标题占满（h1 高度不超过视口 40%）
  M-03 可点元素不小于 40px（按钮、导航项）

用法：
    python tests/mobile_check.py            # 全部页面
    python tests/mobile_check.py / /why/    # 只看几页

需要 playwright（装在 envs/default 里）。跑不出来会明说 BLOCKED，不记成 FAIL。
"""
import http.server
import os
import re
import socketserver
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("SITE_OUT") or os.path.join(ROOT, "site-output")
SHOT = os.path.join(ROOT, "tests", "_shots")

VIEW = {"width": 390, "height": 844}          # iPhone 14 / 15 的逻辑像素
MIN_TAP = 40


def serve():
    os.chdir(OUT)

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(("127.0.0.1", 0), Q)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def pages_from_sitemap():
    p = os.path.join(OUT, "sitemap.xml")
    xml = open(p, encoding="utf-8").read()
    locs = re.findall(r"<loc>(.*?)</loc>", xml)
    out = []
    for u in locs:
        m = re.search(r"(?:https?://[^/]+)?(/.*)$", u)
        out.append(m.group(1) if m else u)
    return out


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("BLOCKED：没有 playwright（%s）。这不是产品缺陷。" % type(e).__name__)
        return 2
    if not os.path.isdir(OUT):
        print("BLOCKED：没有构建产物 %s。先跑 gen.py。" % OUT)
        return 2

    want = [a for a in argv if a.startswith("/")]
    httpd, port = serve()
    base = "http://127.0.0.1:%d" % port
    paths = want or pages_from_sitemap()
    os.makedirs(SHOT, exist_ok=True)

    overflow, tall, small, nostyle = [], [], [], []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport=VIEW, device_scale_factor=2, is_mobile=True,
                        has_touch=True)
        for path in paths:
            pg.goto(base + path, wait_until="load")
            # M-00 样式表真的生效。CSS 404 时页面「看起来能用」，只是没样式——
            # 这种状态下量出来的溢出、点击区全是假绿。先验量具，再量产品。
            nrules = pg.evaluate(
                "() => { let n = 0;"
                " for (const s of document.styleSheets) {"
                "   try { n += s.cssRules.length } catch (e) {} } return n; }")
            if nrules == 0:
                nostyle.append(path)
            # 拿设定宽度比，不拿 innerWidth —— 内容撑宽时 innerWidth 会跟着变大，
            # 两边一起变，溢出就检不出来（这是第一版的假阴性）。
            w = pg.evaluate("() => document.documentElement.scrollWidth")
            if w > VIEW["width"] + 1:
                overflow.append("%s（%d>%d）" % (path, w, VIEW["width"]))
            h1 = pg.evaluate(
                "() => { const h = document.querySelector('main h1');"
                " return h ? h.getBoundingClientRect().height : 0; }")
            if h1 > VIEW["height"] * 0.40:
                tall.append("%s（%dpx）" % (path, int(h1)))
            tiny = pg.evaluate(
                "() => [...document.querySelectorAll('a.btn, .mainnav a, .navbtn')]"
                ".filter(e => { const r = e.getBoundingClientRect();"
                " return r.width > 0 && (r.height < %d); })"
                ".map(e => (e.textContent || '').trim().slice(0, 12))" % MIN_TAP)
            if tiny:
                small.append("%s（%s）" % (path, "、".join(tiny[:3])))

        for path, name in (("/", "home"), ("/why/", "why"), ("/sample/", "sample")):
            pg.goto(base + path, wait_until="load")
            pg.screenshot(path=os.path.join(SHOT, "m-%s.png" % name), full_page=True)
        b.close()
    httpd.shutdown()

    print("手机实测（390×844，共 %d 页）" % len(paths))
    print("  %s M-00 样式表未生效 %d%s" % ("✓" if not nostyle else "✗", len(nostyle),
                                        ("：" + "、".join(nostyle[:3])) if nostyle else ""))
    print("  %s M-01 横向溢出 %d%s" % ("✓" if not overflow else "✗", len(overflow),
                                     ("：" + "、".join(overflow[:5])) if overflow else ""))
    print("  %s M-02 首屏标题过高 %d%s" % ("✓" if not tall else "✗", len(tall),
                                        ("：" + "、".join(tall[:5])) if tall else ""))
    print("  %s M-03 点击区过小 %d%s" % ("✓" if not small else "✗", len(small),
                                       ("：" + "、".join(small[:5])) if small else ""))
    print("截图在 %s" % SHOT)
    return 0 if not (nostyle or overflow or tall or small) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
