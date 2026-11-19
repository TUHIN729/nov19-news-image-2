#!/usr/bin/env python3
"""news-image-20261119 entry 2: a one-day world-news poster for Thursday
19 November 2026, drawn from scratch with the Python standard library only.

Layout (1024 x 1024, rendered at 2x and downsampled for smooth edges):
  * navy masthead naming the day in huge type
  * one dominant hero story: the Trump-Xi-Putin trilateral talks in
    Shenzhen, with the three national flags drawn beside it
  * four numbered story rows covering the US-Iran exchange of fire,
    the GTA VI global rollout, Nvidia, and Voyager 1 plus the EU loan,
    the India-Japan 2+2 talks and the Fed minutes

The program writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
No network, no randomness, no timestamps: two runs are byte-identical.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024
SS = 2  # supersampling factor for smooth strokes

# ---------------------------------------------------------------- palette
NAVY = (11, 33, 68)
NAVY_TOP = (8, 26, 51)
NAVY_BOT = (15, 46, 92)
CREAM = (250, 243, 223)
WHITE = (255, 255, 255)
INK = (16, 32, 56)
RED = (193, 39, 45)
GOLD = (201, 162, 39)
GREY = (74, 84, 96)
ROW_ALT = (238, 242, 247)
TEAL = (14, 124, 123)
PURPLE = (91, 75, 138)
GREEN = (31, 107, 58)
FLAG_BLUE = (60, 59, 110)
FLAG_RED = (178, 34, 52)
CHINA_RED = (222, 41, 16)
CHINA_YELLOW = (255, 222, 0)
RUSSIA_BLUE = (0, 57, 166)
RUSSIA_RED = (213, 43, 30)

# ------------------------------------------------- stroke font (grid 8 x 12)
# Each glyph is a list of polylines; each polyline is "x,y x,y ...".
# Coordinates run x 0..8, y 0..12 (y down). All text is set in capitals.
GLYPHS = {
    "A": "0,12 4,0 8,12;2,8 6,8",
    "B": "1,12 1,0 6,0 8,2 8,4 6,6;6,6 8,8 8,10 6,12 1,12",
    "C": "8,2 6,0 2,0 0,2 0,10 2,12 6,12 8,10",
    "D": "1,12 1,0 6,0 8,3 8,9 6,12 1,12",
    "E": "8,0 0,0 0,12 8,12;0,6 6,6",
    "F": "0,12 0,0 8,0;0,6 6,6",
    "G": "8,2 6,0 2,0 0,2 0,10 2,12 6,12 8,10 8,6 5,6",
    "H": "0,0 0,12;8,0 8,12;0,6 8,6",
    "I": "4,0 4,12;1,0 7,0;1,12 7,12",
    "J": "8,0 8,10 6,12 2,12 0,10",
    "K": "0,0 0,12;8,0 0,6;2,7 8,12",
    "L": "0,0 0,12 8,12",
    "M": "0,12 0,0 4,7 8,0 8,12",
    "N": "0,12 0,0 8,12 8,0",
    "O": "2,0 6,0 8,2 8,10 6,12 2,12 0,10 0,2 2,0",
    "P": "0,12 0,0 6,0 8,2 8,5 6,7 0,7",
    "Q": "2,0 6,0 8,2 8,10 6,12 2,12 0,10 0,2 2,0;5,9 8,12",
    "R": "0,12 0,0 6,0 8,2 8,5 6,7 0,7;3,7 8,12",
    "S": "7,2 5,0 2,0 0,2 0,5 2,6 6,6 8,8 8,11 6,12 3,12 1,10",
    "T": "0,0 8,0;4,0 4,12",
    "U": "0,0 0,9 2,12 6,12 8,9 8,0",
    "V": "0,0 4,12 8,0",
    "W": "0,0 2,12 4,6 6,12 8,0",
    "X": "0,0 8,12;8,0 0,12",
    "Y": "0,0 4,6 8,0;4,6 4,12",
    "Z": "0,0 8,0 0,12 8,12",
    "0": "2,0 6,0 8,2 8,10 6,12 2,12 0,10 0,2 2,0",
    "1": "1,3 4,0 4,12;1,12 7,12",
    "2": "1,2 2,0 6,0 7,2 7,5 0,12 8,12",
    "3": "1,1 3,0 6,0 7,2 7,5 5,6;5,6 7,7 7,10 6,12 3,12 1,11",
    "4": "0,9 6,0 6,12;0,9 7,9",
    "5": "7,0 1,0 1,5 6,5 8,7 8,10 6,12 2,12 0,10",
    "6": "7,1 5,0 2,0 0,3 0,9 2,12 6,12 8,10 8,7 6,5 2,5 0,7",
    "7": "0,0 8,0 4,12",
    "8": "2,0 6,0 8,2 8,5 6,7 2,7 0,5 0,2 2,0;2,7 6,7 8,9 8,11 6,12 2,12 0,10 0,9",
    "9": "2,0 6,0 8,2 8,6 6,8 2,8 0,6 0,2 2,0;8,5 8,10 6,12 3,12",
    ".": "3,10 5,10 5,12 3,12 3,10",
    ",": "3,10 5,10 5,12 4,13 2,13",
    ":": "3,2 5,2 5,4 3,4 3,2;3,9 5,9 5,11 3,11 3,9",
    ";": "3,2 5,2 5,4 3,4 3,2;3,9 5,9 5,11 4,13 2,13",
    "-": "1,6 7,6",
    "'": "5,0 4,3",
    "(": "6,0 3,2 3,10 6,12",
    ")": "2,0 5,2 5,10 2,12",
    "/": "7,0 1,12",
    "%": "0,0 8,12;1,1 3,1 3,3 1,3 1,1;5,9 7,9 7,11 5,11 5,9",
    "+": "4,3 4,9;1,6 7,6",
    "=": "1,4 7,4;1,8 7,8",
    "!": "4,0 4,8;3,10 5,10 5,12 3,12 3,10",
    "?": "2,1 4,0 6,1 7,3 7,5 5,7 4,8 4,9;3,11 5,11 5,12 3,12 3,11",
}
# Advance width in grid units (default 9). Bullet is drawn as a disc.
NARROW = {".": 5, ",": 5, ":": 5, ";": 5, "'": 5, "!": 5, "?": 6,
           " ": 5, "-": 7, "(": 6, ")": 6, "/": 7, "1": 7}


def glyph_advance(ch):
    return NARROW.get(ch, 9)


def text_width(text, size):
    scale = size / 12.0
    return sum(glyph_advance(c) * scale for c in text)


def wrap_text(text, size, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, size) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ raster canvas
class Canvas:
    def __init__(self, w, h, ss):
        self.w, self.h, self.ss = w, h, ss
        self.px = bytearray(w * ss * h * ss * 3)

    def _set(self, x, y, color):
        if 0 <= x < self.w * self.ss and 0 <= y < self.h * self.ss:
            i = (y * self.w * self.ss + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def disc(self, cx, cy, r, color):
        r = int(math.ceil(r))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    self._set(int(cx) + dx, int(cy) + dy, color)

    def line(self, x0, y0, x1, y1, thick, color):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps if steps else 0.0
            self.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                      thick / 2.0, color)

    def rect(self, x, y, w, h, color):
        x, y, w, h = int(x * self.ss), int(y * self.ss), \
            int(w * self.ss), int(h * self.ss)
        for yy in range(y, y + h):
            base = (yy * self.w * self.ss + x) * 3
            for xx in range(w):
                i = base + xx * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def vgrad(self, x, y, w, h, top, bot):
        for row in range(int(h)):
            t = row / max(1, int(h) - 1)
            c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            self.rect(x, y + row, w, 1, c)

    def star(self, cx, cy, r, color):
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        self.polygon(pts, color)

    def polygon(self, pts, color):
        pts = [(p[0] * self.ss, p[1] * self.ss) for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self._set(xx, yy, color)

    def text(self, x, y, s, size, color, align="left"):
        """Draw text with its top-left at (x, y) in final pixels."""
        if align == "center":
            x -= text_width(s, size) / 2.0
        elif align == "right":
            x -= text_width(s, size)
        scale = size / 12.0
        thick = max(1.6, size * 0.085) * self.ss
        ox = x
        for ch in s:
            if ch == " ":
                ox += glyph_advance(ch) * scale
                continue
            if ch == "\u2022":  # bullet: solid disc
                self.disc((ox + 4 * scale) * self.ss,
                          (y + 6.5 * scale) * self.ss,
                          size * 0.16 * self.ss, color)
                ox += 9 * scale
                continue
            for poly in GLYPHS[ch].split(";"):
                pts = [tuple(map(float, p.split(","))) for p in poly.split(" ")]
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    self.line((ox + ax * scale) * self.ss,
                              (y + ay * scale) * self.ss,
                              (ox + bx * scale) * self.ss,
                              (y + by * scale) * self.ss, thick, color)
            ox += glyph_advance(ch) * scale

    def downsample_png(self):
        """Average each SS x SS block and encode a deterministic PNG."""
        sw, sh = self.w * self.ss, self.h * self.ss
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter: none
            for x in range(self.w):
                for c in range(3):
                    total = 0
                    for dy in range(self.ss):
                        for dx in range(self.ss):
                            i = ((y * self.ss + dy) * sw +
                                 (x * self.ss + dx)) * 3 + c
                            total += self.px[i]
                    raw.append(total // (self.ss * self.ss))
        comp = zlib.compress(bytes(raw), 9)

        def chunk(kind, data):
            out = struct.pack(">I", len(data)) + kind + data
            return out + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ------------------------------------------------------------------- flags
def draw_usa(c, x, y, w, h):
    stripe = h / 13.0
    for i in range(13):
        c.rect(x, y + i * stripe, w, stripe + 0.6,
               FLAG_RED if i % 2 == 0 else WHITE)
    cw, chh = w * 0.40, stripe * 7
    c.rect(x, y, cw, chh, FLAG_BLUE)
    for r in range(5):
        for col in range(6):
            sx = x + 10 + col * (cw - 18) / 5.0
            sy = y + 7 + r * (chh - 12) / 4.0
            c.disc(sx * SS, sy * SS, 2.2 * SS, WHITE)


def draw_china(c, x, y, w, h):
    c.rect(x, y, w, h, CHINA_RED)
    c.star(x + 34, y + 30, 15, CHINA_YELLOW)
    for sx, sy in ((72, 16), (88, 28), (88, 48), (72, 60)):
        c.star(x + sx, y + sy, 5, CHINA_YELLOW)


def draw_russia(c, x, y, w, h):
    c.rect(x, y, w, h / 3.0 + 0.6, WHITE)
    c.rect(x, y + h / 3.0, w, h / 3.0 + 0.6, RUSSIA_BLUE)
    c.rect(x, y + 2 * h / 3.0, w, h / 3.0 + 0.6, RUSSIA_RED)


# -------------------------------------------------------------------- poster
def build():
    c = Canvas(W, H, SS)
    c.rect(0, 0, W, H, WHITE)

    # Masthead: navy gradient, gold rules, the day in huge type.
    c.vgrad(0, 0, W, 148, NAVY_TOP, NAVY_BOT)
    c.text(W / 2, 12, "THURSDAY - THE WORLD IN ONE IMAGE", 18, GOLD,
           align="center")
    c.text(W / 2, 48, "19 NOVEMBER 2026", 72, WHITE, align="center")
    c.rect(48, 138, W - 96, 3, GOLD)

    # Hero: warm cream panel, one dominant story.
    c.rect(0, 148, W, 404, CREAM)
    c.text(48, 170, "APEC SUMMIT - SHENZHEN, CHINA", 24, RED)
    c.text(48, 200, "TRUMP, XI AND", 58, INK)
    c.text(48, 276, "PUTIN MEET IN", 58, INK)
    c.text(48, 352, "SHENZHEN", 58, RED)
    c.text(48, 462, "TRILATERAL TALKS AT THE APEC SUMMIT", 23, INK)
    c.text(48, 492, "XI MET PUTIN FIRST, THEN TRUMP ARRIVED", 20, GREY)
    c.rect(48, 540, 560, 3, GOLD)

    # The three flags, each with a caption bar.
    fx, fw, fh = 672, 304, 88
    for i, (draw, name) in enumerate(
            ((draw_usa, "UNITED STATES"), (draw_china, "CHINA"),
             (draw_russia, "RUSSIA"))):
        fy = 178 + i * 114
        draw(c, fx, fy, fw, fh)
        c.rect(fx, fy + fh, fw, 24, NAVY)
        c.text(fx + fw / 2, fy + fh + 4, name, 16, WHITE, align="center")

    # Four numbered story rows.
    rows = [
        (RED, "1", "US AND IRAN EXCHANGE FIRE",
         "US STRIKES A MISSILE SITE ON QESHM ISLAND. IRAN HITS A US BASE "
         "IN KUWAIT AND STRIKES BAHRAIN AGAIN."),
        (TEAL, "2", "GTA VI ROLLS OUT WORLDWIDE",
         "GAMERS RETURN TO VICE CITY AS THE GLOBAL LAUNCH BEGINS, WITH "
         "NEAR-PERFECT REVIEWS."),
        (PURPLE, "3", "NVIDIA HALTS CHINA CHIP SHIPMENTS",
         "ACTING CHIEF COLETTE KRESS PROMISES EARLIER PAY RAISES AND MORE "
         "STOCK GRANTS."),
        (GREEN, "4", "VOYAGER 1 PASSES ONE LIGHT-DAY",
         "PLUS: EU 45 BILLION EURO UKRAINE LOAN. INDIA-JAPAN 2+2 IN "
         "TOKYO. FED: MORE HIKES LIKELY."),
    ]
    y0, rh = 552, 118
    for i, (chip, num, head, sub) in enumerate(rows):
        ry = y0 + i * rh
        if i % 2 == 1:
            c.rect(0, ry, W, rh, ROW_ALT)
        c.rect(32, ry + 15, 88, 88, chip)
        c.text(76, ry + 33, num, 56, WHITE, align="center")
        c.text(144, ry + 14, head, 33, INK)
        lines = wrap_text(sub, 22, W - 144 - 24)
        for j, line in enumerate(lines[:2]):
            c.text(144, ry + 56 + j * 27, line, 22, GREY)
    return c.downsample_png()


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = build()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
