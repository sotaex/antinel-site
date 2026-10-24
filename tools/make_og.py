# -*- coding: utf-8 -*-
"""一次性生成社交分享预览图 assets/og-cover.png（1200x630）。

**这个脚本不是构建链的一环**：gen.py 只把 assets/ 下的文件原样复制进产物，
PNG 是提交进仓的静态资产。构建器纯标准库，CI 没有 Pillow，也不该有。

用法（需要 Pillow，与站点构建无关）：
    python tools/make_og.py

已知局限（诚实登记）：
  图里的数字（37 条规则／24 类宿主）是**写死在图上的**，不在 J-06/J-17 的
  扫描范围内（它们扫的是 HTML 文本，不是图片像素）。改了 facts 必须重跑
  本脚本，否则图会和页面对不上——而没有任何判据会红。
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "og-cover.png")

W, H = 1200, 630
# 色值取自 assets/site.css 的浅色主题，保证预览图和站点同色。
PAPER = "#fbfbfa"
INK = "#10151c"
INK2 = "#3d4753"
INK3 = "#5f6a78"
ACCENT = "#0d5c63"
ACCENT_SOFT = "#e8f1f0"

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"


def fit(draw, text, path, size, max_w, min_size=20):
    """字号从 size 往下缩，直到文字装进 max_w。返回 (font, w, h)。"""
    while size > min_size:
        f = ImageFont.truetype(path, size)
        w = draw.textlength(text, font=f)
        if w <= max_w:
            return f, w, size
        size -= 2
    return ImageFont.truetype(path, min_size), draw.textlength(text, font=f), min_size


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # 右侧盾牌：软件里「拦一下」的那个动作，用最简形状表达。
    cx, top, hw, hh = 950, 170, 175, 300
    d.polygon([(cx - hw, top), (cx + hw, top), (cx + hw, top + hh * 0.45),
               (cx, top + hh), (cx - hw, top + hh * 0.45)],
              fill=ACCENT_SOFT, outline=ACCENT, width=10)
    d.line([(cx - 70, top + hh * 0.42), (cx - 20, top + hh * 0.60),
            (cx + 80, top + hh * 0.20)], fill=ACCENT, width=20, joint="curve")

    x = 90
    max_w = 660  # 文字块不侵入盾牌区

    f, w, _ = fit(d, "Antinel 监理", FONT_BOLD, 104, max_w)
    d.text((x, 105), "Antinel 监理", font=f, fill=INK)

    d.rectangle([x, 250, x + 120, 258], fill=ACCENT)

    f1, _, _ = fit(d, "AI 工具在你机器上做的一切，", FONT_REG, 44, max_w)
    d.text((x, 300), "AI 工具在你机器上做的一切，", font=f1, fill=INK2)
    f2, _, _ = fit(d, "独立第三方监理，逐个有据可查", FONT_REG, 44, max_w)
    d.text((x, 362), "独立第三方监理，逐个有据可查", font=f2, fill=INK2)

    f3, _, _ = fit(d, "37 条护盾规则 · 24 类宿主登记 · 数字可复算",
                   FONT_REG, 36, max_w)
    d.text((x, 452), "37 条护盾规则 · 24 类宿主登记 · 数字可复算",
           font=f3, fill=INK3)

    f4, _, _ = fit(d, "sotaex.github.io/antinel-site", FONT_REG, 32, max_w)
    d.text((x, 536), "sotaex.github.io/antinel-site", font=f4, fill=ACCENT)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("写出 %s（%d 字节）" % (OUT, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()
