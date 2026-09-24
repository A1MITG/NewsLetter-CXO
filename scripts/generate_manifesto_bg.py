"""Generate the Manifesto section's background: signal out of noise.

An original, procedural image in SIGNAL's own palette. A quiet field of faint
points (raw information) fills the frame; out of it, flowing lines gather,
converge through one focal point like light through a lens, and fan gently
onward (the signal). The left side stays calm so text can sit on it; the
energy is on the right.

    python scripts/generate_manifesto_bg.py               # the page's image (seed 7)
    python scripts/generate_manifesto_bg.py --seed 21     # a variation: manifesto-bg-21.jpg here
    python scripts/generate_manifesto_bg.py --width 3840  # larger (height is half the width)

The page's image is written to both places it is served from: app/static/img
(Flask) and public/img (the static deploy). Variations go to the current
directory, so they never replace it by accident.

Dev-only: needs numpy, Pillow and SciPy, which are not in requirements.txt.
Deterministic for a given seed and size.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
PAGE_IMAGE = (ROOT / 'app' / 'static' / 'img' / 'manifesto-bg.jpg',
              ROOT / 'public' / 'img' / 'manifesto-bg.jpg')

# The Command Center's tokens.
NAVY = (0x0b, 0x15, 0x24)
NAVY_2 = (0x14, 0x24, 0x3a)
BLUE = (0x2f, 0x6f, 0xed)
LINE = (0x9f, 0xc1, 0xff)      # the engine tiles' vector colour
AMBER = (0xf5, 0xa6, 0x23)     # the logo's amber


def rgb(c):
    return np.array(c, dtype=np.float32) / 255.0


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def splat(buf, xs, ys, weights):
    """Add points into buf (H, W) with bilinear weights: anti-aliased marks
    without a vector renderer."""
    h, w = buf.shape
    x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = xs - x0, ys - y0
    for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)),
                       (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi, yi = x0 + dx, y0 + dy
        ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        np.add.at(buf, (yi[ok], xi[ok]), (weights * wt)[ok])


def paint(img, layer, color, gain=1.0):
    """img += layer (H, W) tinted with color."""
    img += (layer * gain)[..., None] * color[None, None, :]


def generate(width=2880, seed=7):
    rng = np.random.default_rng(seed)
    w, h = width, width // 2
    s = w / 2880.0                                   # scale factor for pixel sizes
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fx, fy = 0.74 * w, 0.50 * h                      # the focal point: the "insight"

    # 1. Base: navy to navy-2, top-left to bottom-right.
    t = ((xx / w) * 0.6 + (yy / h) * 0.4)[..., None]
    img = rgb(NAVY) * (1 - t) + rgb(NAVY_2) * t

    # 2. A faint blue haze around the focal point.
    r2 = ((xx - fx) / w) ** 2 + ((yy - fy) / h) ** 2 * 0.35
    paint(img, 0.07 * np.exp(-r2 / 0.010) + 0.03 * np.exp(-r2 / 0.08), rgb(BLUE))

    # 3. Raw information: faint points everywhere, thinning out where the
    #    signal has gathered (right of the focus, near its line).
    points = np.zeros((h, w), np.float32)
    n = int(12000 * s * s)
    px, py = rng.uniform(0, w, n), rng.uniform(0, h, n)
    near_band = np.exp(-((py - fy) / (0.18 * h)) ** 2) * smoothstep((px - 0.45 * w) / (0.3 * w))
    keep = rng.uniform(0, 1, n) > 0.85 * near_band
    splat(points, px[keep], py[keep], rng.uniform(0.05, 0.5, keep.sum()) ** 2.4)
    paint(img, gaussian_filter(points, 0.9 * s), rgb(LINE), 3.6)

    # 4. The signal: threads that start scattered and wavering, all but
    #    invisible, then gather through the focal point and fan gently to the
    #    right edge, fading as they go.
    energy = np.zeros((h, w), np.float32)
    for _ in range(80):
        x0 = rng.uniform(-0.08, 0.40) * w
        y0 = rng.uniform(0.04, 0.96) * h
        spread = rng.uniform(-1, 1)                  # its place in the fan past the focus
        xs = np.arange(x0, w * 1.02, 0.55)
        pre = smoothstep((xs - x0) / (fx - x0))      # 0 scattered -> 1 converged
        chaos = (1 - pre) ** 1.6
        wobble = sum(rng.uniform(0.3, 1.0) * np.sin(xs / (w * rng.uniform(0.035, 0.12)) + rng.uniform(0, 6.28))
                     for _ in range(3)) * 0.035 * h * chaos
        post = np.clip((xs - fx) / (w - fx), 0, None) ** 1.25
        ys = fy + (y0 - fy) * (1 - pre) + wobble + spread * post * 0.11 * h
        # The gathering carries the eye; the fan past the focus is quieter.
        vis = (0.08 + 0.92 * pre ** 2.2) * np.where(xs > fx, 0.7 * np.exp(-(xs - fx) / (0.2 * w)), 1.0)
        splat(energy, xs, ys, vis * rng.uniform(0.4, 1.0) * 0.45)
    # Overlapping threads saturate softly instead of adding up to white.
    core = 1 - np.exp(-energy * 1.1)
    paint(img, core, rgb(LINE), 0.55)
    paint(img, gaussian_filter(core, 4 * s), rgb(LINE) * 0.5 + rgb(BLUE) * 0.5, 0.45)
    paint(img, gaussian_filter(core, 20 * s), rgb(BLUE), 0.30)

    # 5. The focal point: a small warm core, the logo's amber, kept quiet.
    d2 = (xx - fx) ** 2 + (yy - fy) ** 2
    paint(img, 0.9 * np.exp(-d2 / (2 * (3.0 * s) ** 2)), rgb(AMBER) * 0.5 + 0.5)
    paint(img, 0.12 * np.exp(-d2 / (2 * (24 * s) ** 2)), rgb(AMBER))

    # 6. Vignette, film grain, then a soft shoulder (slope 1 at black, so the
    #    navy keeps its value) that stops highlights clipping.
    vig = 1 - 0.38 * (((xx - 0.55 * w) / (0.75 * w)) ** 2 + ((yy - 0.5 * h) / (0.75 * h)) ** 2)
    img *= np.clip(vig, 0.55, 1)[..., None]
    img += rng.normal(0, 0.008, (h, w, 1)).astype(np.float32)
    img = 1 - np.exp(-np.clip(img, 0, None))
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--seed', type=int, default=7)
    p.add_argument('--width', type=int, default=2880)
    p.add_argument('--out', default=None,
                   help="default: the page's image for seed 7 at 2880, else manifesto-bg-<seed>.jpg here")
    a = p.parse_args()
    if a.out:
        outs = [Path(a.out)]
    elif a.seed == 7 and a.width == 2880:
        outs = list(PAGE_IMAGE)
    else:
        outs = [Path(f'manifesto-bg-{a.seed}.jpg')]
    img = generate(a.width, a.seed)
    for out in outs:
        img.save(out, quality=86, optimize=True, progressive=True)
        print(f'Wrote {out}: {img.size[0]}x{img.size[1]}, {out.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
