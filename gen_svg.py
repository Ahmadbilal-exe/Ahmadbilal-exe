"""Generates dark_mode.svg / light_mode.svg (portrait = colored ASCII art of avatar.png).
today.py later fills in the live numbers. Re-run this only when you change text or the picture."""
from PIL import Image, ImageEnhance

SRC = "avatar_cut.png"          # made by make_cutout.py (character only, no background)
COLS, ROWS = 72, 36                  # char cell is 6x12 px -> square portrait of 384x384
RAMP = " .*()%#$@"                    # light -> dense, classic ASCII symbols
W = 63                               # characters per text line
HALF = 30                            # width of each stats column
X_TXT, LH = 470, 20
ART_FONT, ART_CW, ART_LH = 10, 6, 12

THEMES = {
    "dark_mode.svg":  dict(bg="#0d1117", panel="#0a1a33", text="#c9d1d9", title="#7ee787", head="#d2a8ff", key="#ffa657", value="#a5d6ff", cc="#484f58"),
    "light_mode.svg": dict(bg="#f6f8fa", panel="#0a1a33", text="#24292f", title="#1a7f37", head="#8250df", key="#953800", value="#0a3069", cc="#afb8c1"),
}

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

def _rgb(h): return [int(h[i:i+2], 16) for i in (1, 3, 5)]
def dim(h): return "#%02x%02x%02x" % tuple(int(v * 0.62) for v in _rgb(h))
def lighten(h): return "#%02x%02x%02x" % tuple(min(255, int(v * 1.25) + 25) for v in _rgb(h))

def portrait():
    """Rows of runs [(color_or_None, text)]; None = transparent background cells (spaces)."""
    src = Image.open(SRC).convert("RGBA")
    rgb = ImageEnhance.Color(ImageEnhance.Contrast(src.convert("RGB")).enhance(1.25)).enhance(1.25)
    rgb = rgb.resize((COLS, ROWS), Image.LANCZOS)
    alpha = src.getchannel("A").resize((COLS, ROWS), Image.BOX)
    q = lambda v: min(255, int(round(v / 16)) * 16)
    rows = []
    for y in range(ROWS):
        cells = []
        for x in range(COLS):
            if alpha.getpixel((x, y)) < 110:
                cells.append((None, " "))
                continue
            r, g, b = rgb.getpixel((x, y))
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            ch = RAMP[min(int((lum ** 0.8) * len(RAMP)), len(RAMP) - 1)]
            cells.append(("#%02x%02x%02x" % (q(min(255, r * 1.15)), q(min(255, g * 1.15)), q(min(255, b * 1.15))), ch))
        runs = []
        for col, ch in cells:
            if runs and runs[-1][0] == col:
                runs[-1] = (col, runs[-1][1] + ch)
            else:
                runs.append((col, ch))
        rows.append(runs)
    return rows

def dots(n):
    return " " + "." * (n - 2) + " " if n >= 2 else " " * max(n, 0)

def kv(key, val, width=W, did=None, vid=None):
    d = dots(width - len(key) - 1 - len(val))
    did_a = f' id="{did}"' if did else ""
    vid_a = f' id="{vid}"' if vid else ""
    return (f'<tspan class="key">{esc(key)}</tspan>:<tspan class="cc"{did_a}>{d}</tspan>'
            f'<tspan class="value"{vid_a}>{esc(val)}</tspan>')

def section(title):
    return f'<tspan class="head">{esc(title)}</tspan> <tspan class="cc">' + "-" * (W - len(title) - 1) + "</tspan>"

def stats(l, r):
    return kv(*l[:2], HALF, l[2], l[3]) + '<tspan class="cc"> | </tspan>' + kv(*r[:2], HALF, r[2], r[3])

LINES = [
    f'<tspan class="title">Ahmadbilal-exe</tspan>',
    "",
    section("Profile"),
    kv("Name", "Ahmad Bilal"),
    kv("Uptime", "0 years, 0 months, 0 days", W, "age_dots", "age_data"),
    kv("Host", "FAST NUCES PESHAWAR"),
    kv("Role", "BSCS Student"),
    "",
    section("Tech"),
    kv("Languages", "C, C++, Kotlin, HTML, CSS, JS, Firebase"),
    kv("Technologies", "Android Studio, VS Code, Qt Creator"),
    kv("Projects", "MiniDB, PayCircle, Donor System"),
    "",
    section("Contact"),
    kv("Portfolio", "ahmadbilal-exe.vercel.app"),
    kv("Insta", "ahmadbilal.exe"),
    kv("LinkedIn", "ahmad-bilal-14a5b4373"),
    "",
    section("GitHub Stats"),
    stats(("Followers", "0", "follower_dots", "follower_data"), ("Stars", "0", "star_dots", "star_data")),
    stats(("Contributions", "0", "contrib_dots", "contrib_data"), ("Repos", "0", "repo_dots", "repo_data")),
    stats(("Commits", "0", "commit_dots", "commit_data"), ("Lines of Code", "0", "loc_dots", "loc_data")),
]

art = portrait()
H = 40 + len(LINES) * LH + 10
PW, PH = COLS * ART_CW + 24, ROWS * ART_LH + 24
PX, PY = 18, (H - PH) // 2
WIDTH = X_TXT + W * 9 + 25

for fname, c in THEMES.items():
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{WIDTH}px" height="{H}px" font-size="15px">',
         "<style>",
         "@font-face{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';font-display:swap;-webkit-size-adjust:109%;size-adjust:109%;}",
         f".title{{fill:{c['title']};font-weight:bold;font-size:18px;}} .head{{fill:{c['head']};font-weight:bold;}} .key{{fill:{c['key']};}} .value{{fill:{c['value']};}} .cc{{fill:{c['cc']};}}",
         "text,tspan{white-space:pre;}",
         "</style>",
         f'<rect width="{WIDTH}px" height="{H}px" fill="{c["bg"]}" rx="15"/>',
         ]
    for i, runs in enumerate(art):
        x = PX + 12
        for col, t in runs:
            w = ART_CW * len(t)
            if col:
                o.append(f'<rect x="{x}" y="{PY + 12 + i * ART_LH}" width="{w}" height="{ART_LH}" fill="{dim(col)}"/>')
            x += w
    o.append(f'<text font-family="DejaVu Sans Mono,Consolas,monospace" font-size="{ART_FONT}px" xml:space="preserve">')
    for i, runs in enumerate(art):
        y = PY + 12 + ART_LH * (i + 1) - 3
        spans = "".join((f'<tspan fill="{lighten(col)}">{esc(t)}</tspan>' if col else t) for col, t in runs)
        o.append(f'<tspan x="{PX + 12}" y="{y}">{spans}</tspan>')
    o.append("</text>")
    o.append(f'<text x="{X_TXT}" y="30" fill="{c["text"]}" xml:space="preserve">')
    for i, l in enumerate(LINES):
        o.append(f'<tspan x="{X_TXT}" y="{30 + i * LH}">{l}</tspan>')
    o.append("</text></svg>")
    open(fname, "w", encoding="utf-8").write("\n".join(o))
print("ok", WIDTH, H)

# quick PNG preview of the portrait (not part of the repo)
from PIL import ImageDraw, ImageFont
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
    im = Image.new("RGB", (COLS * 6 + 24, ROWS * 12 + 24), "#0d1117"); d = ImageDraw.Draw(im)
    for i, runs in enumerate(art):
        x = 12
        for col, t in runs:
            (d.rectangle([x, 12 + i * 12, x + 6 * len(t), 12 + i * 12 + 12], fill=dim(col)), d.text((x, 12 + i * 12), t, fill=lighten(col), font=f)) if col else None; x += 6 * len(t)
    im = im.resize((im.width * 2, im.height * 2)); im.save("/home/claude/preview.png")
except Exception as e:
    print("preview skipped", e)
