# -*- coding: utf-8 -*-
"""生成朋友圈宣传海报（竖版 1080x1500），仅依赖 Pillow + 系统中文字体。"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1500
OUT = "wechat-poster.png"

F_REG = "C:/Windows/Fonts/msyh.ttc"
F_BOLD = "C:/Windows/Fonts/msyhbd.ttc"


def f(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    """按像素宽度折行，返回行列表。"""
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if draw.textlength(t, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def center(draw, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


img = Image.new("RGB", (W, H), "#FFFFFF")
d = ImageDraw.Draw(img)

# ---------- 顶部标签 ----------
d.rounded_rectangle([80, 62, 1000, 126], radius=32, fill="#FFF1F0")
center(d, 78, "麦当劳 × WorkBuddy 创意开发大赛 · 参赛作品", f(F_REG, 34), "#C0392B")

# ---------- 主标题 ----------
center(d, 190, "今天吃啥？", f(F_BOLD, 120), "#1A1A1A")
center(d, 366, "把「选择困难症」变成一次有理由的决定", f(F_REG, 42), "#5B6472")

# ---------- 三张人格卡片 ----------
CARDS = [
    ("#2563EB", "#EFF4FF", "看心情",
     "不知道吃啥就交给它：按心情加权随机，并告诉你为什么是它"),
    ("#16A34A", "#EDFAF1", "薅一把",
     "预算 30 块也能吃好：挑预算内折扣率最高的，省钱明细算给你看"),
    ("#F59E0B", "#FFF6E6", "宠自己",
     "今天想犒劳自己：按口味偏好排序，价格先放一边"),
]

x, top, ch, gap = 80, 462, 212, 26
for i, (accent, bg, title, desc) in enumerate(CARDS):
    y = top + i * (ch + gap)
    d.rounded_rectangle([x, y, x + 920, y + ch], radius=28, fill=bg)
    d.rounded_rectangle([x, y + 26, x + 10, y + ch - 26], radius=5, fill=accent)
    d.text((x + 48, y + 34), title, font=f(F_BOLD, 54), fill=accent)
    for j, line in enumerate(wrap(d, desc, f(F_REG, 34), 790)):
        d.text((x + 48, y + 114 + j * 50), line, font=f(F_REG, 34), fill="#4B5563")

# ---------- 真实数据卡 ----------
dy = top + 3 * (ch + gap) + 16
d.rounded_rectangle([80, dy, 1000, dy + 130], radius=28, fill="#F4F5F7")
d.text((116, dy + 26), "真实数据 · 东莞石龙门店实测", font=f(F_BOLD, 32), fill="#1A1A1A")
d.text((116, dy + 78), "预算 30 元 → 大堡口福三件套 ¥22.9（省 ¥24.6）",
       font=f(F_REG, 30), fill="#4B5563")

# ---------- 底部引导 ----------
by = dy + 130 + 56
center(d, by, "github.com/guomming/mcd-decision", f(F_BOLD, 38), "#1A1A1A")
center(d, by + 58, "打开链接 → 点右上角星星图标", f(F_REG, 30), "#8A93A0")

img.save(OUT, "PNG")
print("saved:", OUT, img.size)
