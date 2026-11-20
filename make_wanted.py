#!/usr/bin/env python3
"""Render wanted.png: a Leonida bounty poster for Grand Theft Auto VI.

Entry 4 of make.fun's gta6-meme-x-01. The joke is a legal frame for the wait:
the game is wanted for "grand theft: 13 years of my life", last seen on CCTV in
2013, and the reward is "$500 for its release" (jail release and release date),
posted by the AI agent with its make.fun bounty winnings.
"""

import hashlib
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from make_payslip import (
    rgb, mix, place_text, text_piece, fit_font, rounded_rect,
    W, H, GHOST_PATH, FONT_BLACK, FONT_BOLD, FONT_SEMI,
    INK, MUTED,
)
from make_impound2 import build_seal

HERE = os.path.dirname(os.path.abspath(__file__))
WORDMARK_PATH = os.path.join(HERE, "assets", "wordmark.png")
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

PAPER = "#E8D9B6"
PAPER_EDGE = "#D3BF92"
WALL = "#241B12"
BRAND = "#C01080"
BROWN = "#5B4A32"

SHEET = (56, 36, 1024, 1044)
INNER = (78, 58, 1002, 1022)


def paper_sheet():
    """Cream poster paper: grain, faint foxing, darkened edge, no flat fill."""
    rnd = random.Random(13)
    w, h = SHEET[2] - SHEET[0], SHEET[3] - SHEET[1]
    sheet = Image.new("RGB", (w, h), rgb(PAPER))
    noise = Image.effect_noise((w // 3, h // 3), 26).resize((w, h), Image.BILINEAR)
    sheet = Image.composite(Image.new("RGB", (w, h), rgb(PAPER_EDGE)), sheet,
                            noise.point(lambda v: int(v * 0.07)))
    d = ImageDraw.Draw(sheet)
    for _ in range(26):
        cx, cy = rnd.randrange(20, w - 20), rnd.randrange(20, h - 20)
        r = rnd.randrange(2, 11)
        tone = rnd.choice((PAPER_EDGE, "#C8B183", "#B7A075"))
        d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], fill=rgb(tone))
    sheet = Image.blend(sheet, Image.new("RGB", (w, h), rgb(PAPER_EDGE)), 0.045)
    # Vignette so the sheet reads as printed paper, not a flat block.
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-w * 0.22, -h * 0.22, w * 1.22, h * 1.22], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(60)).point(lambda v: 255 - int((255 - v) * 0.7))
    sheet = Image.composite(sheet, Image.new("RGB", (w, h), rgb(PAPER_EDGE)), vig)
    return sheet


def case_layer():
    """The suspect: a game case with a Vice City sunset cover and a magenta VI."""
    ss = 3
    cw, ch = 180 * ss, 250 * ss
    case = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(case, "RGBA")
    rounded_rect(d, (0, 0, cw - 1, ch - 1), 10 * ss, rgb("#0B0B0D") + (255,))
    d.rectangle([3 * ss, 3 * ss, cw - 3 * ss, ch - 3 * ss],
                outline=rgb("#3A3A44") + (255,), width=ss)

    # Spine and bottom edge: a few pixels of thickness so it reads as a case.
    d.rectangle([3 * ss, 3 * ss, 11 * ss, ch - 3 * ss],
                fill=rgb("#1A1A22") + (255,))
    d.line([(11 * ss, 3 * ss), (11 * ss, ch - 3 * ss)],
           fill=rgb("#4A4A56") + (255,), width=ss)
    d.rectangle([3 * ss, ch - 8 * ss, cw - 3 * ss, ch - 3 * ss],
                fill=rgb("#22222A") + (255,))

    # Cover: Vice City sunset, sun, sea, palm, then the VI band.
    top, mid1, mid2, low = "#24103C", "#7A1A5E", "#D6552E", "#F2A64E"
    cx0, cy0 = 8 * ss, 8 * ss
    cx1, horizon = cw - 8 * ss, 150 * ss
    for y in range(cy0, horizon):
        t = (y - cy0) / float(horizon - cy0)
        if t < 0.5:
            col = mix(top, mid1, t / 0.5)
        elif t < 0.8:
            col = mix(mid1, mid2, (t - 0.5) / 0.3)
        else:
            col = mix(mid2, low, (t - 0.8) / 0.2)
        d.line([(cx0, y), (cx1, y)], fill=col + (255,))
    sun_x, sun_d = cw * 0.52, 46 * ss
    d.ellipse([sun_x, horizon - sun_d - 4 * ss, sun_x + sun_d, horizon - 4 * ss],
              fill=rgb("#FFD9A0") + (232,))
    # Sea: dark band, hot horizon line, sun glitter.
    d.rectangle([cx0, horizon, cx1, horizon + 40 * ss],
                fill=rgb("#1B0F24") + (255,))
    d.rectangle([cx0, horizon, cx1, horizon + ss],
                fill=rgb("#F2A64E") + (205,))
    rnd = random.Random(7)
    for _ in range(8):
        gw = int(rnd.uniform(12, 34) * ss)
        gx = int(sun_x + sun_d / 2 - gw / 2)
        gy = horizon + int(rnd.uniform(3, 32) * ss)
        d.rectangle([gx, gy, gx + gw, gy + max(1, ss)],
                    fill=rgb("#F2A64E") + (60,))

    # Palm silhouette on the left.
    base = (62 * ss, horizon + 34 * ss)
    crown = (76 * ss, 104 * ss)
    d.line([base, crown], fill=rgb("#120A12") + (255,), width=4 * ss)
    for ang, ln in ((-166, 40), (-134, 38), (-102, 40), (-70, 36), (-38, 30)):
        a = math.radians(ang)
        tip = (crown[0] + math.cos(a) * ln * ss,
               crown[1] + math.sin(a) * ln * ss * 0.42)
        d.line([crown, tip], fill=rgb("#120A12") + (255,), width=2 * ss)

    # VI band across the lower cover: magenta field, white mark, cream caption.
    band_top = horizon + 40 * ss
    d.rectangle([cx0, band_top, cx1, ch - 8 * ss],
                fill=rgb("#C01080") + (255,))
    vi_font = ImageFont.truetype(FONT_BLACK, 58 * ss)
    viw, vih = vi_font.getsize("VI")
    d.text(((cw - viw) / 2, band_top - 2 * ss), "VI", font=vi_font,
           fill=(255, 246, 228, 255))
    tiny = ImageFont.truetype(FONT_SEMI, 13 * ss)
    cap = "GRAND THEFT AUTO"
    capw, caph = tiny.getsize(cap)
    d.text(((cw - capw) / 2, band_top + 52 * ss), cap, font=tiny,
           fill=(255, 246, 228, 235))
    return case


def cctv_panel(w, h):
    """Dark surveillance still with scanlines and a shelf line."""
    panel = Image.new("RGB", (w, h))
    top, bot = "#26332C", "#0C1210"
    d = ImageDraw.Draw(panel)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=mix(top, bot, y / float(h - 1)))
    grain = Image.effect_noise((w // 2, h // 2), 34).resize((w, h), Image.BILINEAR)
    panel = Image.blend(panel, Image.merge("RGB", (grain, grain, grain)), 0.05)
    d = ImageDraw.Draw(panel, "RGBA")
    for y in range(0, h, 4):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 34))
    # Shelf: lit lip, dark front face, faint reflection. The case stands on the lip.
    shelf_y = int(h * 0.80)
    d.rectangle([0, shelf_y, w, shelf_y + 4], fill=(214, 228, 216, 150))
    d.rectangle([0, shelf_y + 4, w, shelf_y + 22], fill=(8, 12, 10, 190))
    d.rectangle([0, shelf_y + 22, w, shelf_y + 24], fill=(214, 228, 216, 45))
    d.rectangle([0, shelf_y + 24, w, h], fill=(10, 14, 12, 60))
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).ellipse([-w * 0.12, -h * 0.12, w * 1.12, h * 1.12], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(40)).point(lambda v: 70 + int(v * 0.73))
    panel = Image.composite(panel, Image.new("RGB", (w, h), (6, 9, 8)), vig)
    return panel


def cctv_mock(w, h):
    """Assemble the photo: panel, case on the shelf, timestamp and camera id."""
    panel = cctv_panel(w, h).convert("RGBA")
    case = case_layer()
    shelf_y = int(h * 0.80)
    max_h = int(shelf_y * 0.94)
    max_w = int(w * 0.52)
    scale = min(max_h / float(case.height), max_w / float(case.width))
    if scale < 1.0:
        case = case.resize((max(1, int(round(case.width * scale))),
                            max(1, int(round(case.height * scale)))),
                           Image.LANCZOS)
    case = case.rotate(-2, expand=True, resample=Image.BICUBIC)
    cx = (w - case.width) // 2
    cy = shelf_y - case.height + 3
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([cx + 10, shelf_y - 4, cx + case.width + 6, shelf_y + 9],
               fill=(0, 0, 0, 190))
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    panel = Image.alpha_composite(panel, shadow)
    d = ImageDraw.Draw(panel, "RGBA")
    d.rectangle([cx + 8, shelf_y - 1, cx + case.width - 8, shelf_y + 1],
                fill=(0, 0, 0, 150))
    panel.paste(case, (cx, cy), case)
    d = ImageDraw.Draw(panel, "RGBA")
    mono = ImageFont.truetype(MONO, 19)
    cam = ImageFont.truetype(MONO, 16)
    stamp_w = mono.getsize("17 SEP 2013 23:58")[0]
    d.text((w - stamp_w - 14, h - 33), "17 SEP 2013 23:58", font=mono,
           fill=(230, 240, 232, 240))
    d.text((14, 14), "CAM 06", font=cam, fill=(230, 240, 232, 230))
    # Frame: printed photo white edge, then a hairline.
    d.rectangle([0, 0, w - 1, h - 1], outline=(238, 232, 214, 255), width=8)
    d.rectangle([8, 8, w - 9, h - 9], outline=(20, 16, 12, 255), width=2)
    return panel


def ghost_cutout(target_h):
    """White ghost mark at target height, detached pale badge removed."""
    ss = 4
    ghost = Image.open(GHOST_PATH).convert("RGBA")
    gb = ghost.getchannel("A").getbbox()
    core_h = gb[3] - gb[1]
    scale = (target_h * ss) / float(core_h)
    scaled = ghost.resize((max(1, int(round(ghost.width * scale))),
                           max(1, int(round(ghost.height * scale)))),
                          Image.LANCZOS)
    badge = Image.new("L", scaled.size, 0)
    bx = scaled.width * 0.735
    by = scaled.height * 0.673
    br = max(6, int(round(scaled.height * 0.148)))
    ImageDraw.Draw(badge).ellipse([bx - br, by - br, bx + br, by + br], fill=255)
    scaled.putalpha(ImageChops.multiply(scaled.getchannel("A"),
                                        ImageChops.invert(badge)))
    sb = scaled.getchannel("A").getbbox()
    scaled = scaled.crop(sb)
    return scaled.resize((max(1, int(round(scaled.width / ss))),
                          max(1, int(round(scaled.height / ss)))),
                         Image.LANCZOS)


def ghost_ink(target_h):
    """Solid ink silhouette of the ghost, badge removed, for print-on-paper marks."""
    ss = 4
    ghost = Image.open(GHOST_PATH).convert("RGBA")
    gb = ghost.getchannel("A").getbbox()
    core_h = gb[3] - gb[1]
    scale = (target_h * ss) / float(core_h)
    scaled = ghost.resize((max(1, int(round(ghost.width * scale))),
                           max(1, int(round(ghost.height * scale)))),
                          Image.LANCZOS)
    badge = Image.new("L", scaled.size, 0)
    bx = scaled.width * 0.735
    by = scaled.height * 0.673
    br = max(6, int(round(scaled.height * 0.148)))
    ImageDraw.Draw(badge).ellipse([bx - br, by - br, bx + br, by + br], fill=255)
    alpha = ImageChops.multiply(scaled.getchannel("A"),
                                ImageChops.invert(badge))
    # Knock the dark face features out so the mark keeps eyes and mouth.
    rgbimg = scaled.convert("RGB")
    dark = rgbimg.convert("L").point(lambda v: 255 if v < 90 else 0)
    alpha = ImageChops.subtract(alpha.point(lambda v: 255 if v > 90 else 0),
                                dark.point(lambda v: v // 3))
    sb = alpha.getbbox()
    alpha = alpha.crop(sb)
    mark = Image.new("RGBA", alpha.size, rgb(INK) + (255,))
    mark.putalpha(alpha)
    return mark.resize((max(1, int(round(mark.width / ss))),
                        max(1, int(round(mark.height / ss)))),
                       Image.LANCZOS)


def recolor_wordmark(target_h, color=BRAND):
    wm = Image.open(WORDMARK_PATH).convert("RGBA")
    a = wm.getchannel("A")
    solid = Image.new("RGBA", wm.size, rgb(color) + (255,))
    solid.putalpha(a)
    b = a.getbbox()
    solid = solid.crop(b)
    scale = target_h / float(solid.height)
    solid = solid.resize((max(1, int(round(solid.width * scale))), target_h),
                         Image.LANCZOS)
    return solid


def seal_with_rings(target_h):
    """Ghost disc with a double ring, so it reads as a poster seal."""
    base = build_seal(target_h)
    pad = max(6, target_h // 11)
    size = target_h + 2 * pad
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(base, (pad, pad), base)
    d = ImageDraw.Draw(out, "RGBA")
    d.ellipse([1, 1, size - 2, size - 2], outline=rgb(INK) + (235,), width=2)
    r = pad + int(target_h * 0.045)
    d.ellipse([r, r, size - 1 - r, size - 1 - r],
              outline=(255, 255, 255, 225), width=2)
    return out


def badge_portrait(size):
    """Square agent badge: white ghost cutout on magenta, ink border."""
    ss = 4
    px = size * ss
    box = Image.new("RGBA", (px, px), rgb(BRAND) + (255,))
    ghost = Image.open(GHOST_PATH).convert("RGBA")
    gb = ghost.getchannel("A").getbbox()
    core_h = gb[3] - gb[1]
    target_h = int(px * 0.76)
    scale = target_h / float(core_h)
    scaled = ghost.resize((max(1, int(round(ghost.width * scale))),
                           max(1, int(round(ghost.height * scale)))), Image.LANCZOS)
    # Remove the pale badge the official mark carries at its lower right.
    mask = Image.new("L", scaled.size, 0)
    bx = scaled.width * 0.735
    by = scaled.height * 0.673
    br = max(6, int(round(scaled.height * 0.148)))
    ImageDraw.Draw(mask).ellipse([bx - br, by - br, bx + br, by + br], fill=255)
    scaled.putalpha(ImageChops.multiply(scaled.getchannel("A"),
                                        ImageChops.invert(mask)))
    sb = scaled.getchannel("A").getbbox()
    scaled = scaled.crop(sb)
    box.paste(scaled, ((px - scaled.width) // 2, (px - scaled.height) // 2), scaled)
    d = ImageDraw.Draw(box)
    d.rectangle([0, 0, px - 1, px - 1], outline=rgb(INK) + (255,), width=3 * ss)
    d.rectangle([5 * ss, 5 * ss, px - 1 - 5 * ss, px - 1 - 5 * ss],
                outline=(255, 255, 255, 120), width=ss)
    return box.resize((size, size), Image.LANCZOS)


def main():
    for path in (GHOST_PATH, WORDMARK_PATH, FONT_BLACK, SERIF, MONO):
        if not os.path.isfile(path):
            raise SystemExit("make_wanted.py: missing %s" % path)

    canvas = Image.new("RGB", (W, H), rgb(WALL))
    wall_grain = Image.effect_noise((W // 4, H // 4), 22).resize((W, H), Image.BILINEAR)
    canvas = Image.blend(canvas, Image.merge("RGB", (wall_grain, wall_grain, wall_grain)), 0.06)
    draw = ImageDraw.Draw(canvas, "RGBA")
    for x in range(0, W, 54):
        draw.line([(x, 0), (x, H)], fill=(0, 0, 0, 16), width=2)

    # Sheet shadow then paper.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rounded_rect(ImageDraw.Draw(shadow),
                 (SHEET[0] + 10, SHEET[1] + 16, SHEET[2] + 12, SHEET[3] + 14),
                 8, (0, 0, 0, 150))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"),
                                       shadow.filter(ImageFilter.GaussianBlur(14))).convert("RGB"), (0, 0))
    canvas.paste(paper_sheet(), (SHEET[0], SHEET[1]))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Double poster frame.
    draw.rectangle([INNER[0], INNER[1], INNER[2], INNER[3]], outline=rgb(INK) + (255,), width=3)
    draw.rectangle([INNER[0] + 9, INNER[1] + 9, INNER[2] - 9, INNER[3] - 9],
                   outline=rgb(INK) + (255,), width=1)

    records = []
    qa = []
    flags = []

    # ---------------- header ----------------
    wanted_font, _, _ = fit_font("WANTED", SERIF, 176, 740, spacing=12, minimum=60)
    wb, _ = place_text(canvas, records, "WANTED", "WANTED", wanted_font, INK,
                       540, 70, align="center", spacing=12)
    qa.append(("value", records[-1]))

    sub_font = ImageFont.truetype(SERIF, 34)
    sb, _ = place_text(canvas, records, "DEAD OR DELAYED", "DEAD OR DELAYED",
                       sub_font, BRAND, 540, wb[3] + 18, align="center", spacing=9)
    qa.append(("value", records[-1]))
    # Small diamonds either side of the subline.
    for side in (-1, 1):
        cx = 540 + side * (sb[0] + sb[2]) / 2.0 + side * 26
        cy = (sb[1] + sb[3]) / 2.0
        draw.polygon([(cx, cy - 9), (cx + 9, cy), (cx, cy + 9), (cx - 9, cy)],
                     fill=rgb(BRAND) + (255,))

    rule_y = sb[3] + 20
    draw.rectangle([120, rule_y, 960, rule_y + 3], fill=rgb(INK) + (255,))
    draw.rectangle([120, rule_y + 8, 960, rule_y + 10], fill=rgb(INK) + (255,))

    # ---------------- cctv photo ----------------
    photo_w, photo_h = 296, 296
    photo_box = ((W - photo_w) // 2, rule_y + 32,
                 (W + photo_w) // 2, rule_y + 32 + photo_h)
    photo = cctv_mock(photo_w, photo_h)
    canvas.paste(photo, (photo_box[0], photo_box[1]), photo)

    # ---------------- suspect name ----------------
    name_font, _, _ = fit_font("GRAND THEFT AUTO VI", FONT_BLACK, 66, 850,
                               spacing=1, minimum=40)
    nb, _ = place_text(canvas, records, "SUSPECT NAME", "GRAND THEFT AUTO VI",
                       name_font, INK, 540, photo_box[3] + 12, align="center",
                       spacing=1)
    qa.append(("value", records[-1]))

    # ---------------- last seen ----------------
    seen_font = ImageFont.truetype(MONO, 24)
    sk, _ = place_text(canvas, records, "LAST SEEN", "LAST SEEN: 17 SEP 2013, VICE CITY",
                       seen_font, INK, 540, nb[3] + 10, align="center", spacing=1)
    qa.append(("label", records[-1]))

    # ---------------- crime ----------------
    crime_font, _, _ = fit_font("CRIME: GRAND THEFT OF 13 YEARS OF MY LIFE",
                                FONT_BLACK, 44, 820, minimum=30)
    cb, _ = place_text(canvas, records, "CRIME",
                       "CRIME: GRAND THEFT OF 13 YEARS OF MY LIFE", crime_font,
                       INK, 540, sk[3] + 10, align="center")
    qa.append(("value", records[-1]))

    # ---------------- reward ----------------
    label_font = ImageFont.truetype(SERIF, 28)
    rl, _ = place_text(canvas, records, "REWARD LABEL", "REWARD", label_font,
                       INK, 540, cb[3] + 14, align="center", spacing=7)
    qa.append(("label", records[-1]))
    amount_font = ImageFont.truetype(FONT_BLACK, 84)
    ab, _ = place_text(canvas, records, "REWARD AMOUNT", "$500", amount_font,
                       BRAND, 540, rl[3] + 8, align="center")
    qa.append(("value", records[-1]))
    rel_font, _, _ = fit_font("FOR ITS RELEASE", FONT_BLACK, 46, 850, spacing=1,
                              minimum=30)
    rlb, _ = place_text(canvas, records, "RELEASE LINE", "FOR ITS RELEASE",
                        rel_font, INK, 540, ab[3] + 8, align="center", spacing=1)
    qa.append(("value", records[-1]))

    # ---------------- funding band ----------------
    band_top = rlb[3] + 14
    draw.rectangle([120, band_top, 960, band_top + 3], fill=rgb(INK) + (255,))
    draw.rectangle([120, band_top + 9, 960, band_top + 10], fill=rgb(INK) + (255,))
    coin = ghost_ink(104)
    f1_font = ImageFont.truetype(FONT_SEMI, 30)
    f1, _, _, _ = text_piece("REWARD FUNDED BY MY AI AGENT'S", f1_font, INK, 0)
    wm = recolor_wordmark(50)
    f2_font = ImageFont.truetype(FONT_SEMI, 44)
    f2, _, _, _ = text_piece("WINNINGS", f2_font, INK, 0)
    gap = 14
    row2_w = wm.width + gap + f2.width
    text_w = max(f1.width, row2_w)
    text_h = 22 + 6 + wm.height
    coin_gap = 26
    total_w = coin.width + coin_gap + text_w
    gx = int(round(540 - total_w / 2.0))
    coin_y = band_top + 12
    f1_x = gx + coin.width + coin_gap
    f1_y = coin_y + (coin.height - text_h) // 2
    canvas.paste(f1, (f1_x, f1_y), f1)
    l2_y = f1_y + 22 + 6
    canvas.paste(wm, (f1_x, l2_y), wm)
    f2_y = l2_y + wm.height - f2.getchannel("A").getbbox()[3]
    canvas.paste(f2, (f1_x + wm.width + gap, f2_y), f2)
    canvas.paste(coin, (gx, coin_y), coin)
    band_bottom = coin_y + coin.height + 12
    draw.rectangle([120, band_bottom, 960, band_bottom + 3], fill=rgb(INK) + (255,))
    draw.rectangle([120, band_bottom + 9, 960, band_bottom + 10], fill=rgb(INK) + (255,))
    records.append({"name": "FUNDING",
                    "text": "REWARD FUNDED BY MY AI AGENT'S make.fun WINNINGS",
                    "box": (gx, coin_y, f1_x + text_w, band_bottom),
                    "block": "footer", "overlay": False,
                    "size": f1_font.size,
                    "ink_h": f1.getchannel("A").getbbox()[3]})
    qa.append(("label", records[-1]))

    # ---------------- QA ----------------
    text_boxes = [(n, r) for n, r in qa]
    for i in range(len(text_boxes)):
        for j in range(i + 1, len(text_boxes)):
            a, b = text_boxes[i][1]["box"], text_boxes[j][1]["box"]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 1 and oy > 1:
                flags.append("%s overlaps %s" % (text_boxes[i][1]["name"],
                                                 text_boxes[j][1]["name"]))

    for role, rec in qa:
        b = rec["box"]
        gap = min(b[0] - INNER[0], b[1] - INNER[1],
                  INNER[2] - b[2], INNER[3] - b[3])
        if gap < 10:
            flags.append("%s is only %d px inside the frame" % (rec["name"], gap))
        h480 = rec["ink_h"] * 480.0 / 1080.0
        minimum = 8.0 if role == "label" else 11.0
        if h480 < minimum:
            flags.append("%s is only %.1f px high at 480" % (rec["name"], h480))

    # Photo and seal must sit inside the frame, and the seal must not touch the header.
    if photo_box[0] < INNER[0] + 10 or photo_box[2] > INNER[2] - 10:
        flags.append("photo leaves the frame horizontally")
    if photo_box[3] > INNER[3] - 10:
        flags.append("photo leaves the frame vertically")
    if band_bottom + 10 > INNER[3] - 10:
        flags.append("funding band bottom is %d px inside the frame" % (INNER[3] - band_bottom))
    if band_top < rlb[3] + 6:
        flags.append("funding band touches the release line")
    if photo_box[3] + 10 > nb[1]:
        flags.append("photo crowds the suspect name")

    if os.environ.get("DEBUG"):
        for role, rec in qa:
            print("  BOX %-18s %s" % (rec["name"][:18], rec["box"]))
        print("  BOX photo", photo_box, "rule", rule_y)
    print("FLAGS:", "none" if not flags else str(len(flags)))
    for f in flags:
        print("  FLAG", f)
    print("BOXES: sheet", SHEET, "inner", INNER, "photo", photo_box)
    print("480 INK HEIGHTS (labels >=8, values >=11):")
    for role, rec in qa:
        h480 = rec["ink_h"] * 480.0 / 1080.0
        print("  %-5s %5.1f px  %s" % (role, h480, rec["text"]))
    print("WANTED width %d (%.1f at 480)"
          % (wb[2] - wb[0], (wb[2] - wb[0]) * 480.0 / 1080.0))
    print("REWARD width %d (%.1f at 480)"
          % (ab[2] - ab[0], (ab[2] - ab[0]) * 480.0 / 1080.0))

    out = os.path.join(HERE, "wanted.png")
    canvas.save(out, optimize=True)
    canvas.resize((480, 480), Image.LANCZOS).save(
        os.path.join(HERE, "wanted_480.png"), optimize=True)
    data = open(out, "rb").read()
    print("wanted.png: %dx%d, %d bytes" % (canvas.width, canvas.height, len(data)))
    print("wanted.png sha256:", hashlib.sha256(data).hexdigest())

    if flags:
        raise SystemExit("make_wanted.py: QA flags remain")


if __name__ == "__main__":
    main()
