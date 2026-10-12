#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成「扫码点 Star」分享素材（离线可用，只需 segno + Pillow）

产出：
    repo-qr.png       纯二维码（可直接贴到任何地方）
    share-card-qr.png 带引导说明的分享卡（1080 宽，适合微信发送）

用法：
    python make_share_qr.py
"""

import os

import segno
from PIL import Image, ImageDraw, ImageFont

REPO_URL = "https://github.com/guomming/mcd-decision"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 主题色
INK = (32, 33, 36)          # 正文深灰
SUB = (110, 115, 125)       # 次要灰
RED = (218, 41, 28)         # 麦当劳红
GOLD = (255, 188, 13)       # 麦当劳黄
CARD = (255, 255, 255)
BG = (247, 248, 250)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]
FONT_REG_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def load_font(size, bold=False):
    for p in (FONT_CANDIDATES if bold else FONT_REG_CANDIDATES):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def measure(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def line_height(font):
    """中文实际行高约 1.33 倍字号"""
    return int(font.size * 1.35)


def text_center(draw, y, text, font, color, width):
    w, _ = measure(draw, text, font)
    draw.text(((width - w) // 2, y), text, font=font, fill=color)
    return y + line_height(font)


# ---------- 1. 纯二维码 ----------
qr = segno.make(REPO_URL, error="h")
plain_path = os.path.join(OUT_DIR, "repo-qr.png")
# scale=10: 原生尺寸直接嵌入卡片，避免非整数倍缩放损伤模块（影响扫码成功率）
qr.save(plain_path, scale=10, border=3, dark="#201F22", light="#FFFFFF")
print(f"  已生成 {plain_path}")


# ---------- 2. 分享卡 ----------
W = 1080
PAD = 64
CARD_W = W - PAD * 2

qr_img = Image.open(plain_path).convert("RGB")
qr_size = qr_img.width  # 使用原生尺寸，不做缩放

# 先算高度
f_tag = load_font(30)
f_title = load_font(72, bold=True)
f_body = load_font(34)
f_step = load_font(34)
f_url = load_font(30)
f_tip = load_font(28)

tmp = Image.new("RGB", (10, 10))
d = ImageDraw.Draw(tmp)

inner_pad = 56
y = PAD + 72
y += line_height(f_tag) + 8                       # tag
y += line_height(f_title) + 30                    # title
y += qr_size + 36                                 # qr
y += line_height(f_body) + 28                     # subtitle
y += line_height(f_step) * 3                      # 3 steps
y += 24
y += line_height(f_url) + 30                      # url
y += line_height(f_tip) + 8                       # tip
H = y + inner_pad

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# 白卡片
draw.rounded_rectangle([PAD, PAD, W - PAD, H - PAD], radius=36, fill=CARD)

cx = W // 2
inner_x = PAD + inner_pad
y = PAD + 72

# 顶部标签
tag = "麦当劳 × WorkBuddy 创意开发大赛 · 参赛作品"
tw, _ = measure(draw, tag, f_tag)
draw.rounded_rectangle(
    [cx - tw // 2 - 26, y - 10, cx + tw // 2 + 26, y + line_height(f_tag) - 2],
    radius=22, fill=(255, 244, 226),
)
draw.text((cx - tw // 2, y), tag, font=f_tag, fill=(180, 120, 20))
y += line_height(f_tag) + 8

# 主标题
y = text_center(draw, y, "帮忙点个 Star", f_title, INK, W)
y += 30

# 二维码
img.paste(qr_img, (cx - qr_size // 2, y))
draw.rounded_rectangle(
    [cx - qr_size // 2 - 14, y - 14, cx + qr_size // 2 + 14, y + qr_size + 14],
    radius=20, outline=(226, 228, 232), width=3,
)
y += qr_size + 36

# 副标题
y = text_center(draw, y, "微信扫一下，或手机相机扫一扫", f_body, SUB, W)
y += 28

# 三步
steps = [
    "① 打开后，点右上角那颗 ★ 星星图标",
    "② 没登录会跳登录页，登一下 GitHub",
    "③ 变实心就成功了，10 秒搞定",
]
for s in steps:
    sw, _ = measure(draw, s, f_step)
    draw.text((cx - sw // 2, y), s, font=f_step, fill=INK)
    y += line_height(f_step)
y += 24

# 地址
y = text_center(draw, y, REPO_URL, f_url, (37, 99, 235), W)
y += 30

# 底部提示
y = text_center(draw, y, "打不开就多刷一次，或换手机流量试试", f_tip, SUB, W)

card_path = os.path.join(OUT_DIR, "share-card-qr.png")
img.save(card_path)
print(f"  已生成 {card_path}  ({W}×{H})")
