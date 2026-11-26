#!/usr/bin/env python3
"""Servicia — Meta Ads traffic campaign video (9:16, 15s, 30fps).
Style: dark cinematic background, neon flowing gradients (brand copper/green
+ violet/blue), translucent glass orbs with rim light, bold Archivo typography.
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
FPS = 30
DUR = 15.0
TOTAL = int(DUR * FPS)

BGW, BGH = 270, 480  # low-res background, upscaled (smooth gradients)

F_DISPLAY = "/tmp/Archivo[wdth,wght].ttf"
F_BODY = "/tmp/Inter[opsz,wght].ttf"

INK = (247, 244, 238)          # cream white (site ink)
COPPER = (216, 149, 95)        # brand copper  #d8955f
COPPER_HOT = (255, 138, 76)
GREEN = (143, 191, 155)        # brand sage   #8fbf9b
GREEN_HOT = (95, 214, 143)
VIOLET = (124, 92, 255)
BLUE = (47, 168, 255)
DARK = (13, 11, 16)

_font_cache = {}
def F(path, size, wght=None):
    key = (path, size, wght)
    if key not in _font_cache:
        f = ImageFont.truetype(path, size)
        if wght is not None:
            try:
                axes = f.get_variation_axes()
                vals = []
                for ax in axes:
                    name = ax["name"] if isinstance(ax, dict) else ax.name
                    nm = (name.decode() if isinstance(name, bytes) else str(name)).lower()
                    if "width" in nm or nm == "wdth":
                        vals.append(100)
                    elif "optical" in nm or nm == "opsz":
                        vals.append(max(ax["minimum"], min(ax["maximum"], size)) if isinstance(ax, dict) else size)
                    else:
                        vals.append(wght)
                f.set_variation_by_axes(vals)
            except Exception:
                pass
        _font_cache[key] = f
    return _font_cache[key]

def ease_out(t):
    return 1 - (1 - t) ** 3

def clamp01(x):
    return max(0.0, min(1.0, x))

def seg(t, a, b, fade=0.35):
    """in/out envelope for element visible between a and b (seconds)."""
    tin = clamp01((t - a) / fade)
    tout = clamp01((b - t) / fade)
    return ease_out(tin) * clamp01(tout)

# ---------------------------------------------------------------- background
_blob_cfg = [
    (COPPER_HOT, 0.42, 0.30, 0.0009, 0.0013, 0.0),
    (VIOLET,     0.36, 0.26, -0.0012, 0.0008, 1.3),
    (GREEN_HOT,  0.30, 0.34, 0.0007, -0.0011, 2.4),
    (BLUE,       0.28, 0.22, -0.0009, -0.0007, 4.1),
]

def background(t):
    yy, xx = np.mgrid[0:BGH, 0:BGW].astype(np.float32)
    nx, ny = xx / BGW, yy / BGH
    img = np.zeros((BGH, BGW, 3), np.float32)
    base = np.array(DARK, np.float32) / 255.0
    img += base[None, None, :]
    for color, rad, inten, sx, sy, ph in _blob_cfg:
        cx = 0.5 + 0.36 * math.sin(t * sx * 2 * math.pi * 3 + ph)
        cy = 0.5 + 0.30 * math.cos(t * sy * 2 * math.pi * 3 + ph * 1.7)
        d2 = ((nx - cx) * 1.0) ** 2 + ((ny - cy) * (BGW / BGH)) ** 2
        g = np.exp(-d2 / (rad * rad)) * inten
        img += g[:, :, None] * (np.array(color, np.float32) / 255.0)[None, None, :]
    img = np.clip(img, 0, 1)
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return np.asarray(im, np.float32) / 255.0

# ---------------------------------------------------------------- glass orbs
class Orb:
    def __init__(self, cx, cy, r, color, t0, drift=1.0):
        self.cx, self.cy, self.r = cx, cy, r
        self.color = color
        self.t0 = t0
        self.drift = drift

    def draw(self, layer, t):
        life = clamp01((t - self.t0) / 0.6)
        if life <= 0:
            return
        e = ease_out(life)
        d = self.drift
        cx = self.cx + 18 * d * math.sin(t * 0.9 + self.t0)
        cy = self.cy + 24 * d * math.cos(t * 0.7 + self.t0 * 2.0)
        r = self.r * (0.86 + 0.14 * e) * (1 + 0.012 * math.sin(t * 1.3 + self.t0))
        alpha = int(70 * e)
        col = self.color
        dr = ImageDraw.Draw(layer)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (alpha,))
        # inner upper-left highlight
        hr = r * 0.55
        dr.ellipse([cx - r * 0.45 - hr * 0.5, cy - r * 0.5 - hr * 0.5,
                    cx - r * 0.45 + hr * 0.5, cy - r * 0.5 + hr * 0.5],
                   fill=(255, 255, 255, int(26 * e)))
        # rim light
        rw = max(3, int(r * 0.012))
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col + (int(200 * e),), width=rw)
        dr.arc([cx - r, cy - r, cx + r, cy + r], start=200, end=330,
               fill=(255, 255, 255, int(160 * e)), width=rw * 2)

def orb_layer(orbs, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for o in orbs:
        o.draw(layer, t)
    return layer

def add_glow(base, layer, radius=26, boost=1.0):
    small = layer.resize((W // 4, H // 4), Image.BILINEAR)
    blurred = small.filter(ImageFilter.GaussianBlur(radius / 4))
    big = blurred.resize((W, H), Image.BILINEAR)
    arr = np.asarray(big, np.float32)
    a = arr[:, :, 3:4] / 255.0 * boost
    rgb = arr[:, :, :3] * a
    out = base + rgb / 255.0
    return np.clip(out, 0, 1)

# ---------------------------------------------------------------- text utils
def text_size(font, s, tracking=0):
    if tracking:
        wsum = sum(font.getlength(c) for c in s) + tracking * (len(s) - 1)
        return wsum, font.getbbox(s)[3] - font.getbbox(s)[1]
    b = font.getbbox(s)
    return font.getlength(s), b[3] - b[1]

def draw_tracked(draw, xy, s, font, fill, tracking=0, anchor_x="left"):
    wsum, _ = text_size(font, s, tracking)
    x, y = xy
    if anchor_x == "center":
        x -= wsum / 2
    elif anchor_x == "right":
        x -= wsum
    for c in s:
        draw.text((x, y), c, font=font, fill=fill)
        x += font.getlength(c) + tracking

def text_sprite(s, font, fill, tracking=0, pad=40):
    wsum, hgt = text_size(font, s, tracking)
    wbox, hbox = int(wsum) + pad * 2, int(hgt * 1.4) + pad * 2
    img = Image.new("RGBA", (max(wbox, 4), max(hbox, 4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = pad - font.getbbox(s)[1]
    if tracking:
        draw_tracked(d, (pad, y), s, font, fill + (255,), tracking)
    else:
        d.text((pad, y), s, font=font, fill=fill + (255,))
    return img

def paste_glow(canvas_np, sprite, cx, cy, alpha, glow=22, boost=0.9, dy=0):
    if alpha <= 0.01:
        return
    sp = sprite
    if alpha < 1:
        sp = sp.copy()
        a = sp.getchannel("A").point(lambda v: int(v * alpha))
        sp.putalpha(a)
    glow_layer = sp.filter(ImageFilter.GaussianBlur(glow / 3))
    small = glow_layer.resize((max(1, sp.width // 4), max(1, sp.height // 4)), Image.BILINEAR)
    big = small.resize(sp.size, Image.BILINEAR)
    pos = (int(cx - sp.width / 2), int(cy - sp.height / 2 + dy))
    gpos = (pos[0], pos[1] + int(glow * 0.2))
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tmp.paste(big, gpos, big)
    arr = np.asarray(tmp, np.float32)
    a = arr[:, :, 3:4] / 255.0 * boost
    base_rgb = np.asarray(canvas_np.convert("RGB"), np.float32) / 255.0
    add = np.clip(base_rgb + (arr[:, :, :3] / 255.0) * a, 0, 1)
    canvas_np.paste(Image.fromarray((add * 255).astype(np.uint8)).convert("RGBA"))
    canvas_np.paste(sp, pos, sp)

# ---------------------------------------------------------------- chip
def chip_sprite(label, font, fg, border, fill=None, tracking=3, pad_x=34, pad_y=20):
    wsum, hgt = text_size(font, label, tracking)
    wbox, hbox = int(wsum) + pad_x * 2, int(hgt * 1.35) + pad_y * 2
    img = Image.new("RGBA", (wbox, hbox), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rect = [3, 3, wbox - 4, hbox - 4]
    if fill:
        d.rounded_rectangle(rect, radius=hbox // 2, fill=fill + (255,))
    d.rounded_rectangle(rect, radius=hbox // 2, outline=border + (255,), width=3)
    y = hbox / 2 - hgt / 2 - font.getbbox(label)[1]
    draw_tracked(d, (pad_x, y), label, font, fg + (255,), tracking)
    return img

# ---------------------------------------------------------------- scenes
MED = dict(disp=lambda s: F(F_DISPLAY, s, 640), body=lambda s: F(F_BODY, s, 480))

def build_sprites():
    S = {}
    # scene 1
    S["s1_label"] = chip_sprite("SERVICIA · OPERACIÓN DE PERSONAL Y ADMINISTRATIVA",
                                F(F_BODY, 30, 600), COPPER, (90, 66, 50), tracking=4)
    S["s1_h1a"] = text_sprite("Toda empresa opera", F(F_DISPLAY, 104, 800), INK)
    S["s1_h1b"] = text_sprite("en dos frentes.", F(F_DISPLAY, 104, 800), COPPER)
    S["s1_sub"] = text_sprite("El piso y la oficina.\nCubrimos los dos.", F(F_BODY, 52, 500), (205, 200, 192))
    # scene 2
    S["s2_chip"] = chip_sprite("FRENTE 01 — EN EL PISO", F(F_BODY, 34, 700), GREEN_HOT, (52, 110, 76), tracking=4)
    S["s2_h2"] = text_sprite("Operación de personal", F(F_DISPLAY, 92, 800), INK)
    S["s2_line"] = text_sprite("Limpieza · Eventos · Hotelería · Logística", F(F_BODY, 44, 500), (190, 185, 178))
    S["s2_b1"] = text_sprite("✓  Asistencia confirmada antes de cada turno", F(F_BODY, 40, 500), INK)
    S["s2_b2"] = text_sprite("✓  Suplencias cubiertas en minutos", F(F_BODY, 40, 500), INK)
    S["s2_tag"] = chip_sprite("GENTE + IA", F(F_BODY, 30, 700), GREEN, (60, 100, 70), tracking=5)
    # scene 3
    S["s3_chip"] = chip_sprite("FRENTE 02 — EN LA OFICINA", F(F_BODY, 34, 700), COPPER_HOT, (120, 72, 40), tracking=4)
    S["s3_h2"] = text_sprite("Tu administración,\noperada como servicio", F(F_DISPLAY, 80, 800), INK)
    S["s3_line"] = text_sprite("Facturación · Cobranza · Pagos · Atención", F(F_BODY, 44, 500), (190, 185, 178))
    S["s3_b1"] = text_sprite("✓  SLA por función, con equipo dedicado", F(F_BODY, 40, 500), INK)
    S["s3_b2"] = text_sprite("✓  Tablero en vivo: asistencia, pendientes y costo", F(F_BODY, 40, 500), INK)
    S["s3_tag"] = chip_sprite("GENTE + IA", F(F_BODY, 30, 700), COPPER, (110, 78, 52), tracking=5)
    # scene 4
    S["s4_h2"] = text_sprite("Inteligencia + Gente\n+ Supervisión", F(F_DISPLAY, 88, 800), INK)
    S["s4_sub"] = text_sprite("Un contrato. Un SLA.\nUn solo responsable.", F(F_BODY, 50, 500), (205, 200, 192))
    S["s4_m1"] = chip_sprite("EN 90 DÍAS O MENOS", F(F_BODY, 32, 700), COPPER_HOT, (120, 72, 40), tracking=3)
    S["s4_m2"] = chip_sprite("24/7 CENTRO DE COMANDO", F(F_BODY, 32, 700), GREEN_HOT, (52, 110, 76), tracking=3)
    S["s4_m3"] = chip_sprite("100% REPSE E IMSS", F(F_BODY, 32, 700), BLUE, (40, 90, 130), tracking=3)
    # scene 5
    S["s5_h1a"] = text_sprite("Deja de perseguir", F(F_DISPLAY, 100, 800), INK)
    S["s5_h1b"] = text_sprite("pendientes.", F(F_DISPLAY, 100, 800), INK)
    S["s5_h2a"] = text_sprite("Empieza a exigir", F(F_DISPLAY, 100, 800), COPPER)
    S["s5_h2b"] = text_sprite("números.", F(F_DISPLAY, 100, 800), COPPER)

    btn_label = "Agenda tu diagnóstico operativo"
    bf = F(F_BODY, 44, 700)
    wsum, hgt = text_size(bf, btn_label)
    bw, bh = int(wsum) + 90, int(hgt * 1.5) + 46
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=bh // 2, fill=COPPER_HOT + (255,))
    d.text((bw / 2 - wsum / 2, bh / 2 - hgt / 2 - bf.getbbox(btn_label)[1]), btn_label, font=bf, fill=(20, 12, 8, 255))
    S["s5_btn"] = img
    S["s5_url"] = text_sprite("servicia.com.mx", F(F_DISPLAY, 58, 700), INK)
    S["s5_brand"] = chip_sprite("SERVICIA", F(F_DISPLAY, 40, 800), COPPER, (90, 66, 50), tracking=8)
    return S

SPR = build_sprites()

ORBS = [
    Orb(W * 0.74, H * 0.24, 300, VIOLET, -1.0, 1.0),
    Orb(W * 0.24, H * 0.40, 190, GREEN_HOT, -1.0, -1.0),
    Orb(W * 0.68, H * 0.62, 240, COPPER_HOT, -1.0, 1.0),
    Orb(W * 0.30, H * 0.80, 210, BLUE, -1.0, -1.2),
]

def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    v = 1 - 0.42 * np.clip(d - 0.45, 0, 1) ** 1.6
    return v[:, :, None]

VIG = vignette()

def compose(t, idx):
    bg = background(t)
    # orbs
    layer = orb_layer(ORBS, t)
    bg = add_glow(bg, layer, radius=40, boost=0.55)
    canvas = Image.fromarray((bg * 255).astype(np.uint8)).convert("RGB").convert("RGBA")
    canvas.alpha_composite(layer)

    # scene text
    if t < 2.8:
        a0 = ease_out(clamp01(t / 0.5)) * clamp01((2.8 - t) / 0.3)
        a1 = ease_out(clamp01((t - 0.25) / 0.5)) * clamp01((2.8 - t) / 0.3)
        a2 = ease_out(clamp01((t - 1.5) / 0.5)) * clamp01((2.8 - t) / 0.3)
        paste_glow(canvas, SPR["s1_label"], W / 2, 400, a0, 14, 0.4, dy=(1 - a0) * 24)
        paste_glow(canvas, SPR["s1_h1a"], W / 2, 760, a1, 24, 0.9, dy=(1 - a1) * 40)
        paste_glow(canvas, SPR["s1_h1b"], W / 2, 900, a1, 24, 0.9, dy=(1 - a1) * 40)
        paste_glow(canvas, SPR["s1_sub"], W / 2, 1180, a2, 16, 0.5, dy=(1 - a2) * 40)
    elif t < 6.0:
        u = t - 2.8
        a0 = ease_out(clamp01(u / 0.45)) * clamp01((3.2 - u) / 0.3)
        a1 = ease_out(clamp01((u - 0.3) / 0.5)) * clamp01((3.2 - u) / 0.3)
        a2 = ease_out(clamp01((u - 0.7) / 0.5)) * clamp01((3.2 - u) / 0.3)
        a3 = ease_out(clamp01((u - 1.1) / 0.45)) * clamp01((3.2 - u) / 0.3)
        a4 = ease_out(clamp01((u - 1.4) / 0.45)) * clamp01((3.2 - u) / 0.3)
        a5 = ease_out(clamp01((u - 1.8) / 0.45)) * clamp01((3.2 - u) / 0.3)
        paste_glow(canvas, SPR["s2_chip"], W / 2, 380, a0, 12, 0.4, dy=(1 - a0) * 24)
        paste_glow(canvas, SPR["s2_h2"], W / 2, 640, a1, 22, 0.9, dy=(1 - a1) * 40)
        paste_glow(canvas, SPR["s2_line"], W / 2, 800, a2, 14, 0.4, dy=(1 - a2) * 32)
        paste_glow(canvas, SPR["s2_b1"], W / 2, 1010, a3, 12, 0.35, dy=(1 - a3) * 30)
        paste_glow(canvas, SPR["s2_b2"], W / 2, 1100, a4, 12, 0.35, dy=(1 - a4) * 30)
        paste_glow(canvas, SPR["s2_tag"], W / 2, 1260, a5, 12, 0.4, dy=(1 - a5) * 24)
    elif t < 9.2:
        u = t - 6.0
        a0 = ease_out(clamp01(u / 0.45)) * clamp01((3.2 - u) / 0.3)
        a1 = ease_out(clamp01((u - 0.3) / 0.5)) * clamp01((3.2 - u) / 0.3)
        a2 = ease_out(clamp01((u - 0.7) / 0.5)) * clamp01((3.2 - u) / 0.3)
        a3 = ease_out(clamp01((u - 1.1) / 0.45)) * clamp01((3.2 - u) / 0.3)
        a4 = ease_out(clamp01((u - 1.4) / 0.45)) * clamp01((3.2 - u) / 0.3)
        a5 = ease_out(clamp01((u - 1.8) / 0.45)) * clamp01((3.2 - u) / 0.3)
        paste_glow(canvas, SPR["s3_chip"], W / 2, 380, a0, 12, 0.4, dy=(1 - a0) * 24)
        paste_glow(canvas, SPR["s3_h2"], W / 2, 660, a1, 22, 0.9, dy=(1 - a1) * 40)
        paste_glow(canvas, SPR["s3_line"], W / 2, 880, a2, 14, 0.4, dy=(1 - a2) * 32)
        paste_glow(canvas, SPR["s3_b1"], W / 2, 1090, a3, 12, 0.35, dy=(1 - a3) * 30)
        paste_glow(canvas, SPR["s3_b2"], W / 2, 1180, a4, 12, 0.35, dy=(1 - a4) * 30)
        paste_glow(canvas, SPR["s3_tag"], W / 2, 1340, a5, 12, 0.4, dy=(1 - a5) * 24)
    elif t < 12.2:
        u = t - 9.2
        a0 = ease_out(clamp01(u / 0.5)) * clamp01((3.0 - u) / 0.3)
        a1 = ease_out(clamp01((u - 0.4) / 0.5)) * clamp01((3.0 - u) / 0.3)
        a2 = ease_out(clamp01((u - 1.0) / 0.45)) * clamp01((3.0 - u) / 0.3)
        a3 = ease_out(clamp01((u - 1.3) / 0.45)) * clamp01((3.0 - u) / 0.3)
        a4 = ease_out(clamp01((u - 1.6) / 0.45)) * clamp01((3.0 - u) / 0.3)
        paste_glow(canvas, SPR["s4_h2"], W / 2, 640, a0, 22, 0.9, dy=(1 - a0) * 40)
        paste_glow(canvas, SPR["s4_sub"], W / 2, 900, a1, 16, 0.5, dy=(1 - a1) * 36)
        paste_glow(canvas, SPR["s4_m1"], W / 2, 1180, a2, 12, 0.4, dy=(1 - a2) * 28)
        paste_glow(canvas, SPR["s4_m2"], W / 2, 1300, a3, 12, 0.4, dy=(1 - a3) * 28)
        paste_glow(canvas, SPR["s4_m3"], W / 2, 1420, a4, 12, 0.4, dy=(1 - a4) * 28)
    else:
        u = t - 12.2
        pulse = 1 + 0.02 * math.sin(t * 4.2)
        a0 = ease_out(clamp01(u / 0.5))
        a1 = ease_out(clamp01((u - 0.5) / 0.5))
        a2 = ease_out(clamp01((u - 1.0) / 0.5))
        a3 = ease_out(clamp01((u - 1.4) / 0.5))
        paste_glow(canvas, SPR["s5_h1a"], W / 2, 600, a0, 22, 0.9, dy=(1 - a0) * 40)
        paste_glow(canvas, SPR["s5_h1b"], W / 2, 730, a0, 22, 0.9, dy=(1 - a0) * 40)
        paste_glow(canvas, SPR["s5_h2a"], W / 2, 900, a1, 22, 0.9, dy=(1 - a1) * 40)
        paste_glow(canvas, SPR["s5_h2b"], W / 2, 1030, a1, 22, 0.9, dy=(1 - a1) * 40)
        btn = SPR["s5_btn"]
        if a2 > 0:
            bw, bh = int(btn.width * pulse), int(btn.height * pulse)
            btnp = btn.resize((bw, bh), Image.BILINEAR)
            paste_glow(canvas, btnp, W / 2, 1330, a2, 30, 1.1, dy=(1 - a2) * 40)
        paste_glow(canvas, SPR["s5_url"], W / 2, 1540, a3, 14, 0.6, dy=(1 - a3) * 30)

    out = np.asarray(canvas.convert("RGB"), np.float32) / 255.0
    out *= VIG
    # grain
    rng = np.random.default_rng(idx)
    out += rng.integers(-5, 6, (H, W, 1)).astype(np.float32) / 255.0 * 0.5
    # progress bar
    prog = t / DUR
    bar_y = H - 14
    out[bar_y:, : int(W * prog)] *= 0.0
    out[bar_y:, : int(W * prog)] += np.array(COPPER_HOT, np.float32) / 255.0
    out[bar_y:, int(W * prog):] *= 0.25
    return np.clip(out, 0, 1)

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    frames = range(TOTAL) if only is None else [int(only)]
    if only is not None:
        f = compose(int(only) / FPS, int(only))
        Image.fromarray((f * 255).astype(np.uint8)).save("/tmp/preview_%04d.png" % int(only))
        print("wrote preview", only)
        return
    ffbin = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    cmd = [ffbin, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "/workspace/servicia-ad/servicia_meta_ad_9x16.mp4"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in frames:
        f = compose(i / FPS, i)
        proc.stdin.write((f * 255).astype(np.uint8).tobytes())
        if i % 30 == 0:
            print(f"frame {i}/{TOTAL}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("done, rc =", proc.returncode)

if __name__ == "__main__":
    main()
