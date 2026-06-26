#!/usr/bin/env python3
"""
Generate the animated profile banner GIF.

The big "DAKSH BAGGA" name is rasterized from ANSI Shadow ASCII art using a real
monospace font (Menlo), so every block/box glyph keeps a uniform grid — something
SVG <text> can't guarantee because browsers substitute different-width fonts for
glyphs like █ ═ ║ ╗. The name is a static ember gradient; only the terminal
typewriter line (cycling the titles) animates, which keeps the GIF small.

Requires: pip install Pillow
Usage:    python scripts/generate_banner.py
Note:     GitHub's image proxy (camo) caches by URL, so to force a refresh on the
          profile, bump OUTPUT_NAME (banner-v7 -> v8 ...) and update the README <img>.
"""
import os
from PIL import Image, ImageFont, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ART_PATH = os.path.join(HERE, "name_ansi.txt")
OUTPUT_NAME = "banner-v7.gif"
OUT = os.path.join(HERE, "..", "assets", OUTPUT_NAME)

# A monospace font with uniform box-drawing/block coverage. Menlo ships with macOS.
# Override with FONT_PATH=/path/to/font.ttf if you're not on macOS.
MENLO = os.environ.get("FONT_PATH", "/System/Library/Fonts/Menlo.ttc")

# titles the terminal types out, in order
ROLES = ["10x prompt engineer", "vibe coder", "growth hacker",
         "unreasonably effective", "visionary"]

TITLE = "daksh@github: ~/profile"

# ---------------------------------------------------------------------------
with open(ART_PATH) as f:
    art = [l.rstrip("\n") for l in f.readlines()]
art = [l for l in art if l.strip() != ""]
ncols = max(len(l) for l in art)
art = [l.ljust(ncols) for l in art]

FS = 22
font = ImageFont.truetype(MENLO, FS, index=0)
subfont = ImageFont.truetype(MENLO, 26, index=0)
titlefont = ImageFont.truetype(MENLO, 15, index=0)

cw = font.getlength("A")
asc, desc = font.getmetrics()
pitch = asc + desc - 6
name_w = int(cw * ncols)
name_h = pitch * len(art)

W = 1280
TITLE_H = 46
top = TITLE_H + 46
sub_y = top + name_h + 48
H = sub_y + 70
left = (W - name_w) // 2


def ember(t):
    STOPS = [(0.00, (200, 30, 0)), (0.18, (255, 61, 0)), (0.38, (255, 122, 0)),
             (0.55, (255, 176, 0)), (0.74, (255, 122, 0)), (0.88, (255, 61, 0)),
             (1.00, (200, 30, 0))]
    t %= 1.0
    for j in range(len(STOPS) - 1):
        a, ca = STOPS[j]; b, cb = STOPS[j + 1]
        if a <= t <= b:
            f = (t - a) / (b - a) if b > a else 0
            return tuple(int(ca[k] + (cb[k] - ca[k]) * f) for k in range(3))
    return STOPS[-1][1]


# name text mask + soft glow
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
for i, line in enumerate(art):
    md.text((left, top + i * pitch), line, font=font, fill=255)
glow_mask = mask.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.55))

# static horizontal ember gradient
grad = Image.new("RGB", (W, 1))
gp = grad.load()
for x in range(W):
    gp[x, 0] = ember(x / 620.0)
grad = grad.resize((W, H))

# clean stage: flat dark bg + terminal chrome + static ember name
BG, BAR, LINE = (13, 15, 20), (24, 27, 34), (38, 42, 52)
stage = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(stage)
d.rounded_rectangle([1, 1, W - 2, H - 2], radius=18, outline=LINE, width=2)
d.rounded_rectangle([2, 2, W - 3, TITLE_H], radius=16, fill=BAR)
d.rectangle([2, TITLE_H - 16, W - 3, TITLE_H], fill=BAR)
d.line([(2, TITLE_H), (W - 3, TITLE_H)], fill=LINE, width=2)
cy = TITLE_H // 2
for cx, col in [(30, (255, 95, 86)), (56, (255, 189, 46)), (82, (40, 200, 64))]:
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=col)
d.text(((W - d.textlength(TITLE, font=titlefont)) // 2, cy - 8), TITLE,
       font=titlefont, fill=(214, 221, 230))
stage = Image.composite(Image.new("RGB", (W, H), (255, 90, 0)), stage, glow_mask)
stage = Image.composite(grad, stage, mask)

# typewriter timeline (uniform frames -> smooth cursor blink, small file)
FRAME_MS = 70
BLINK = 7
timeline = []  # (text, cursor_on)
for role in ROLES:
    for k in range(1, len(role) + 1):
        timeline.append((role[:k], True))
    for h in range(16):
        timeline.append((role, (h // BLINK) % 2 == 0))
    k = len(role)
    while k > 0:
        k = max(0, k - 2)
        timeline.append((role[:k], True))
    for h in range(7):
        timeline.append(("", (h // BLINK) % 2 == 0))


def render_frame(text, cursor_on):
    img = stage.copy()  # static name; only the typing strip changes per frame
    dd = ImageDraw.Draw(img)
    pre = "> "
    body = pre + text
    total = dd.textlength(body, font=subfont) + (15 if cursor_on else 0)
    sx = int((W - total) // 2)
    dd.text((sx, sub_y), pre, font=subfont, fill=(255, 150, 30))
    dd.text((sx + dd.textlength(pre, font=subfont), sub_y), text, font=subfont,
            fill=(255, 240, 224))
    if cursor_on:
        curx = sx + dd.textlength(body + " ", font=subfont)
        dd.rectangle([curx, sub_y + 3, curx + 13, sub_y + 27], fill=(255, 150, 30))
    return img.convert("P", palette=Image.ADAPTIVE, colors=80)


frames = [render_frame(t, c) for (t, c) in timeline]
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=FRAME_MS,
               loop=0, disposal=1, optimize=True)
print(f"{W}x{H}, {len(frames)} frames, {os.path.getsize(OUT) // 1024} KB -> {OUT}")
