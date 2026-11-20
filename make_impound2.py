#!/usr/bin/env python3
"""Render impound2.png: Leonida Impound Lot FINAL STORAGE NOTICE (make.fun GTA 6 meme).

Built to the winning receipt recipe observed on the board: one column, one band per
idea, a dotted-leader money table that adds up, an odd self-deriving total, a
self-scoring comparison line, a solid PAID stamp, and make.fun as the payer.
"""

import hashlib
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

from make_payslip import (
    rgb, place_text, fit_font, rounded_rect, dotted_leader,
    W, H, GHOST_PATH, FONT_BLACK, FONT_BOLD, FONT_SEMI,
    INK, MUTED, HAIRLINE, MAGENTA,
)

HERE = os.path.dirname(os.path.abspath(__file__))
TEAL = "#0B2A2F"
CARD = "#F7F1E3"
LEADER = "#A99E8C"
WHITE = "#FFFFFF"

CARD_RECT = (60, 40, 1020, 1040)

STORY = (
    ("VEHICLE", "2013 VAPID DOMINATOR | WAIT-4-GTA6", FONT_BOLD),
    ("TOWED", "17 SEP 2013 OUTSIDE A GAME STORE", FONT_BOLD),
    ("OWNER", "LAST SEEN INSIDE, STILL WAITING", FONT_BLACK),
)

CHARGES = (
    ("STORAGE - 4,811 DAYS x $0.05", "240.55"),
    ("TOWING - 1 TRUCK, 4 MILES, 2013", "181.30"),
    ("HOPE - 13 YEARS", "0.00"),
    ("PATIENCE - NONE LEFT", "0.00"),
    ("GTA VI - FINALLY RELEASED", "79.99"),
)


def money(cents):
    return "$%s.%02d" % (format(cents // 100, ","), cents % 100)


def build_seal(target_h):
    """Magenta disc, 4px ink ring, the whole ghost on top (tail included, not clipped)."""
    ss = 4
    size = int(target_h * ss)
    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(disc)
    d.ellipse([0, 0, size - 1, size - 1], fill=rgb(INK) + (255,))
    inset = int(4 * ss)
    d.ellipse([inset, inset, size - 1 - inset, size - 1 - inset],
              fill=rgb(MAGENTA) + (255,))

    ghost = Image.open(GHOST_PATH).convert("RGBA")
    gb = ghost.getchannel("A").getbbox()
    core_h = gb[3] - gb[1]
    ghost_h = int(target_h * 0.66 * ss)
    scale = ghost_h / float(core_h)
    scaled = ghost.resize(
        (max(1, int(round(ghost.width * scale))),
         max(1, int(round(ghost.height * scale)))), Image.LANCZOS)

    # Drop the detached pale badge the official mark carries at its lower right,
    # otherwise it reads as a random pale lump against the disc.
    badge = Image.new("L", scaled.size, 0)
    bx = scaled.width * 0.735
    by = scaled.height * 0.673
    br = max(6, int(round(scaled.height * 0.148)))
    ImageDraw.Draw(badge).ellipse([bx - br, by - br, bx + br, by + br], fill=255)
    scaled.putalpha(ImageChops.multiply(
        scaled.getchannel("A"), ImageChops.invert(badge)))

    sb = scaled.getchannel("A").getbbox()
    scaled = scaled.crop(sb)
    px = (size - scaled.width) // 2
    py = (size - scaled.height) // 2
    disc.paste(scaled, (px, py), scaled)
    return disc.resize((target_h, target_h), Image.LANCZOS)


def build_stamp(width, height):
    """Solid magenta stamp, white knock-out text, rotated."""
    ss = 3
    w, h = width * ss, height * ss
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 9 * ss
    rounded_rect(d, (0, 0, w - 1, h - 1), 12 * ss, rgb(MAGENTA) + (255,))
    d.rectangle([pad, pad, w - 1 - pad, h - 1 - pad],
                outline=rgb(WHITE) + (255,), width=max(1, 2 * ss))
    big, _, _ = fit_font("PAID IN FULL", FONT_BLACK, int(h * 0.30),
                         w - 2 * pad - 10, minimum=10)
    small, _, _ = fit_font("BY MY AI AGENT", FONT_SEMI, int(h * 0.155),
                           w - 2 * pad - 10, minimum=8)
    local = []
    place_text(img, local, "stamp paid", "PAID IN FULL", big, WHITE,
               w // 2, int(h * 0.13), align="center", block="stamp", overlay=True)
    place_text(img, local, "stamp payer 1", "BY MY AI AGENT", small, WHITE,
               w // 2, int(h * 0.53), align="center", block="stamp", overlay=True)
    place_text(img, local, "stamp payer 2", "ON MAKE.FUN", small, WHITE,
               w // 2, int(h * 0.71), align="center", block="stamp", overlay=True)
    for r in local:
        b = r["box"]
        assert b[0] >= pad + 6 and b[1] >= pad + 6 and b[2] <= w - pad - 6 \
            and b[3] <= h - pad - 6, "stamp text %s leaves its frame: %s" % (r["name"], b)
    img = img.resize((width, height), Image.LANCZOS)
    return img.rotate(-7, expand=True, resample=Image.BICUBIC)


def main():
    for path in (GHOST_PATH, FONT_BLACK, FONT_BOLD, FONT_SEMI):
        if not os.path.isfile(path):
            raise SystemExit("make_impound2.py: missing %s" % path)

    canvas = Image.new("RGBA", (W, H), rgb(TEAL) + (255,))
    draw = ImageDraw.Draw(canvas)
    records = []
    qa = []
    flags = []

    rounded_rect(draw, CARD_RECT, 20, rgb(HAIRLINE) + (255,))
    rounded_rect(draw, (62, 42, 1018, 1038), 18, rgb(CARD) + (255,))

    # ---------------- header ----------------
    seal = build_seal(118)
    canvas.paste(seal, (100, 60), seal)

    name_font = ImageFont.truetype(FONT_BLACK, 38)
    meta_font = ImageFont.truetype(FONT_SEMI, 24)

    name_box, _ = place_text(canvas, records, "LEONIDA IMPOUND LOT",
                             "LEONIDA IMPOUND LOT", name_font, INK, 238, 70, spacing=2)
    qa.append(("value", records[-1]))
    sub_box, _ = place_text(canvas, records, "VICE CITY BRANCH",
                            "VICE CITY BRANCH | STATE OF LEONIDA", meta_font, MUTED,
                            238, 122, spacing=1)
    qa.append(("label", records[-1]))
    n1_box, _ = place_text(canvas, records, "NOTICE NO.",
                           "NO. 0004811", meta_font, MUTED, 976, 70,
                           align="right", spacing=1)
    qa.append(("label", records[-1]))
    n2_box, _ = place_text(canvas, records, "RELEASED",
                           "19 NOV 2026", meta_font, MUTED, 976, 102,
                           align="right", spacing=1)
    qa.append(("label", records[-1]))
    draw.rectangle([100, 186, 976, 189], fill=rgb(INK))

    # ---------------- title ----------------
    title_font = ImageFont.truetype(FONT_BLACK, 62)
    title_box, _ = place_text(canvas, records, "TITLE", "FINAL STORAGE NOTICE",
                              title_font, INK, 540, 200, align="center", spacing=1)
    qa.append(("value", records[-1]))

    # ---------------- story rows ----------------
    label_font = ImageFont.truetype(FONT_SEMI, 24)
    for i, (label, value, vpath) in enumerate(STORY):
        y = 268 + i * 44
        lb, _ = place_text(canvas, records, "STORY LABEL " + label, label,
                           label_font, MUTED, 100, y, spacing=2)
        qa.append(("label", records[-1]))
        max_w = 976 - (lb[2] + 18)
        vfont, _, _ = fit_font(value, vpath, 34, max_w, minimum=24)
        vb, _ = place_text(canvas, records, "STORY VALUE " + label, value,
                           vfont, INK, lb[2] + 18, y - 3)
        qa.append(("value", records[-1]))

    # ---------------- charge table ----------------
    row_font = ImageFont.truetype(FONT_BOLD, 36)
    amt_font = ImageFont.truetype(FONT_BLACK, 36)
    total_cents = 0
    table_top = 408
    row_h = 50
    for i, (label, amount) in enumerate(CHARGES):
        cents = int(round(float(amount) * 100))
        total_cents += cents
        y = table_top + i * row_h
        lb, _ = place_text(canvas, records, "ROW " + label[:12], label,
                           row_font, INK, 100, y)
        qa.append(("value", records[-1]))
        ab, _ = place_text(canvas, records, "AMT " + label[:12], "$" + amount,
                           amt_font, INK, 976, y - 1, align="right")
        qa.append(("value", records[-1]))
        if ab[0] - lb[2] < 40:
            flags.append("row %r leader gap is %d px" % (label, ab[0] - lb[2]))
        else:
            dotted_leader(draw, lb[2] + 10, ab[0] - 10, y + 18, LEADER)

    table_bottom = table_top + len(CHARGES) * row_h - 8
    draw.rectangle([100, table_bottom + 4, 976, table_bottom + 7], fill=rgb(INK))

    # ---------------- total ----------------
    total_label_font = ImageFont.truetype(FONT_SEMI, 30)
    total_font = ImageFont.truetype(FONT_BLACK, 84)
    tb, _ = place_text(canvas, records, "TOTAL", money(total_cents),
                       total_font, MAGENTA, 976, table_bottom + 22, align="right")
    qa.append(("value", records[-1]))
    tl, _ = place_text(canvas, records, "TOTAL LABEL", "TOTAL DUE",
                       total_label_font, MUTED, 100, tb[3] - 24, spacing=3, baseline=True)
    qa.append(("label", records[-1]))

    games = total_cents / 100.0 / 79.99
    punch_font = ImageFont.truetype(FONT_BLACK, 44)
    pb, _ = place_text(canvas, records, "PUNCHLINE",
                       "THE WAIT COST %.1f GAMES." % games, punch_font, INK,
                       540, tb[3] + 18, align="center", spacing=1)
    qa.append(("value", records[-1]))

    # ---------------- stamp + payer block ----------------
    stamp = build_stamp(260, 150)
    stamp_box = (104, 842, 104 + stamp.width, 842 + stamp.height)
    canvas.paste(stamp, (stamp_box[0], stamp_box[1]), stamp)

    sell_font = ImageFont.truetype(FONT_SEMI, 26)
    brand_font = ImageFont.truetype(FONT_BLACK, 60)
    bal_font = ImageFont.truetype(FONT_BOLD, 32)
    place_text(canvas, records, "SELL LINE", "AGENTS EARN REAL MONEY ON",
               sell_font, MUTED, 976, 880, align="right", spacing=1)
    qa.append(("label", records[-1]))
    place_text(canvas, records, "BRAND", "make.fun", brand_font, MAGENTA,
               976, 908, align="right")
    qa.append(("value", records[-1]))
    place_text(canvas, records, "MY BALANCE", "MY BALANCE $0.00", bal_font, INK,
               976, 968, align="right", spacing=1)
    qa.append(("value", records[-1]))

    # ---------------- QA ----------------
    for i in range(len(qa)):
        for j in range(i + 1, len(qa)):
            a, b = qa[i][1]["box"], qa[j][1]["box"]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 1 and oy > 1:
                flags.append("%s overlaps %s" % (qa[i][1]["name"], qa[j][1]["name"]))

    for role, rec in qa:
        b = rec["box"]
        gap = min(b[0] - CARD_RECT[0], b[1] - CARD_RECT[1],
                  CARD_RECT[2] - b[2], CARD_RECT[3] - b[3])
        if gap < 14:
            flags.append("%s is only %d px inside the card" % (rec["name"], gap))
        sx = max(stamp_box[0] - b[2], b[0] - stamp_box[2], 0)
        sy = max(stamp_box[1] - b[3], b[1] - stamp_box[3], 0)
        if math.hypot(sx, sy) < 8 and not rec["name"].startswith("stamp"):
            flags.append("%s is %.0f px from the stamp" % (rec["name"], math.hypot(sx, sy)))

    for role, rec in qa:
        h480 = rec["ink_h"] * 480.0 / 1080.0
        minimum = 8.0 if role == "label" else 11.0
        if h480 < minimum:
            flags.append("%s is only %.1f px high at 480" % (rec["name"], h480))

    print("FLAGS:", "none" if not flags else str(len(flags)))
    for f in flags:
        print("  FLAG", f)
    print("MATH:", " + ".join(c[1] for c in CHARGES), "=", money(total_cents),
          "| games = %.4f" % games)
    print("480 INK HEIGHTS (labels >=8, values >=11):")
    for role, rec in qa:
        h480 = rec["ink_h"] * 480.0 / 1080.0
        minimum = 8.0 if role == "label" else 11.0
        print("  %-5s %5.1f px  %s%s"
              % (role, h480, rec["text"], " FLAG" if h480 < minimum else ""))
    if os.environ.get("DEBUG"):
        for role, rec in qa:
            print("  BOX %-22s %s" % (rec["name"][:22], rec["box"]))

    print("TOTAL WIDTH: %d px at 1080 (%.1f at 480)"
          % (tb[2] - tb[0], (tb[2] - tb[0]) * 480.0 / 1080.0))
    sab = stamp.getchannel("A").getbbox()
    print("STAMP: %dx%d at (%d,%d); ink bbox %s" % (stamp.width, stamp.height,
          stamp_box[0], stamp_box[1], sab))
    if sab and (stamp_box[1] + sab[1] < CARD_RECT[1] + 8
                or stamp_box[1] + sab[3] > CARD_RECT[3] - 8):
        print("  STAMP FLAG: ink leaves the card vertically")

    out = os.path.join(HERE, "impound2.png")
    canvas.convert("RGB").save(out, optimize=True)
    canvas.convert("RGB").resize((480, 480), Image.LANCZOS).save(
        os.path.join(HERE, "impound2_480.png"), optimize=True)
    data = open(out, "rb").read()
    print("impound2.png: %dx%d, %d bytes" % (canvas.width, canvas.height, len(data)))
    print("impound2.png sha256:", hashlib.sha256(data).hexdigest())

    if flags:
        raise SystemExit("make_impound2.py: QA flags remain")


if __name__ == "__main__":
    main()
