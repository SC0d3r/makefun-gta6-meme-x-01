#!/usr/bin/env python3
"""Render payslip.png: a GTA 6 payroll joke with make.fun's ghost as the AI employee."""

import hashlib
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

W = H = 1080
HERE = os.path.dirname(os.path.abspath(__file__))
GHOST_PATH = os.path.join(HERE, "assets", "ghost.png")
FONT_DIR = "/usr/share/fonts/truetype/lato"
FONT_BLACK = os.path.join(FONT_DIR, "Lato-Black.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "Lato-Bold.ttf")
FONT_SEMI = os.path.join(FONT_DIR, "Lato-Semibold.ttf")

PAPER = "#F6F1E6"
INK = "#14110E"
MUTED = "#7A7166"
HAIRLINE = "#D8CFC0"
MAGENTA = "#C2185B"
PITCH_INK = "#4A4239"

LEFT = (78, 252, 520, 890)
RIGHT = (560, 252, 1002, 890)
HEADER = (78, 34, 1002, 238)
FOOTER = (78, 906, 1002, 1046)
BLOCKS = {"header": HEADER, "left": LEFT, "right": RIGHT, "footer": FOOTER}


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    ca, cb = rgb(a), rgb(b)
    return tuple(int(round(ca[i] + (cb[i] - ca[i]) * t)) for i in range(3))


def text_piece(text, font, fill, spacing=0):
    """Return an ink-cropped RGBA piece, its advance, and its ink offset."""
    widths = [font.getsize(ch)[0] for ch in text]
    advance = sum(widths) + spacing * max(0, len(text) - 1)
    line_h = font.getsize(text)[1]
    pad = 12
    layer = Image.new("RGBA", (int(advance) + pad * 2, int(line_h) + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x = pad
    for ch in text:
        draw.text((x, pad), ch, font=font, fill=rgb(fill))
        x += font.getsize(ch)[0] + spacing
    box = layer.getbbox()
    if box is None:
        raise SystemExit("make_payslip.py: empty text piece for %r" % text)
    piece = layer.crop(box)
    return piece, advance, box[0] - pad, box[1] - pad


def fit_font(text, path, start_size, max_width, spacing=0, minimum=10):
    size = start_size
    while size > minimum:
        font = ImageFont.truetype(path, size)
        width = sum(font.getsize(ch)[0] for ch in text)
        width += spacing * max(0, len(text) - 1)
        if width <= max_width:
            return font, size, width
        size -= 1
    font = ImageFont.truetype(path, minimum)
    return font, minimum, sum(font.getsize(ch)[0] for ch in text)


def place_text(canvas, records, name, text, font, fill, x, y, align="left",
               spacing=0, baseline=False, block="header", overlay=False):
    piece, advance, ink_x, ink_y = text_piece(text, font, fill, spacing)
    if align == "left":
        px = x
    elif align == "right":
        px = x - piece.width
    else:
        px = x - piece.width / 2.0
    if baseline:
        ascent = font.getmetrics()[0]
        py = y - ascent + ink_y
    else:
        py = y
    px, py = int(round(px)), int(round(py))
    canvas.paste(piece, (px, py), piece)
    box = (px, py, px + piece.width, py + piece.height)
    records.append({"name": name, "text": text, "box": box, "block": block,
                    "overlay": overlay, "size": font.size, "ink_h": piece.height})
    return box, advance


def rounded_rect(draw, box, radius, fill):
    x0, y0, x1, y1 = [int(v) for v in box]
    r = int(radius)
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    draw.ellipse([x0, y0, x0 + 2 * r, y0 + 2 * r], fill=fill)
    draw.ellipse([x1 - 2 * r, y0, x1, y0 + 2 * r], fill=fill)
    draw.ellipse([x0, y1 - 2 * r, x0 + 2 * r, y1], fill=fill)
    draw.ellipse([x1 - 2 * r, y1 - 2 * r, x1, y1], fill=fill)


def dotted_leader(draw, x0, x1, y, color=MUTED):
    x = int(x0)
    while x < int(x1):
        draw.rectangle([x, int(y), x + 2, int(y) + 2], fill=rgb(color))
        x += 7


def union_box(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def box_clearance(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def build_photo(ghost):
    """Return (photo, ghost height, head width at 480, clipped alpha box, ring gap, badge residual)."""
    alpha = ghost.getchannel("A")
    gb = alpha.getbbox()
    gh = gb[3] - gb[1]
    ghost_h = 118
    scale = ghost_h / float(gh)
    scaled = ghost.resize((int(round(ghost.width * scale)),
                           int(round(ghost.height * scale))), Image.LANCZOS)
    sa = scaled.getchannel("A")
    sb = sa.getbbox()
    sh = sb[3] - sb[1]
    sh_bottom = sb[1] + int(round(0.45 * sh))
    shb = sa.crop((sb[0], sb[1], sb[2], sh_bottom)).getbbox()
    head_480 = (shb[2] - shb[0]) * 480.0 / 1080.0

    photo = Image.new("RGBA", (144, 144), (0, 0, 0, 0))
    pd = ImageDraw.Draw(photo)
    pd.ellipse([0, 0, 143, 143], fill=rgb(INK) + (255,))
    pd.ellipse([4, 4, 139, 139], fill=rgb(MAGENTA) + (255,))

    hcx = sb[0] + (shb[0] + shb[2]) / 2.0
    hcy = sb[1] + (shb[1] + shb[3]) / 2.0
    ghost_layer = Image.new("RGBA", (144, 144), (0, 0, 0, 0))
    gx = int(round(72 - hcx))
    gy = int(round(72 - hcy))
    ghost_layer.paste(scaled, (gx, gy), scaled)

    # The official mark includes a detached pale badge at its lower right.
    # Clear that badge before the portrait clip, otherwise it survives as a
    # pale crescent against the lower-right edge of the photo.
    badge = Image.new("L", (144, 144), 0)
    badge_cx = gx + scaled.width * 0.735
    badge_cy = gy + scaled.height * 0.673
    badge_r = max(10, int(round(scaled.height * 0.148)))
    ImageDraw.Draw(badge).ellipse(
        [badge_cx - badge_r, badge_cy - badge_r,
         badge_cx + badge_r, badge_cy + badge_r], fill=255)
    ghost_layer.putalpha(ImageChops.multiply(
        ghost_layer.getchannel("A"), ImageChops.invert(badge)))

    clip = Image.new("L", (144, 144), 0)
    ImageDraw.Draw(clip).ellipse([12, 12, 131, 131], fill=255)
    ghost_layer.putalpha(ImageChops.multiply(ghost_layer.getchannel("A"), clip))
    photo = Image.alpha_composite(photo, ghost_layer)
    gbox = ghost_layer.getchannel("A").getbbox()
    ring_gap = min(gbox[0] - 4, gbox[1] - 4, 139 - gbox[2], 139 - gbox[3])
    badge_residual = ImageChops.multiply(
        ghost_layer.getchannel("A"), badge).getbbox()
    return photo, ghost_h, head_480, gbox, ring_gap, badge_residual


def build_stamp():
    stamp = Image.new("RGBA", (190, 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle([4, 4, 185, 7], fill=rgb(MAGENTA) + (255,))
    sd.rectangle([4, 72, 185, 75], fill=rgb(MAGENTA) + (255,))
    sd.rectangle([4, 4, 7, 75], fill=rgb(MAGENTA) + (255,))
    sd.rectangle([182, 4, 185, 75], fill=rgb(MAGENTA) + (255,))
    paid = ImageFont.truetype(FONT_BOLD, 44)
    mark = ImageFont.truetype(FONT_SEMI, 20)
    local = []
    place_text(stamp, local, "stamp PAID", "PAID", paid, MAGENTA,
               95, 9, align="center", block="stamp", overlay=True)
    place_text(stamp, local, "stamp make.fun", "make.fun", mark, MAGENTA,
               95, 48, align="center", block="stamp", overlay=True)
    for r in local:
        b = r["box"]
        assert b[0] >= 8 and b[1] >= 8 and b[2] <= 181 and b[3] <= 71, \
            "stamp text %s leaves its border: %s" % (r["name"], b)
    stamp.putalpha(stamp.getchannel("A").point(lambda v: int(v * 0.72)))
    return stamp.rotate(-11, expand=True, resample=Image.BICUBIC)


def main():
    for path in (GHOST_PATH, FONT_BLACK, FONT_BOLD, FONT_SEMI):
        if not os.path.isfile(path):
            raise SystemExit("make_payslip.py: missing %s" % path)

    canvas = Image.new("RGBA", (W, H), rgb(PAPER) + (255,))
    draw = ImageDraw.Draw(canvas)
    records = []

    # Border, column rule, and section rules.
    draw.rectangle([34, 34, 1046, 35], fill=rgb(INK))
    draw.rectangle([34, 1045, 1046, 1046], fill=rgb(INK))
    draw.rectangle([34, 34, 35, 1046], fill=rgb(INK))
    draw.rectangle([1045, 34, 1046, 1046], fill=rgb(INK))
    draw.rectangle([520, 252, 520, 806], fill=rgb(HAIRLINE))
    draw.rectangle([78, 238, 1002, 239], fill=rgb(INK))
    draw.rectangle([78, 906, 1002, 907], fill=rgb(INK))

    # Header.
    h_small = ImageFont.truetype(FONT_SEMI, 23)
    place_text(canvas, records, "LEONIDA", "LEONIDA PAYROLL SERVICES", h_small, MUTED,
               540, 64, align="center", spacing=3, block="header")
    h_title = ImageFont.truetype(FONT_BOLD, 82)
    place_text(canvas, records, "PAYSLIP", "PAYSLIP", h_title, INK,
               540, 104, align="center", spacing=12, block="header")
    h_period = ImageFont.truetype(FONT_SEMI, 22)
    place_text(canvas, records, "PAY PERIOD", "PAY PERIOD 17 SEP 2013 - 19 NOV 2026",
               h_period, MUTED, 540, 206, align="center", block="header")
    h_no = ImageFont.truetype(FONT_SEMI, 21)
    place_text(canvas, records, "PAYROLL NO.", "PAYROLL NO. 0004811", h_no, MUTED,
               1002, 72, align="right", block="header")

    # Left employee block.
    label_font = ImageFont.truetype(FONT_SEMI, 20)
    place_text(canvas, records, "LEFT EMPLOYEE", "EMPLOYEE", label_font, MUTED,
               78, 270, spacing=3, block="left")
    you_font = ImageFont.truetype(FONT_BOLD, 66)
    place_text(canvas, records, "YOU", "YOU", you_font, INK, 78, 298, block="left")
    job_font = ImageFont.truetype(FONT_SEMI, 20)
    place_text(canvas, records, "LEFT JOB", "PROFESSIONAL GTA 6 WAITER", job_font, MUTED,
               78, 382, spacing=2, block="left")

    ledger_label = ImageFont.truetype(FONT_SEMI, 24)
    ledger_value = ImageFont.truetype(FONT_BOLD, 30)
    left_rows = (("HOURS WAITED", "115,464"), ("SICK DAYS", "47"),
                 ("DELAYS SURVIVED", "2"))
    for i, (label, value) in enumerate(left_rows):
        y = 470 + 62 * i
        lb, _ = place_text(canvas, records, "LEFT " + label, label, ledger_label,
                           MUTED, 78, y, block="left")
        vb, _ = place_text(canvas, records, "LEFT VALUE " + value, value, ledger_value,
                           INK, 496, y, align="right", block="left")
        dotted_leader(draw, lb[2] + 8, vb[0] - 8, y + 21)

    net_label = ImageFont.truetype(FONT_SEMI, 28)
    place_text(canvas, records, "LEFT NET PAY", "NET PAY", net_label, MUTED,
               78, 706, spacing=3, block="left")
    big_font = ImageFont.truetype(FONT_BOLD, 112)
    place_text(canvas, records, "LEFT AMOUNT", "$0.00", big_font, INK,
               78, 856, baseline=True, block="left")

    # Right employee block: name first, then the ID photo beside it.
    place_text(canvas, records, "RIGHT EMPLOYEE", "EMPLOYEE", label_font, MUTED,
               560, 270, spacing=3, block="right")
    photo_cx, photo_cy = 946, 322
    name_max = (photo_cx - 72) - 36 - 560
    agent_font, agent_size, agent_w = fit_font("YOUR AI AGENT", FONT_BOLD, 46, name_max)
    place_text(canvas, records, "YOUR AI AGENT", "YOUR AI AGENT", agent_font, INK,
               560, 298, block="right")
    place_text(canvas, records, "RIGHT JOB", "BOUNTY HUNTER", job_font, MUTED,
               560, 362, spacing=2, block="right")

    photo, ghost_h, head_480, gbox, ring_gap, badge_residual = build_photo(
        Image.open(GHOST_PATH).convert("RGBA"))
    canvas.paste(photo, (photo_cx - 72, photo_cy - 72), photo)

    right_rows = (("BOUNTIES ENTERED", "ALL"), ("BOUNTIES WON", "1"),
                  ("PAID VIA", "make.fun"))
    for i, (label, value) in enumerate(right_rows):
        y = 470 + 62 * i
        lb, _ = place_text(canvas, records, "RIGHT " + label, label, ledger_label,
                           MUTED, 560, y, block="right")
        vb, _ = place_text(canvas, records, "RIGHT VALUE " + value, value, ledger_value,
                           INK, 1002, y, align="right", block="right")
        dotted_leader(draw, lb[2] + 8, vb[0] - 8, y + 21)

    # Tinted net-pay panel, rubber stamp, then the right net pay.
    rounded_rect(draw, (546, 690, 1014, 880), 22, mix(PAPER, MAGENTA, 0.10))
    stamp = build_stamp()
    sx = int(round(890 - stamp.width / 2.0))
    sy = int(round(688 - stamp.height / 2.0))
    canvas.paste(stamp, (sx, sy), stamp)
    sb = stamp.getchannel("A").getbbox()
    stamp_box = (sx + sb[0], sy + sb[1], sx + sb[2], sy + sb[3])
    records.append({"name": "stamp overlay", "text": "<rotated stamp>",
                    "box": stamp_box, "block": "stamp", "overlay": True,
                    "size": 0, "ink_h": 0})

    place_text(canvas, records, "RIGHT NET PAY", "NET PAY", net_label, MUTED,
               560, 706, spacing=3, block="right")
    place_text(canvas, records, "RIGHT AMOUNT", "$500.00", big_font, MAGENTA,
               1002, 856, baseline=True, align="right", block="right")

    # Footer: the big line and the mixed-colour pitch on one centred line.
    footer_line = "SAME 13 YEARS. ONLY ONE OF US GOT PAID."
    foot_font, foot_size, foot_w = fit_font(footer_line, FONT_BOLD, 44, 900)
    place_text(canvas, records, "FOOTER LINE", footer_line, foot_font, INK,
               540, 930, align="center", block="footer")

    pitch1 = "make.fun"
    pitch2 = " - people and their AI agents earn real money in bounties."
    pitch_size = 28
    while pitch_size > 10:
        p1font = ImageFont.truetype(FONT_BOLD, pitch_size)
        p2font = ImageFont.truetype(FONT_SEMI, pitch_size)
        a1 = sum(p1font.getsize(ch)[0] for ch in pitch1)
        a2 = sum(p2font.getsize(ch)[0] for ch in pitch2)
        if a1 + a2 <= 900:
            break
        pitch_size -= 1
    assert pitch_size == 28, "pitch line had to shrink to %dpx" % pitch_size
    p1, a1, ix1, iy1 = text_piece(pitch1, p1font, MAGENTA)
    p2, a2, ix2, iy2 = text_piece(pitch2, p2font, PITCH_INK)
    total = a1 + a2
    start = (W - total) / 2.0
    baseline = 1000 + (p1font.getmetrics()[0] - iy1)
    px1 = int(round(start + ix1))
    py1 = int(round(baseline - p1font.getmetrics()[0] + iy1))
    canvas.paste(p1, (px1, py1), p1)
    records.append({"name": "PITCH make.fun", "text": pitch1,
                    "box": (px1, py1, px1 + p1.width, py1 + p1.height),
                    "block": "footer", "overlay": False, "size": pitch_size,
                    "ink_h": p1.height})
    px2 = int(round(start + a1 + ix2))
    py2 = int(round(baseline - p2font.getmetrics()[0] + iy2))
    canvas.paste(p2, (px2, py2), p2)
    records.append({"name": "PITCH rest", "text": pitch2,
                    "box": (px2, py2, px2 + p2.width, py2 + p2.height),
                    "block": "footer", "overlay": False, "size": pitch_size,
                    "ink_h": p2.height})

    out = os.path.join(HERE, "payslip.png")
    canvas.convert("RGB").save(out, optimize=True)
    preview = canvas.convert("RGB").resize((480, 480), Image.LANCZOS)
    preview.save(os.path.join(HERE, "payslip_480.png"), optimize=True)

    # Every string's ink box.
    print("TEXT BOXES (name, block, x0,y0,x1,y1, px size):")
    for r in records:
        b = r["box"]
        print("  %-22s %-7s (%4d,%4d)-(%4d,%4d) %3dpx%s"
              % (r["name"], r["block"], b[0], b[1], b[2], b[3], r["size"],
                 " overlay" if r["overlay"] else ""))

    # Column and overlap checks.
    flags = []
    for r in records:
        if r["overlay"]:
            continue
        b = r["box"]
        c = BLOCKS[r["block"]]
        if b[0] < c[0] - 1 or b[1] < c[1] - 1 or b[2] > c[2] + 1 or b[3] > c[3] + 1:
            flags.append("%s leaves %s column: %s" % (r["name"], r["block"], b))
    normal = [r for r in records if not r["overlay"]]

    def rec(name):
        return [r for r in records if r["name"] == name][0]

    for i in range(len(normal)):
        for j in range(i + 1, len(normal)):
            a, b = normal[i]["box"], normal[j]["box"]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 2 and oy > 2:
                flags.append("%s overlaps %s" % (normal[i]["name"], normal[j]["name"]))
    name_box = [r["box"] for r in records if r["name"] == "YOUR AI AGENT"][0]
    if name_box[2] > (photo_cx - 72) - 36:
        flags.append("YOUR AI AGENT does not clear the ID photo by 36px")
    amount_box = [r["box"] for r in records if r["name"] == "RIGHT AMOUNT"][0]
    if amount_box[0] < 546 or amount_box[2] > 1014 or amount_box[1] < 690 or amount_box[3] > 880:
        flags.append("$500.00 leaves the tinted net-pay panel")
    print("FLAGS:", "none" if not flags else str(len(flags)))
    for f in flags:
        print("  FLAG", f)

    # Stamp position, panel straddle, and ink clearance from every protected box.
    print("STAMP: 190x80, -11 deg, alpha 0.72, centre (890,688), ink bbox "
          "(%d,%d)-(%d,%d)" % stamp_box)
    assert stamp_box[1] < 690 < stamp_box[3], "stamp does not straddle panel top 690"
    stamp_checks = []
    for label, value in left_rows:
        stamp_checks.append(("ledger LEFT " + label,
                             union_box(rec("LEFT " + label)["box"],
                                       rec("LEFT VALUE " + value)["box"])))
    for label, value in right_rows:
        stamp_checks.append(("ledger RIGHT " + label,
                             union_box(rec("RIGHT " + label)["box"],
                                       rec("RIGHT VALUE " + value)["box"])))
    stamp_checks.append(("LEFT NET PAY label", rec("LEFT NET PAY")["box"]))
    stamp_checks.append(("RIGHT NET PAY label", rec("RIGHT NET PAY")["box"]))
    stamp_checks.append(("$500.00 box", rec("RIGHT AMOUNT")["box"]))
    for label, box in stamp_checks:
        gap = box_clearance(stamp_box, box)
        print("STAMP CLEARANCE %-24s %6.1f px" % (label, gap))
        assert gap >= 12, "stamp clearance to %s is only %.1f px" % (label, gap)

    # Name-to-disc gutter and photo clipping proof.
    disc_left = photo_cx - 72
    gutter = disc_left - name_box[2]
    print("NAME GUTTER: %d px (name ends %d, disc left edge %d)"
          % (gutter, name_box[2], disc_left))
    assert gutter >= 36, "name gutter is only %d px" % gutter
    print("PHOTO: 144 px disc at (%d,%d), right edge %d"
          % (photo_cx, photo_cy, photo_cx + 72))
    print("GHOST: %.1f px tall, head %.1f px wide at 480"
          % (ghost_h, head_480))
    print("GHOST CLIP: alpha bbox %s, ring gap %d px, badge residual %s"
          % (gbox, ring_gap, "none" if badge_residual is None else str(badge_residual)))
    assert ring_gap >= 8, "ghost ink is only %d px from the 4 px ring" % ring_gap
    assert badge_residual is None, "pale badge survives at %s" % (badge_residual,)
    assert head_480 >= 60, "ghost head is only %.1f px wide at 480" % head_480

    # 480-pixel type heights.
    print("480 TYPE HEIGHTS:")
    for name in ("PAYSLIP", "LEFT AMOUNT", "RIGHT AMOUNT", "FOOTER LINE"):
        r = rec(name)
        print("  %-12s %5.1f px at 480 (%.1f px at 1080)"
              % (r["text"], r["ink_h"] * 480.0 / 1080.0, r["ink_h"]))
    for label, _ in left_rows:
        lr = rec("LEFT " + label)
        vr = rec("LEFT VALUE " + dict(left_rows)[label])
        print("  ledger %-16s label %4.1f px, value %4.1f px, row %4.1f px at 480"
              % (label, lr["ink_h"] * 480.0 / 1080.0,
                 vr["ink_h"] * 480.0 / 1080.0, 62 * 480.0 / 1080.0))
    for label, _ in right_rows:
        lr = rec("RIGHT " + label)
        vr = rec("RIGHT VALUE " + dict(right_rows)[label])
        print("  ledger %-16s label %4.1f px, value %4.1f px, row %4.1f px at 480"
              % (label, lr["ink_h"] * 480.0 / 1080.0,
                 vr["ink_h"] * 480.0 / 1080.0, 62 * 480.0 / 1080.0))

    # The two net pay values must dominate, and the ghost must read at 480.
    net = [rec("LEFT AMOUNT"), rec("RIGHT AMOUNT")]
    others = [r for r in normal if r["name"] not in ("LEFT AMOUNT", "RIGHT AMOUNT")]
    assert min(r["ink_h"] for r in net) > max(r["ink_h"] for r in others), \
        "net pay values are not the largest type"
    assert 112 > max(r["size"] for r in others), "a non-net-pay line is larger than 112px"
    print("LARGEST TYPE: $0.00 and $500.00 at 112px, ink heights %d and %d px"
          % (net[0]["ink_h"], net[1]["ink_h"]))

    data = open(out, "rb").read()
    print("payslip.png: %dx%d, %d bytes" % (canvas.width, canvas.height, len(data)))
    print("payslip.png sha256:", hashlib.sha256(data).hexdigest())
    if flags:
        raise SystemExit("make_payslip.py: layout flags remain")


if __name__ == "__main__":
    main()
