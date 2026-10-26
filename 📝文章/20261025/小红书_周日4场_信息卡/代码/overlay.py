# -*- coding: utf-8 -*-
"""在给定底图上加文字（日期 + 赛事信息），不改底图。

底图 = 用户提供/已确认的赛博海报图；本脚本只做「贴文字」：
  3:4  -> 左下角一块比赛信息面板（4 场）+ 顶部日期签
  16:9 -> 标题下方一块两列比赛信息面板（6 场）+ 日期签

用法：
  python -X utf8 scripts/cover/overlay.py --base X/base_3x4.png --out X/封面_3x4.png --ratio 3:4
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SKINS = {
    "neon": (0, 240, 120), "cyan": (34, 211, 255), "violet": (178, 107, 255),
    "amber": (255, 176, 32), "ice": (92, 225, 230),
}
SKIN_ORDER = ["neon", "cyan", "violet", "amber", "ice"]
GREEN = (0, 240, 120)
WHITE = (238, 245, 255)
MUTED = (143, 163, 183)
PANEL = (5, 12, 18, 205)
EDGE = (0, 240, 120, 235)

FONT_DIR = Path(r"C:\Windows\Fonts")
BOLD = FONT_DIR / "msyhbd.ttc"
REG = FONT_DIR / "msyh.ttc"
MONO = FONT_DIR / "consola.ttf"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.truetype(str(BOLD), size)


DEFAULT_MATCHES = [
    ("13:00", "韩职", "首尔FC", "江原FC"),
    ("14:00", "日职", "神户胜利", "町田泽维"),
    ("19:30", "英超", "维拉", "曼城"),
    ("21:00", "意甲", "科莫", "萨索洛"),
    ("22:00", "英超", "阿森纳", "埃弗顿"),
    ("00:00", "意甲", "那不勒斯", "罗马"),
]


def rounded(draw: ImageDraw.ImageDraw, box, r: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def draw_chip(draw: ImageDraw.ImageDraw, xy, text: str, fs: int) -> int:
    f = font(BOLD, fs)
    pad_x, pad_y = fs * 0.80, fs * 0.40
    tw = draw.textlength(text, font=f)
    x, y = xy
    box = (x, y, x + tw + pad_x * 2, y + fs + pad_y * 2)
    rounded(draw, box, int(fs * 0.42), (0, 240, 120, 26), EDGE, 2)
    draw.text((x + pad_x, y + pad_y - fs * 0.08), text, font=f, fill=GREEN)
    return int(box[2] - x)


def retag_band(im, ratio: str, tags=("数据拆解", "赛况分析", "数据整理", "风险提示")) -> None:
    """把底图上烧死的标签行遮掉，按同一位置重写（去掉「赛果预测」）。"""
    W, H = im.size
    if ratio == "3:4":
        y0, y1 = int(H * 0.428), int(H * 0.492)
        x0 = int(W * 0.058)
        fs = int(W * 0.040)
    else:
        y0, y1 = int(H * 0.622), int(H * 0.696)
        x0 = int(W * 0.055)
        fs = int(W * 0.030)
    band = Image.new("RGBA", (W, y1 - y0), (5, 12, 18, 0))
    bd = ImageDraw.Draw(band)
    hgt = y1 - y0
    for i in range(hgt):
        a = int(150 + 100 * (1 - abs(i - hgt / 2) / (hgt / 2)) ** 0.6)
        bd.line([(0, i), (W, i)], fill=(5, 12, 18, a))
    im.alpha_composite(band, (0, y0))
    d = ImageDraw.Draw(im)
    f = font(BOLD, fs)
    x, y = x0, y0 + (hgt - fs) // 2 - int(fs * 0.08)
    for i, t in enumerate(tags):
        d.text((x, y), t, font=f, fill=WHITE)
        x += int(d.textlength(t, font=f))
        if i < len(tags) - 1:
            d.text((x + int(fs * 0.32), y), "/", font=f, fill=GREEN)
            x += int(fs * 0.32) + int(d.textlength("/", font=f)) + int(fs * 0.30)


def build(base: Path, out: Path, ratio: str, date: str, weekday: str, matches, k: float = 1.0, rows_n: int = 0, skip: int = 0, retag: bool = False) -> None:
    im = Image.open(base).convert("RGBA")
    if retag:
        retag_band(im, ratio)
    w, h = im.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    matches = matches[skip:]

    if ratio == "3:4":
        # ---- 日期签 ----
        if k >= 1.8:
            draw_chip(d, (int(w * 0.045), int(h * 0.560)), f"{date}  {weekday}", int(w * 0.030 * k))
        else:
            draw_chip(d, (int(w * 0.050), int(h * 0.128)), f"{date}  {weekday}", max(24, int(w * 0.034 * k)))

        # ---- 比赛信息面板（左下，单行一场）----
        rows = matches[:(rows_n or (2 if k >= 1.8 else (3 if k >= 1.3 else 4)))]
        if len(rows) > 5:
            k = k * (5.0 / len(rows)) ** 0.6
        fs_t, fs_n, fs_l = int(w * 0.024 * k), int(w * 0.029 * k), int(w * 0.018 * k)
        pad = int(w * 0.020)
        pw = int(w * (0.470 if k < 1.3 else (0.720 if k < 1.8 else 0.905)))
        row_h = int(fs_n * 1.85)
        ph = row_h * len(rows) + pad * 2
        px = int(w * 0.028)
        py = int(h * (0.655 if k < 1.3 else (0.628 if k < 1.8 else 0.600)))
        if len(rows) > 5:
            py = int(h * 0.588)
        rounded(d, (px, py, px + pw, py + ph), int(w * 0.016), PANEL, EDGE, 2)
        d.rectangle((px, py + 8, px + 5, py + ph - 8), fill=EDGE)

        fy = py + pad
        x_t = px + pad + 8
        x_l = px + int(pw * (0.245 if k < 1.3 else (0.205 if k < 1.8 else 0.160)))
        x_n = px + int(pw * (0.355 if k < 1.3 else (0.335 if k < 1.8 else 0.272)))
        for t, lg, hm, aw in rows:
            ty = fy + int((row_h - fs_n) / 2) + 1
            d.text((x_t, ty + 2), t, font=font(MONO, fs_t), fill=GREEN)
            d.text((x_l, ty + 3), lg, font=font(REG, fs_l), fill=MUTED)
            d.text((x_n, ty), f"{hm}  vs  {aw}", font=font(BOLD, fs_n), fill=WHITE)
            fy += row_h

    else:
        # ---- 单行信息条：日期 + 焦点场次（压在副标题与卖点条之间）----
        sep = "  ｜  "
        fs = max(18, int(w * (0.0235 if k < 1.8 else 0.0205) * k))
        px = int(w * 0.022)
        limit = w - 2 * px - 16
        hpad = int(fs * 0.9)
        vpad = int(fs * (0.35 if k >= 1.15 else 0.6))
        f_r = font(REG, fs)

        def build_lines(items, two_rows):
            groups = [items] if not two_rows else [items[:1], items[1:]]
            lines = []
            for gi, grp in enumerate(groups):
                if not grp:
                    continue
                pieces = []
                if gi == 0:
                    pieces.append((f"{date} {weekday}", GREEN, font(BOLD, fs)))
                for t, lg, hm, aw in grp:
                    pieces.append((t, GREEN, font(MONO, fs)))
                    pieces.append((f"{hm} vs {aw}", WHITE, font(BOLD, fs)))
                lines.append(pieces)
            widest = 0
            for pieces in lines:
                wsum = (sum(d.textlength(txt, font=f) for txt, _, f in pieces)
                        + d.textlength(sep, font=f_r) * (len(pieces) - 1))
                widest = max(widest, wsum)
            return lines, widest

        picks = matches[:(rows_n or (1 if k >= 1.8 else 3))]
        two_rows = False
        lines, widest = build_lines(picks, two_rows)
        while widest + hpad * 2 > limit and picks:
            picks = picks[:-1]
            if not picks:
                break
            lines, widest = build_lines(picks, two_rows)

        lh = int(fs * (1.55 if k >= 1.15 else 1.85))
        ph = lh * len(lines) + vpad
        py = int(h * (0.698 if k < 1.8 else 0.625))
        pw = int(widest + hpad * 2)
        rounded(d, (px, py, px + pw, py + ph), int(fs * 0.5), PANEL, EDGE, 2)
        d.rectangle((px, py + 6, px + 4, py + ph - 6), fill=EDGE)
        y = py + vpad // 2
        for pieces in lines:
            x = px + hpad
            for i, (txt, color, f) in enumerate(pieces):
                if i:
                    d.text((x, y + fs * 0.1), sep, font=f_r, fill=MUTED)
                    x += d.textlength(sep, font=f_r)
                d.text((x, y), txt, font=f, fill=color)
                x += d.textlength(txt, font=f)
            y += lh

    im = Image.alpha_composite(im, layer).convert("RGB")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=95)
    print(f"✅ {out.name}  {im.size[0]}x{im.size[1]}  {out.stat().st_size // 1024}KB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ratio", choices=["3:4", "16:9"], default="3:4")
    ap.add_argument("--date", default="10.24")
    ap.add_argument("--weekday", default="周六")
    ap.add_argument("--font-scale", type=float, default=1.0)
    ap.add_argument("--rows", type=int, default=0, help="封面上列几场（0=默认）")
    ap.add_argument("--skip", type=int, default=0, help="从第几场开始取")
    ap.add_argument("--skin", default="")
    ap.add_argument("--matches", default="", help="时间|联赛|主队|客队;... 覆盖默认赛程")
    ap.add_argument("--retag", action="store_true",
                    help="遮掉底图上的标签行并改写（去掉「赛果预测」）")
    a = ap.parse_args()
    global DEFAULT_MATCHES
    if a.matches.strip():
        rows = []
        for part in a.matches.split(";"):
            part = part.strip()
            if not part:
                continue
            t, lg, hm, aw = [x.strip() for x in part.split("|")]
            rows.append((t, lg, hm, aw))
        DEFAULT_MATCHES = rows
    if a.skin in SKINS:
        globals()["GREEN"] = SKINS[a.skin]
    else:
        digits = "".join(ch for ch in str(a.date) if ch.isdigit())
        key = SKIN_ORDER[(int(digits) if digits else 0) % len(SKIN_ORDER)]
        globals()["GREEN"] = SKINS[key]
    build(Path(a.base), Path(a.out), a.ratio, a.date, a.weekday, DEFAULT_MATCHES, a.font_scale, a.rows, a.skip, a.retag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
