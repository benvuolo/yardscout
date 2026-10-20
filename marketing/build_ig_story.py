#!/usr/bin/env python3
"""Build the YardScout Instagram Story promo (1080x1920)."""
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/benjamin.vuolo/PODIUM_SETUP/admin/junkyard-hunter"
OUT = f"{ROOT}/marketing/ig_story.png"

W, H = 1080, 1920
BG = (26, 24, 21)
CREAM = (250, 248, 242)
DIM = (168, 159, 138)
ORANGE = (210, 92, 28)

MENLO = "/System/Library/Fonts/Menlo.ttc"
font_word = ImageFont.truetype(MENLO, 76, index=1)   # Bold wordmark
font_tag = ImageFont.truetype(MENLO, 36, index=0)    # Regular tagline
font_foot = ImageFont.truetype(MENLO, 30, index=0)   # Footer

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


def draw_letterspaced(d, cx, y, text, font, fill, tracking):
    """Draw text centered at cx with extra tracking between chars; returns width."""
    widths = []
    for ch in text:
        bbox = font.getbbox(ch)
        widths.append(d.textlength(ch, font=font))
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


# ---------- Lockup: icon + wordmark ----------
LOCKUP_CY = 265  # vertical center of the icon/wordmark row (safe: below 150px)
icon = Image.open(f"{ROOT}/assets/icon-only.png").convert("RGBA")
ICON_H = 110
icon = icon.resize((ICON_H, ICON_H), Image.LANCZOS)

WORD = "YARDSCOUT"
TRACK = 18
word_w = sum(draw.textlength(c, font=font_word) for c in WORD) + TRACK * (len(WORD) - 1)
GAP = 44
total_w = ICON_H + GAP + word_w
lx = (W - total_w) / 2

img.paste(icon, (int(lx), int(LOCKUP_CY - ICON_H / 2)), icon)

# vertically center wordmark on cap height
asc, desc = font_word.getmetrics()
cap_bbox = font_word.getbbox("Y")
cap_h = cap_bbox[3] - cap_bbox[1]
word_y = LOCKUP_CY - cap_h / 2 - cap_bbox[1]
x = lx + ICON_H + GAP
for ch in WORD:
    draw.text((x, word_y), ch, font=font_word, fill=CREAM)
    x += draw.textlength(ch, font=font_word) + TRACK

# ---------- Dashed orange rule ----------
RULE_Y = 392
DASH_W, DASH_H, DASH_GAP = 22, 6, 12
RULE_TOTAL = 560
n = int((RULE_TOTAL + DASH_GAP) // (DASH_W + DASH_GAP))
rule_w = n * DASH_W + (n - 1) * DASH_GAP
rx = (W - rule_w) / 2
for i in range(n):
    x0 = rx + i * (DASH_W + DASH_GAP)
    draw.rectangle([x0, RULE_Y, x0 + DASH_W, RULE_Y + DASH_H], fill=ORANGE)

# ---------- Tagline ----------
TAG = "Every self-serve junkyard. One search."
tag_w = draw.textlength(TAG, font=font_tag)
draw.text(((W - tag_w) / 2, 448), TAG, font=font_tag, fill=CREAM)

# ---------- Phone mockup ----------
shot = Image.open(f"{ROOT}/marketing/pro_capture.png").convert("RGB")
PH_H = 1050                                  # ~55% of canvas height
PH_W = round(PH_H * shot.width / shot.height)
shot = shot.resize((PH_W, PH_H), Image.LANCZOS)

RAD = 46
SS = 4  # supersample mask for smooth corners
mask = Image.new("L", (PH_W * SS, PH_H * SS), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, PH_W * SS - 1, PH_H * SS - 1],
                                       radius=RAD * SS, fill=255)
mask = mask.resize((PH_W, PH_H), Image.LANCZOS)

# bezel: slightly larger dark rounded rect with a subtle outline
BEZ = 14
bz_w, bz_h = PH_W + 2 * BEZ, PH_H + 2 * BEZ
bz_rad = RAD + BEZ
bezel_mask = Image.new("L", (bz_w * SS, bz_h * SS), 0)
ImageDraw.Draw(bezel_mask).rounded_rectangle([0, 0, bz_w * SS - 1, bz_h * SS - 1],
                                             radius=bz_rad * SS, fill=255)
bezel_mask = bezel_mask.resize((bz_w, bz_h), Image.LANCZOS)
bezel = Image.new("RGB", (bz_w, bz_h), (12, 11, 10))

# phone placement: centered slightly below vertical middle
phone_cx = W // 2
phone_top = 544                               # bezel top
bx = phone_cx - bz_w // 2

# soft drop glow behind the phone so it separates from the bg
glow = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(glow)
gd.rounded_rectangle([bx - 10, phone_top - 10, bx + bz_w + 10, phone_top + bz_h + 10],
                     radius=bz_rad + 10, fill=38)
from PIL import ImageFilter
glow = glow.filter(ImageFilter.GaussianBlur(28))
glow_layer = Image.new("RGB", (W, H), (0, 0, 0))
img = Image.composite(glow_layer, img, glow)
draw = ImageDraw.Draw(img)

img.paste(bezel, (bx, phone_top), bezel_mask)
# subtle outline on the bezel edge
outline = Image.new("RGBA", (bz_w, bz_h), (0, 0, 0, 0))
ImageDraw.Draw(outline).rounded_rectangle([1, 1, bz_w - 2, bz_h - 2],
                                          radius=bz_rad, outline=(72, 66, 58, 255), width=2)
img.paste(outline, (bx, phone_top), outline)

img.paste(shot, (bx + BEZ, phone_top + BEZ), mask)

# ---------- Footer ----------
draw = ImageDraw.Draw(img)
FOOT = "free · no account · yardscout.io"
foot_w = draw.textlength(FOOT, font=font_foot)
foot_y = phone_top + bz_h + 40               # just under the phone; ends well above bottom 250px
draw.text(((W - foot_w) / 2, foot_y), FOOT, font=font_foot, fill=DIM)

img.save(OUT)
print(f"saved {OUT}  phone bottom={phone_top + bz_h}  footer y={foot_y}")
