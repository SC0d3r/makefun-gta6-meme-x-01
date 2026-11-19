#!/usr/bin/env python3
"""Render meme.png: a GTA 6 / Vice City "MISSION PASSED" joke for make.fun."""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1080
HERE = os.path.dirname(os.path.abspath(__file__))
GHOST_PATH = os.path.join(HERE, "assets", "ghost.png")
WORDMARK_PATH = os.path.join(HERE, "assets", "wordmark.png")
FONT_DIR = "/usr/share/fonts/truetype/lato"

NEAR_BLACK = "#191419"
PLUM = "#380E32"
MAGENTA = "#FF409C"
GOLD_LIGHT = "#FFF8DC"
GOLD_DARK = "#FFBE70"
CREAM = "#FFD296"


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def vgrad(height, stops, width=W):
    """Vertical RGB gradient; stops are (row, '#rrggbb') from 0 to height - 1."""
    rows = []
    for y in range(height):
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y <= y1 or i == len(stops) - 2:
                t = 0.0 if y1 == y0 else (y - y0) / float(y1 - y0)
                t = max(0.0, min(1.0, t))
                a, b = rgb(c0), rgb(c1)
                rows.append(tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3)))
                break
    img = Image.new("RGB", (1, height))
    img.putdata(rows)
    return img.resize((width, height), Image.BILINEAR)


def band(y0, y1, stops):
    """Gradient covering rows y0 .. y1 - 1, with absolute y stops."""
    rel = [(y - y0, c) for y, c in stops]
    return vgrad(y1 - y0, rel)


def bezier(p0, p1, p2, steps=24):
    out = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def text_piece(text, font, fill=None, gradient=None, outline=0,
               outline_color=NEAR_BLACK, spacing=0):
    """Return (RGBA piece, fill offset in piece, fill width, fill height)."""
    widths = [font.getsize(ch)[0] for ch in text]
    total = sum(widths) + spacing * max(0, len(text) - 1)
    line_h = font.getsize(text)[1]
    pad = outline + 30
    size = (int(total) + pad * 2 + 8, int(line_h) + pad * 2 + 8)

    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    x = pad
    for ch in text:
        md.text((x, pad), ch, font=font, fill=255)
        x += font.getsize(ch)[0] + spacing
    fill_box = mask.getbbox()
    if fill_box is None:
        raise SystemExit("make_meme.py: text %r rendered empty" % text)

    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    if outline:
        ld = ImageDraw.Draw(layer)
        x = pad
        for ch in text:
            ld.text((x, pad), ch, font=font, fill=outline_color,
                    stroke_width=outline, stroke_fill=outline_color)
            x += font.getsize(ch)[0] + spacing

    fill_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    if gradient:
        gw, gh = fill_box[2] - fill_box[0], fill_box[3] - fill_box[1]
        grad = vgrad(gh, [(0, gradient[0]), (max(0, gh - 1), gradient[1])], gw)
        fill_layer.paste(grad, (fill_box[0], fill_box[1]), mask.crop(fill_box))
    else:
        solid = Image.new("RGBA", size, rgb(fill) + (255,))
        fill_layer.paste(solid, (0, 0), mask)
    layer = Image.alpha_composite(layer, fill_layer)

    box = layer.getbbox()
    piece = layer.crop(box)
    return (piece,
            (fill_box[0] - box[0], fill_box[1] - box[1]),
            fill_box[2] - fill_box[0],
            fill_box[3] - fill_box[1])


def check_bounds(name, left, top, right, bottom, max_right=1000):
    if left < 0 or top < 0 or right > W or bottom > H:
        raise SystemExit("make_meme.py: %s runs off the %dx%d canvas "
                         "(box %.1f,%.1f,%.1f,%.1f)" % (name, W, H, left, top, right, bottom))
    if right > max_right:
        raise SystemExit("make_meme.py: %s runs past x=%d (right edge %.1f)"
                         % (name, max_right, right))


def put_text(canvas, name, text, font, x, y, fill=None, gradient=None,
             outline=0, outline_color=NEAR_BLACK, spacing=0,
             align_right=None, max_right=1000):
    piece, off, fw, fh = text_piece(text, font, fill, gradient, outline,
                                    outline_color, spacing)
    px = x - off[0]
    if align_right is not None:
        px = align_right - fw - off[0]
    py = y - off[1]
    check_bounds(name, px, py, px + piece.width, py + piece.height, max_right)
    canvas.paste(piece, (int(round(px)), int(round(py))), piece)
    return piece.width


def preflight(name, text, font, x, y, spacing=0, outline=0,
              align_right=None, max_right=1000):
    """Measure a line with font.getsize before it is drawn."""
    advance = sum(font.getsize(ch)[0] for ch in text)
    advance += spacing * max(0, len(text) - 1)
    piece, off, fw, fh = text_piece(text, font, "#FFFFFF", None, outline,
                                    NEAR_BLACK, spacing)
    px = x - off[0]
    if align_right is not None:
        px = align_right - fw - off[0]
    py = y - off[1]
    left, top = px, py
    right, bottom = px + piece.width, py + piece.height
    if left < 0 or top < 0 or right > W or bottom > H:
        raise SystemExit("make_meme.py: %s runs off the %dx%d canvas "
                         "(box %.1f,%.1f,%.1f,%.1f)" % (name, W, H, left, top, right, bottom))
    if right > max_right:
        raise SystemExit("make_meme.py: %s runs past x=%d (right edge %.1f)"
                         % (name, max_right, right))
    return advance, right, max_right


def draw_trunk(draw, p0, p1, w0, w1, bend):
    ctrl = ((p0[0] + p1[0]) / 2.0 + bend, (p0[1] + p1[1]) / 2.0)
    pts = bezier(p0, ctrl, p1, 30)
    for i in range(len(pts) - 1):
        t = (i + 0.5) / (len(pts) - 1)
        draw.line([pts[i], pts[i + 1]], fill=NEAR_BLACK,
                  width=int(round(w0 + (w1 - w0) * t + 6)))
    for i in range(len(pts) - 1):
        t = (i + 0.5) / (len(pts) - 1)
        draw.line([pts[i], pts[i + 1]], fill=PLUM,
                  width=int(round(w0 + (w1 - w0) * t)))


def draw_frond(draw, base, angle, length, droop, width):
    a = math.radians(angle)
    tip = (base[0] + math.cos(a) * length,
           base[1] + math.sin(a) * length + droop)
    ctrl = (base[0] + math.cos(a) * length * 0.55,
            base[1] + math.sin(a) * length * 0.55 - length * 0.10)
    pts = bezier(base, ctrl, tip, 22)

    def spine(fill, extra):
        for i in range(len(pts) - 1):
            t = (i + 0.5) / (len(pts) - 1)
            draw.line([pts[i], pts[i + 1]], fill=fill,
                      width=max(1, int(round(width + (2 - width) * t + extra))))

    spine(NEAR_BLACK, 5)
    spine(PLUM, 0)

    for j in range(6, 20):
        t = j / 21.0
        p = pts[min(len(pts) - 1, int(t * (len(pts) - 1)))]
        q = pts[min(len(pts) - 1, int(t * (len(pts) - 1)) + 1)]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        leaf = math.sin(math.pi * t) * length * 0.14
        for side in (-1, 1):
            end = (p[0] + nx * leaf * side + dx / ln * leaf * 0.45,
                   p[1] + ny * leaf * side + dy / ln * leaf * 0.45)
            draw.line([p, end], fill=NEAR_BLACK, width=5)
            draw.line([p, end], fill=PLUM, width=2)


def draw_palm(draw, base, top, w0, w1, bend, fronds, length, droop):
    draw_trunk(draw, base, top, w0, w1, bend)
    start, step = -168.0, 156.0 / (fronds - 1)
    for i in range(fronds):
        draw_frond(draw, top, start + step * i, length, droop, 9)
    draw.ellipse([top[0] - 14, top[1] - 14, top[0] + 14, top[1] + 14],
                 fill=NEAR_BLACK)
    draw.ellipse([top[0] - 10, top[1] - 10, top[0] + 10, top[1] + 10], fill=PLUM)


def draw_flamingo(draw, cx, feet_y):
    body_cy = feet_y - 118
    draw.line([(cx - 12, body_cy + 28), (cx - 16, feet_y)], fill=NEAR_BLACK, width=9)
    draw.line([(cx + 10, body_cy + 28), (cx + 16, feet_y)], fill=NEAR_BLACK, width=9)
    draw.line([(cx - 12, body_cy + 28), (cx - 16, feet_y)], fill="#FF6CA4", width=4)
    draw.line([(cx + 10, body_cy + 28), (cx + 16, feet_y)], fill="#FF6CA4", width=4)
    draw.line([(cx - 26, feet_y), (cx - 8, feet_y)], fill=NEAR_BLACK, width=5)
    draw.line([(cx + 8, feet_y), (cx + 26, feet_y)], fill=NEAR_BLACK, width=5)

    draw.ellipse([cx - 58, body_cy - 44, cx + 58, body_cy + 44], fill=NEAR_BLACK)
    draw.ellipse([cx - 52, body_cy - 38, cx + 52, body_cy + 38], fill="#FF6CA4")

    neck = bezier((cx + 34, body_cy - 20), (cx + 72, body_cy - 60),
                  (cx + 66, body_cy - 102), 20)
    for width, color in ((18, NEAR_BLACK), (11, "#FF6CA4")):
        for i in range(len(neck) - 1):
            draw.line([neck[i], neck[i + 1]], fill=color, width=width)

    hx, hy = cx + 66, body_cy - 104
    draw.ellipse([hx - 18, hy - 18, hx + 18, hy + 18], fill=NEAR_BLACK)
    draw.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], fill="#FF6CA4")
    draw.polygon([(hx + 10, hy - 6), (hx + 42, hy + 2), (hx + 10, hy + 9)],
                 fill=NEAR_BLACK)
    draw.polygon([(hx + 12, hy - 4), (hx + 38, hy + 2), (hx + 12, hy + 7)],
                 fill="#FF6CA4")
    draw.ellipse([hx + 1, hy - 6, hx + 6, hy - 1], fill=NEAR_BLACK)


def main():
    for path in (GHOST_PATH, WORDMARK_PATH):
        if not os.path.isfile(path):
            raise SystemExit("make_meme.py: missing asset %s" % path)

    font_black = os.path.join(FONT_DIR, "Lato-Black.ttf")
    font_bold = os.path.join(FONT_DIR, "Lato-Bold.ttf")
    font_semi = os.path.join(FONT_DIR, "Lato-Semibold.ttf")
    for path in (font_black, font_bold, font_semi):
        if not os.path.isfile(path):
            raise SystemExit("make_meme.py: missing font %s" % path)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)
    measurements = []

    # Sky and sun.
    canvas.paste(band(0, 471, [(0, "#1C0622"), (90, "#4A0A42"), (200, "#92126E"),
                               (280, "#CC1E74"), (340, "#F53E64"), (410, "#FF7654"),
                               (455, "#FFAC5C"), (470, "#FFD694")]), (0, 0))

    r = 168
    sun = vgrad(2 * r, [(0, "#FFF8E2"), (2 * r - 1, "#FFBE70")], 2 * r).convert("RGBA")
    sm = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(sm).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    sun.putalpha(sm)
    sd = ImageDraw.Draw(sun)
    for pct, bar_h in ((0.32, 6), (0.44, 8), (0.56, 10), (0.68, 12)):
        yy = int(round(pct * r))
        dy = yy - r
        half = int(round(math.sqrt(max(0, r * r - dy * dy))))
        sd.rectangle([r - half, yy, r + half, yy + bar_h - 1], fill=rgb("#E23466"))
    sun = sun.crop((0, 0, 2 * r, r))
    canvas.paste(sun, (786 - r, 470 - r), sun)

    # Hotels on the left horizon.
    for x0, x1, bh in ((0, 168, 210), (190, 356, 150), (378, 520, 76)):
        top = 476 - bh
        draw.rectangle([x0, top, x1, 476], fill=rgb(PLUM))
        draw.rectangle([x0, top, x1, top + 1], fill=rgb(MAGENTA))
        wx = x0 + 12
        while wx + 9 <= x1 - 8:
            wy = top + 14
            while wy + 13 <= 466:
                draw.rectangle([wx, wy, wx + 8, wy + 12], fill=rgb("#FFCE96"))
                wy += 30
            wx += 26

    # Sea and its sun reflection.
    canvas.paste(band(470, 641, [(470, "#4AA4A0"), (520, "#1E7E8E"),
                                 (580, "#0E566C"), (640, "#093A58")]), (0, 470))
    glint = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glint)
    for i in range(16):
        yy = 474 + i * 10
        t = (yy - 470) / 170.0
        ww = 40 + 220 * t
        alpha = int(round(235 * (1 - t) + 20))
        gd.rectangle([786 - ww / 2, yy, 786 + ww / 2, yy + 4],
                     fill=rgb(CREAM) + (max(20, alpha),))
    canvas.paste(glint, (0, 0), glint)

    # Beach and foam.
    canvas.paste(band(640, 1081, [(640, "#D88C84"), (700, "#F2BA92"),
                                  (800, "#F7CEA8"), (1000, "#FDE4C0"),
                                  (1080, "#FDE4C0")]), (0, 640))
    foam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(foam)
    for base_y, width, alpha, phase in ((646, 6, 235, 0.0), (662, 4, 185, 1.3),
                                        (680, 3, 145, 2.6)):
        pts = [(x, base_y + math.sin(x / 58.0 + phase) * 3.0) for x in range(0, W + 8, 8)]
        fd.line(pts, fill=(255, 246, 230, alpha), width=width, joint="curve")
    canvas.paste(foam, (0, 0), foam)

    # Palms.
    draw_palm(draw, (10, 1100), (58, 424), 30, 13, 28, 9, 150, 34)
    draw_palm(draw, (890, 490), (862, 372), 20, 9, 8, 7, 90, 20)

    # Flamingo on the sand.
    draw_flamingo(draw, 660, 820)

    # Ghost shadow, rims, then the official ghost.
    ghost = Image.open(GHOST_PATH).convert("RGBA")
    gbox = ghost.getchannel("A").getbbox()
    scale = 460.0 / (gbox[2] - gbox[0])
    ghost = ghost.resize((int(round(ghost.width * scale)),
                          int(round(ghost.height * scale))), Image.LANCZOS)
    gbox = ghost.getchannel("A").getbbox()
    gx = int(round(344 - (gbox[0] + gbox[2]) / 2.0))
    gy = int(round(966 - gbox[3]))

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([344 - 210, 966 - 20, 344 + 210, 966 + 20],
                                   fill=rgb("#28041E") + (166,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(11))
    canvas.paste(shadow, (0, 0), shadow)

    alpha = ghost.getchannel("A")
    for color, dx, dy in (("#FF4A96", 10, 4), ("#FFCE96", 5, -2)):
        rim = Image.new("RGBA", ghost.size, rgb(color) + (255,))
        rim.putalpha(alpha)
        canvas.paste(rim, (gx + dx, gy + dy), rim)

    warm = ghost.copy()
    px = warm.load()
    for yy in range(warm.height):
        for xx in range(warm.width):
            r0, g0, b0, a0 = px[xx, yy]
            px[xx, yy] = (min(255, int(r0 * 1.03 + 4)),
                          min(255, int(g0 * 1.01 + 2)),
                          int(b0 * 0.95), a0)
    canvas.paste(warm, (gx, gy), warm)

    # Headline.
    headline = ImageFont.truetype(font_black, 148)
    measurements.append(("MISSION",) + preflight("MISSION", "MISSION", headline,
                                                  56, 52, outline=11))
    measurements.append(("PASSED",) + preflight("PASSED", "PASSED", headline,
                                                 56, 196, outline=11))
    put_text(canvas, "MISSION", "MISSION", headline, 56, 52,
             gradient=(GOLD_LIGHT, GOLD_DARK), outline=11)
    put_text(canvas, "PASSED", "PASSED", headline, 56, 196,
             gradient=(GOLD_LIGHT, GOLD_DARK), outline=11)

    subtitle = ImageFont.truetype(font_bold, 38)
    measurements.append(("subtitle",) + preflight("subtitle", "GTA 6 \u00b7 THE 13-YEAR WAIT",
                                                   subtitle, 60, 350, spacing=7, outline=6))
    put_text(canvas, "subtitle", "GTA 6 \u00b7 THE 13-YEAR WAIT", subtitle, 60, 350,
             fill="#FFFCF6", outline=6, spacing=7)

    # Reward card.
    draw.rectangle([720, 724, 1040, 962], fill=rgb("#150514"))
    draw.rectangle([720, 724, 1040, 962], outline=rgb("#FFC46E"), width=2)
    reward_font = ImageFont.truetype(font_bold, 24)
    measurements.append(("REWARD",) + preflight("REWARD", "REWARD", reward_font,
                                                  746, 740, spacing=7))
    put_text(canvas, "REWARD", "REWARD", reward_font, 746, 740,
             fill="#FFE2B4", spacing=7)
    amount_font = ImageFont.truetype(font_black, 110)
    measurements.append(("$500",) + preflight("$500", "$500", amount_font,
                                               746, 774, max_right=1000))
    put_text(canvas, "$500", "$500", amount_font, 746, 774,
             gradient=(GOLD_LIGHT, GOLD_DARK), max_right=1000)
    paid_font = ImageFont.truetype(font_bold, 26)
    measurements.append(("PAID",) + preflight("PAID TO MY AI AGENT", "PAID TO MY AI AGENT",
                                               paid_font, 746, 878, max_right=1036))
    put_text(canvas, "PAID TO MY AI AGENT", "PAID TO MY AI AGENT", paid_font,
             746, 878, fill="#FFFFFF", max_right=1036)

    wordmark = Image.open(WORDMARK_PATH).convert("RGBA")
    card_mark = wordmark.resize((152, int(round(152 * wordmark.height / wordmark.width))),
                                Image.LANCZOS)
    canvas.paste(card_mark, (746, 962 - 12 - card_mark.height), card_mark)

    # Footer.
    draw.rectangle([0, 996, W, H], fill=rgb("#100410"))
    draw.rectangle([0, 996, W, 997], fill=rgb("#FF3D9A"))
    foot_mark = wordmark.resize((232, int(round(232 * wordmark.height / wordmark.width))),
                                Image.LANCZOS)
    canvas.paste(foot_mark, (36, 996 + (84 - foot_mark.height) // 2), foot_mark)
    foot_font = ImageFont.truetype(font_semi, 25)
    measurements.append(("footer",) + preflight("footer", "AI AGENTS EARN REAL MONEY HERE",
                                                foot_font, 0, 1025,
                                                align_right=1042, max_right=1042))
    put_text(canvas, "footer", "AI AGENTS EARN REAL MONEY HERE", foot_font,
             0, 1025, fill="#FFE2F0", align_right=1042, max_right=1042)

    out = os.path.join(HERE, "meme.png")
    canvas.convert("RGB").save(out, optimize=True)
    print("wrote %s (%dx%d)" % (out, W, H))
    for name, advance, right, limit in measurements:
        print("  %-8s advance=%4dpx right=%7.1f limit=%d" % (name, advance, right, limit))


if __name__ == "__main__":
    main()
