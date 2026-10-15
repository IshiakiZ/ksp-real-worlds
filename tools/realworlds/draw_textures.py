#!/usr/bin/env python3
"""Real Worlds' textures that no spacecraft's map gives, drawn from published measurements (2026-10-14).

    python3 tools/realworlds/draw_textures.py

  Venus      the ground under the clouds: the dark basalt Venera 13 and 14 photographed (it looks orange there only because
             of the light that reaches it); and the cloud tops seen from space, almost featureless in visible light.
  Saturn, Uranus, Neptune
             no global map of their cloud tops is published: their bands drawn in the colours of their photographs (Cassini,
             Voyager 2), with a faint drift of finer bands. Said so wherever they are shown.
  Saturn's rings
             the brightness and opacity across the rings from their measured edges and optical depths (NASA's Saturnian
             rings fact sheet: the D, C, B and A rings, the Cassini Division, the Encke and Keeler gaps, the F ring).
Each is written as a picture in ~/.ksp-ai-bridge/tools/realworlds/drawn and made into a texture by maps.swift (rings straight to an RGBA DDS).
"""
import json, math, os, random, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from sources import SCRATCH  # noqa: E402
from bodies import BODIES  # noqa: E402

OUT = os.path.join(ROOT, "src", "RealWorlds", "PluginData")
WORK = os.path.expanduser("~/.ksp-ai-bridge/tools/realworlds/drawn")
TOOL = os.path.expanduser("~/.ksp-ai-bridge/tools/realworlds/maps")
MADE = os.path.join(HERE, "made.json")

def write_ppm(path, w, h, pixel):
    with open(path, "wb") as f:
        f.write(b"P6 %d %d 255\n" % (w, h))
        row = bytearray(w * 3)
        for y in range(h):
            lat = 90.0 - (y + 0.5) * 180.0 / h
            for x in range(w):
                lon = -180.0 + (x + 0.5) * 360.0 / w
                r, g, b = pixel(lat, lon)
                row[3 * x] = max(0, min(255, int(r * 255 + 0.5)))
                row[3 * x + 1] = max(0, min(255, int(g * 255 + 0.5)))
                row[3 * x + 2] = max(0, min(255, int(b * 255 + 0.5)))
            f.write(row)

def smooth_noise(seed, n=64):
    """A cheap smooth random function of one variable (sums of sines), for the bands' drift."""
    rnd = random.Random(seed)
    waves = [(rnd.uniform(1, n), rnd.uniform(0, 2 * math.pi), rnd.uniform(0.3, 1.0)) for _ in range(12)]
    total = sum(a for _, _, a in waves)
    return lambda t: sum(a * math.sin(k * t + p) for k, p, a in waves) / total

def lerp_stops(stops, x):
    if x <= stops[0][0]:
        return stops[0][1]
    for (x0, c0), (x1, c1) in zip(stops, stops[1:]):
        if x <= x1:
            f = (x - x0) / (x1 - x0)
            return tuple(a + (b - a) * f for a, b in zip(c0, c1))
    return stops[-1][1]

def banded(stops, wobble, seed, fine):
    """Bands by latitude from colour stops; each band's edge drifts a little with longitude, and fine bands ripple."""
    drift = smooth_noise(seed)
    ripple = smooth_noise(seed + 1, 400)
    def pixel(lat, lon):
        t = math.radians(lon)
        l = lat + wobble * drift(t + lat * 0.05)
        c = lerp_stops(stops, l)
        k = 1.0 + fine * ripple(math.radians(lat) * 6.0 + 0.15 * drift(t * 3))
        return tuple(v * k for v in c)
    return pixel

# Saturn (Cassini's natural colour): a pale butterscotch equator, tan belts, fainter bands towards the poles, a blue-grey
# north polar region within the hexagon (as in 2013-2017), tan in the south.
SATURN = [(-90, (0.78, 0.70, 0.55)), (-70, (0.80, 0.72, 0.56)), (-50, (0.86, 0.78, 0.60)), (-35, (0.83, 0.74, 0.56)),
          (-22, (0.88, 0.80, 0.62)), (-12, (0.80, 0.68, 0.48)), (-6, (0.93, 0.86, 0.68)), (6, (0.94, 0.87, 0.69)),
          (12, (0.82, 0.70, 0.50)), (22, (0.89, 0.81, 0.63)), (35, (0.85, 0.76, 0.58)), (50, (0.82, 0.76, 0.62)),
          (65, (0.72, 0.72, 0.70)), (78, (0.60, 0.66, 0.72)), (90, (0.58, 0.64, 0.70))]
# Uranus (Voyager 2, 1986, south pole towards the Sun): nearly featureless pale cyan, a little brighter round the pole.
URANUS = [(-90, (0.70, 0.86, 0.88)), (-55, (0.66, 0.84, 0.87)), (-20, (0.61, 0.81, 0.85)), (20, (0.60, 0.80, 0.85)),
          (90, (0.58, 0.79, 0.85))]
# Neptune (Voyager 2, its true colour as Irwin et al. 2024 recalibrated it: a pale greenish blue a little deeper than
# Uranus), a darker band near 60 S and faint bright streaks of cloud.
NEPTUNE = [(-90, (0.50, 0.68, 0.84)), (-65, (0.42, 0.60, 0.80)), (-55, (0.47, 0.66, 0.84)), (-30, (0.50, 0.69, 0.86)),
           (0, (0.49, 0.68, 0.86)), (30, (0.50, 0.69, 0.86)), (90, (0.52, 0.70, 0.86))]

def venus_ground(lat, lon):
    return (0.36, 0.31, 0.26)

def venus_clouds(seed=7):
    drift = smooth_noise(seed)
    def pixel(lat, lon):
        # (in visible light the cloud tops are almost uniform: a faint darkening towards the poles, a faint drift)
        k = 1.0 - 0.10 * (abs(lat) / 90.0) ** 2 + 0.015 * drift(math.radians(lon) * 2 + math.radians(lat) * 4)
        return (0.96 * k, 0.90 * k, 0.74 * k)
    return pixel

def titan_haze(seed=13):
    drift = smooth_noise(seed)
    def pixel(lat, lon):
        # (in visible light Titan is its haze: an even orange-tan, the summer hemisphere a little lighter than the winter one
        # (Voyager and Cassini saw the contrast swap with the seasons), darkening a little towards the poles; a faint drift)
        k = 1.0 + 0.05 * math.tanh(lat / 25.0) - 0.08 * (abs(lat) / 90.0) ** 2 + 0.01 * drift(math.radians(lon) + math.radians(lat) * 3)
        return (0.80 * k, 0.58 * k, 0.30 * k)
    return pixel

# Saturn's rings, km from Saturn's centre: (inner, outer, optical depth, colour), from NASA's fact sheet and Cassini's
# occultations (optical depths are typical values across each region).
RINGS = [
    (66900, 74510, 0.002, (0.70, 0.64, 0.58)),   # D ring
    (74658, 77790, 0.08, (0.66, 0.60, 0.54)),    # C ring, inner
    (77790, 77940, 0.0, None),                   # Colombo gap
    (77940, 87420, 0.10, (0.68, 0.62, 0.55)),    # C ring
    (87420, 87610, 0.0, None),                   # Maxwell gap
    (87610, 92000, 0.12, (0.70, 0.64, 0.57)),    # C ring, outer
    (92000, 99000, 1.4, (0.86, 0.78, 0.66)),     # B ring, inner
    (99000, 104500, 2.5, (0.92, 0.85, 0.73)),    # B ring
    (104500, 115000, 4.0, (0.95, 0.88, 0.76)),   # B ring, the densest
    (115000, 117580, 2.0, (0.90, 0.83, 0.71)),   # B ring, outer edge
    (117580, 117930, 0.02, (0.55, 0.52, 0.48)),  # Huygens gap
    (117930, 122170, 0.10, (0.62, 0.58, 0.53)),  # Cassini Division
    (122170, 133423, 0.55, (0.86, 0.80, 0.71)),  # A ring
    (133423, 133748, 0.0, None),                 # Encke gap
    (133748, 136485, 0.45, (0.84, 0.78, 0.69)),  # A ring, outer
    (136485, 136527, 0.0, None),                 # Keeler gap
    (136527, 136775, 0.40, (0.82, 0.76, 0.67)),  # A ring, its edge
    (136775, 139900, 0.0, None),
    (139900, 140400, 0.3, (0.80, 0.75, 0.68)),   # F ring
]
RING_INNER, RING_OUTER = 66900.0, 141000.0

def ring_texture(path, n=2048):
    """An RGBA DDS one row high for every radius from RING_INNER (u = 0) to RING_OUTER (u = 1): colour by brightness, alpha
    the share of light a ring stops looking through it at about 40 degrees."""
    texels = []
    for i in range(n):
        r = RING_INNER + (i + 0.5) / n * (RING_OUTER - RING_INNER)
        tau, col = 0.0, (0.0, 0.0, 0.0)
        for a, b, t, c in RINGS:
            if a <= r < b:
                tau, col = t, c or (0.0, 0.0, 0.0)
                break
        alpha = 1.0 - math.exp(-tau / 0.64) if tau > 0 else 0.0
        # (a thin ring looks dim; an opaque one shows its own colour)
        lum = 0.35 + 0.65 * min(1.0, tau / 1.5) if tau > 0 else 0.0
        texels.append(tuple(int(max(0, min(255, v * lum * 255))) for v in col) + (int(alpha * 255 + 0.5),))
    h = 4
    header = bytearray(b"DDS ")
    header += struct.pack("<7I", 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, h, n, n * 4, 0, 1)
    header += b"\0" * 44
    header += struct.pack("<8I", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    header += struct.pack("<5I", 0x1000, 0, 0, 0, 0)
    body = bytearray()
    for _ in range(h):
        for (r_, g_, b_, a_) in texels:
            body += bytes((b_, g_, r_, a_))
    with open(path, "wb") as f:
        f.write(bytes(header) + bytes(body))

# The colour of each giant's limb, where the light passes through the most haze (the rim ramp of the game's far-away
# shader, read from the middle outward): from photographs of each (Cassini, Juno, Voyager 2).
# The colour each atmosphere's edge is tinted with, for the worlds drawn with KSP's rim shader (Jupiter's is not, since
# Real Worlds gives it the plain one: kept for a later use).
RIMS = {"Jupiter": (0.80, 0.78, 0.74), "Saturn": (0.86, 0.80, 0.66), "Uranus": (0.70, 0.88, 0.92), "Neptune": (0.52, 0.70, 0.92),
        "Venus": (0.95, 0.88, 0.70), "Titan": (0.85, 0.55, 0.25)}

def rim_ppm(path, colour, w=256, h=8):
    with open(path, "wb") as f:
        f.write(b"P6 %d %d 255\n" % (w, h))
        row = bytearray()
        for x in range(w):
            # (as the stock ramps run: the colour at the left, fading to black by seven tenths of the way)
            t = max(0.0, 1.0 - x / (0.7 * (w - 1.0))) ** 1.5
            row += bytes(int(max(0, min(255, c * t * 255))) for c in colour)
        f.write(bytes(row) * h)

def colour_job(png, out, w, h):
    return {"kind": "colour", "in": png, "out": out, "width": w, "height": h, "lon0": -180}

def flat_normals(path, w=8, h=4, alpha=255):
    """A normal map that bends nothing (uncompressed RGBA): for the giants, whose template's normal map is Jool's swirls.
    The rim shader Venus and Titan are drawn with reads it from red and green; the plain one the giants are drawn with
    (Jool's template's, and the one Worlds.cs gives Jupiter) reads its sideways part from alpha, where 255 tips every
    normal on its side and lights the planet from the wrong side (seen 2026-10-14: Jupiter and Neptune a sliver lit with
    the sun behind the camera): so the giants' has alpha 128."""
    header = bytearray(128)
    struct.pack_into("<4sIIIIIII", header, 0, b"DDS ", 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, h, w, w * 4, 0, 1)
    # pixel format: 32 bytes at 76, RGBA with masks
    struct.pack_into("<IIIIIIII", header, 76, 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    struct.pack_into("<I", header, 108, 0x1000)
    with open(path, "wb") as f:
        f.write(header)
        f.write(bytes([255, 128, 128, alpha]) * (w * h))  # B, G, R, A in memory order: R = G = 128, B = 255

def main():
    os.makedirs(WORK, exist_ok=True)
    jobs = []
    drawn = {
        ("Venus", "colour.dds", 1024, 512): venus_ground,
        ("Venus", "clouds.dds", 2048, 1024): venus_clouds(),
        ("Titan", "clouds.dds", 2048, 1024): titan_haze(),
        ("Saturn", "colour.dds", 4096, 2048): banded(SATURN, 1.2, 11, 0.04),
        ("Uranus", "colour.dds", 2048, 1024): banded(URANUS, 0.6, 21, 0.01),
        ("Neptune", "colour.dds", 2048, 1024): banded(NEPTUNE, 1.5, 31, 0.03),
    }
    for (world, name, w, h), pixel in drawn.items():
        ppm = os.path.join(WORK, "%s_%s.ppm" % (world, name.split(".")[0]))
        png = ppm[:-4] + ".png"
        write_ppm(ppm, w, h, pixel)
        subprocess.run(["sips", "-s", "format", "png", ppm, "--out", png], check=True, capture_output=True)
        os.makedirs(os.path.join(OUT, world), exist_ok=True)
        jobs.append(colour_job(png, os.path.join(OUT, world, name), w, h))
    for world, colour in RIMS.items():
        ppm = os.path.join(WORK, "%s_rim.ppm" % world)
        png = ppm[:-4] + ".png"
        rim_ppm(ppm, colour)
        subprocess.run(["sips", "-s", "format", "png", ppm, "--out", png], check=True, capture_output=True)
        os.makedirs(os.path.join(OUT, world), exist_ok=True)
        jobs.append({"kind": "colour", "in": png, "out": os.path.join(OUT, world, "rim.dds"), "width": 256, "height": 8, "lon0": -180,
                     "mirror": False, "flipRows": False, "mips": False})
    path = os.path.join(WORK, "jobs-drawn.json")
    json.dump(jobs, open(path, "w"), indent=1)
    subprocess.run([TOOL, path], check=True)
    os.makedirs(os.path.join(OUT, "Saturn"), exist_ok=True)
    ring_texture(os.path.join(OUT, "Saturn", "rings.dds"))
    flat_normals(os.path.join(OUT, "flat_normals.dds"))
    flat_normals(os.path.join(OUT, "flat_normals_alpha.dds"), alpha=128)
    made = json.load(open(MADE)) if os.path.exists(MADE) else {}
    for (world, name, w, h) in drawn:
        e = made.setdefault(world, {})
        e["textures"] = sorted(set(e.get("textures", [])) | {name})
        e["drawn"] = sorted(set(e.get("drawn", [])) | {name})
    for world in RIMS:
        e = made.setdefault(world, {})
        e["textures"] = sorted(set(e.get("textures", [])) | {"rim.dds"})
    made.setdefault("Saturn", {})["rings"] = {"inner_km": RING_INNER, "outer_km": RING_OUTER}
    made["Saturn"]["textures"] = sorted(set(made["Saturn"].get("textures", [])) | {"rings.dds"})
    json.dump(made, open(MADE, "w"), indent=1, sort_keys=True)
    print("drawn:", ", ".join("%s/%s" % (w, n) for (w, n, _, _) in drawn), "and Saturn/rings.dds")

if __name__ == "__main__":
    main()
