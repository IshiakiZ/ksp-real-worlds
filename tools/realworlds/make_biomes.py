#!/usr/bin/env python3
"""Real Worlds' biomes: each world's regions for science, from its own maps (2026-10-14).

    python3 tools/realworlds/make_biomes.py [World ...]     # every world below, or those named

The stock worlds' biome maps were drawn for Kerbin's continents and the Mun's craters; laid over the real worlds they
named the Atlantic "Highlands". Each world here gets a map made from the same height and colour textures its terrain is
made of (src/RealWorlds/PluginData/<World>/height.dds and colour.dds), so the regions lie where the ground shows them:

  Earth     the sea by depth (shallows over the continental shelves, the open ocean, the trenches), the low coasts
            (shores: Cape Canaveral is one), and the land by height (mountains, highlands) and by what grows there, read
            from the Blue Marble's colours (ice sheets, deserts, tundra, rainforest, forest, grassland).
  Moon      the dark maria, each named for the great mare it lies in (the rest are the lesser maria); the near and
            far side's highlands; the South Pole-Aitken basin; the poles.
  Mars      the polar caps, Olympus Mons, the Tharsis rise, Valles Marineris, Hellas and Argyre, the northern
            lowlands below the old shore, the highlands.
  others    the poles, plains by height (or by brightness where only a picture is measured), and the named features
            seen from orbit (Caloris, Maxwell Montes, Occator, Sputnik Planitia, Enceladus's tiger stripes...).

Each map is a PNG (north at the top, longitude running west from 90 E at its left edge, as Kopernicus reads it:
x = 0.25 - longitude/360) in src/RealWorlds/PluginData/<World>/biomes.png; made.json records the regions and their
colours for make_configs.py. The giants have none (there is no ground to sample).
"""
import json, math, os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "src", "RealWorlds", "PluginData")
MADE = os.path.join(HERE, "made.json")

# ---------------------------------------------------------------- reading the textures

def dds_header(path):
    d = open(path, "rb").read(148)
    h, w = struct.unpack("<II", d[12:20])
    mips = max(1, struct.unpack("<I", d[28:32])[0])
    fourcc = d[84:88]
    return w, h, mips, fourcc, (148 if fourcc == b"DX10" else 128)

def read_height(world, W, H):
    """Heights in metres at W x H (south row first), sampled from the R16 height map."""
    path = os.path.join(OUT, world, "height.dds")
    if not os.path.exists(path):
        return None
    w, h, mips, fourcc, start = dds_header(path)
    made = json.load(open(MADE))[world]["height"]
    off, deform = made["offset"], made["deformity"]
    data = open(path, "rb").read()
    rows = []
    for i in range(H):
        y = min(h - 1, int((i + 0.5) * h / H))
        row = struct.unpack_from("<%dH" % w, data, start + 2 * w * y)
        rows.append([off + deform * row[min(w - 1, int((j + 0.5) * w / W))] / 65535.0 for j in range(W)])
    return rows

def rgb565(c):
    return ((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31

def read_colour(world, W, H):
    """Colours (r, g, b) at W x H (south row first), from the mip level of the BC1 colour map nearest W wide."""
    path = os.path.join(OUT, world, "colour.dds")
    if not os.path.exists(path):
        return None
    w, h, mips, fourcc, start = dds_header(path)
    if fourcc != b"DXT1":
        return None
    level, lw, lh, at = 0, w, h, start
    while level + 1 < mips and lw // 2 >= W:
        at += max(1, lw // 4) * max(1, lh // 4) * 8
        lw, lh, level = lw // 2, lh // 2, level + 1
    data = open(path, "rb").read()
    bw = max(1, lw // 4)
    # decode the level, block by block, into rows (south first, as the texture's rows run)
    pix = [[(0, 0, 0)] * lw for _ in range(lh)]
    for by in range(max(1, lh // 4)):
        for bx in range(bw):
            o = at + (by * bw + bx) * 8
            c0, c1, bits = struct.unpack_from("<HHI", data, o)
            a, b = rgb565(c0), rgb565(c1)
            if c0 > c1:
                pal = [a, b, tuple((2 * x + y) // 3 for x, y in zip(a, b)), tuple((x + 2 * y) // 3 for x, y in zip(a, b))]
            else:
                pal = [a, b, tuple((x + y) // 2 for x, y in zip(a, b)), (0, 0, 0)]
            for k in range(16):
                y, x = by * 4 + k // 4, bx * 4 + k % 4
                if y < lh and x < lw:
                    pix[y][x] = pal[(bits >> (2 * k)) & 3]
    return [[pix[min(lh - 1, int((i + 0.5) * lh / H))][min(lw - 1, int((j + 0.5) * lw / W))] for j in range(W)] for i in range(H)]

# ---------------------------------------------------------------- where a pixel is

def lon_of(j, W):
    lon = 360.0 * (0.25 - (j + 0.5) / W)
    return (lon + 180.0) % 360.0 - 180.0

def lat_of(i, H):
    return -90.0 + (i + 0.5) * 180.0 / H

def apart(lat1, lon1, lat2, lon2):
    """Degrees of arc between two places."""
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))

def within(lat, lon, centre, km, radius_km):
    return apart(lat, lon, centre[0], centre[1]) <= math.degrees(km / radius_km)

def bright(c):
    return (c[0] + c[1] + c[2]) / 3.0

# ---------------------------------------------------------------- the worlds

# Well-separated colours for the maps (the game finds each pixel's region by its nearest colour).
PALETTE = [(0, 0, 255), (0, 255, 255), (0, 0, 110), (255, 255, 255), (130, 70, 20), (190, 140, 60), (255, 220, 0),
           (150, 160, 170), (0, 120, 0), (0, 210, 60), (170, 230, 90), (255, 0, 0), (255, 0, 255), (120, 0, 160),
           (255, 128, 0), (0, 128, 128), (128, 128, 0), (64, 64, 64), (255, 160, 200), (160, 255, 220)]

def earth(lat, lon, h, c, ctx):
    r, g, b = c
    s = bright(c)
    grey = max(c) - min(c)
    # (the sea: below sea level and blue in the picture; a 20 km pixel on a coast is often a metre under, and land below the
    # sea, as round the Dead Sea, is not blue)
    if h < -200 or (h < 0 and b >= r and b >= g):
        return "Trenches" if h < -6500 else "Oceans" if h < -200 else "Shallows"
    if abs(lat) > 58 and s > 180 and grey < 45:
        return "Ice Sheets"
    if h > 2500:
        return "Mountains"
    # (deserts: bare ground, pale (the Sahara) or red (Australia's interior), before the plateaus: the Gobi and the
    # Kalahari are both)
    if r > g > b and ((r - b > 35 and s > 115) or (r - b > 60 and r > 0.15 * 255 and g < 0.8 * r)):
        return "Deserts"
    if h > 1000:
        return "Highlands"
    if -20 < h < 10:
        return "Shores"
    if abs(lat) > 62 or (abs(lat) > 50 and grey < 25 and s > 110):
        return "Tundra"
    if g >= r and s < 85:
        return "Rainforests" if abs(lat) < 23.5 else "Forests"
    return "Grasslands"

EARTH = ["Oceans", "Shallows", "Trenches", "Ice Sheets", "Mountains", "Highlands", "Deserts", "Tundra", "Forests",
         "Rainforests", "Grasslands", "Shores"]

# The great maria: centres (lat, lon) from the IAU's gazetteer, and how far (degrees of arc) each reaches.
MARIA = [("Oceanus Procellarum", 18.4, -57.4, 30), ("Mare Imbrium", 32.8, -15.6, 18), ("Mare Serenitatis", 28.0, 17.5, 11),
         ("Mare Tranquillitatis", 8.5, 31.4, 14), ("Mare Crisium", 17.0, 59.1, 9), ("Mare Fecunditatis", -7.8, 51.3, 12),
         ("Mare Nectaris", -15.2, 35.5, 8), ("Mare Nubium", -21.3, -16.6, 13), ("Mare Humorum", -24.4, -38.6, 8),
         ("Mare Frigoris", 56.0, 1.4, 22), ("Mare Orientale", -19.4, -92.8, 9), ("Mare Moscoviense", 27.3, 147.9, 6)]

def moon(lat, lon, h, c, ctx):
    if lat > 80:
        return "North Pole"
    if lat < -80:
        return "South Pole"
    if c is not None and bright(c) < ctx["dark"]:
        # (dark ground is a mare: named for the great mare whose reach it lies in, nearest first; the small ones and the
        # dark floors of far-side craters are the lesser maria)
        reach = [(apart(lat, lon, m[1], m[2]) / m[3], m[0]) for m in MARIA]
        f, name = min(reach)
        return name if f <= 1.0 else "Lesser Maria"
    if within(lat, lon, (-53.0, -169.0), 1250, 1737.4):
        return "South Pole-Aitken Basin"
    return "Near Side Highlands" if abs(lon) <= 90 else "Far Side Highlands"

MOON = ["North Pole", "South Pole"] + [m[0] for m in MARIA] + ["Lesser Maria", "South Pole-Aitken Basin", "Near Side Highlands",
                                                               "Far Side Highlands"]

def mars(lat, lon, h, c, ctx):
    # (the residual caps: the north's about 1,000 km across, the south's smaller and off the pole)
    if lat > 80:
        return "North Polar Cap"
    if lat < -83:
        return "South Polar Cap"
    if within(lat, lon, (18.65, -133.8), 330, 3389.5):
        return "Olympus Mons"
    if -18 < lat < -2 and -95 < lon < -35 and h < ctx["vm"]:
        return "Valles Marineris"
    if within(lat, lon, (-42.4, 70.5), 1150, 3389.5) and h < -2500:
        return "Hellas Planitia"
    if within(lat, lon, (-49.7, -44.0), 900, 3389.5) and h < -1000:
        return "Argyre Planitia"
    if within(lat, lon, (2.0, -110.0), 2800, 3389.5) and h > 3000:
        return "Tharsis"
    if h < -3000:
        return "Northern Lowlands"
    return "Highlands"

MARS = ["North Polar Cap", "South Polar Cap", "Olympus Mons", "Valles Marineris", "Hellas Planitia", "Argyre Planitia",
        "Tharsis", "Northern Lowlands", "Highlands"]

# Named features of the smaller worlds: (name, centre lat, centre lon (east positive), radius km).
FEATURES = {
    "Mercury": [("Caloris Basin", 30.5, 162.7, 775)],
    "Venus": [("Maxwell Montes", 65.2, 3.3, 450), ("Ishtar Terra", 70.4, 27.5, 2800)],
    "Ceres": [("Occator Crater", 19.82, -120.67, 46)],
    "Pluto": [("Sputnik Planitia", 20.0, 177.0, 600), ("Cthulhu Macula", -5.0, 100.0, 1100)],
    "Charon": [("Mordor Macula", 85.0, 0.0, 250)],
    "Triton": [],
    "Io": [("Loki Patera", 13.0, -51.0, 160), ("Pele", -18.7, -134.0, 300)],
    "Europa": [("Conamara Chaos", 9.7, -86.4, 120)],
    "Ganymede": [("Galileo Regio", 35.0, -145.0, 1600)],
    "Callisto": [("Valhalla", 15.0, -56.0, 1900)],
    "Titan": [("Xanadu", -10.0, -100.0, 1800), ("Kraken Mare", 68.0, -50.0, 600), ("Ligeia Mare", 79.0, -112.0, 250)],
    "Enceladus": [],
    "Phobos": [("Stickney Crater", 1.0, -49.0, 4.5)],
    "Deimos": [],
}

def other(world, radius_km):
    feats = FEATURES.get(world, [])
    def classify(lat, lon, h, c, ctx):
        if world == "Enceladus" and lat < -65:
            return "Tiger Stripes"
        if lat > 75:
            return "North Pole"
        if lat < -75:
            return "South Pole"
        for name, flat, flon, km in feats:
            if within(lat, lon, (flat, flon), km, radius_km):
                return name
        if h is not None:
            return "Lowlands" if h < ctx["low"] else "Highlands" if h > ctx["high"] else "Midlands"
        if c is not None:
            s = bright(c)
            return "Dark Terrain" if s < ctx["low"] else "Bright Terrain" if s > ctx["high"] else "Plains"
        return "Plains"
    names = (["Tiger Stripes"] if world == "Enceladus" else []) + ["North Pole", "South Pole"] + [f[0] for f in feats]
    return classify, names

def tercile(values):
    v = sorted(values)
    return v[len(v) // 3], v[2 * len(v) // 3]

def png(path, rows):
    """An 8-bit RGB PNG, written row by row as given (the first row at the top)."""
    W, H = len(rows[0]), len(rows)
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for c in row:
            raw += bytes(c)
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))

def make(world):
    sys.path.insert(0, HERE)
    from bodies import BODIES
    radius_km = BODIES[world]["radius"] / 1000.0
    big = world in ("Earth", "Moon", "Mars")
    W, H = (2048, 1024) if big else (1024, 512)
    hts = read_height(world, W, H)
    col = read_colour(world, W, H)
    if hts is None and col is None:
        print("%s: no maps, no biomes" % world)
        return None
    ctx = {}
    if world == "Earth":
        classify, names = earth, EARTH
    elif world == "Moon":
        classify, names = moon, MOON
        ctx["dark"] = sorted(bright(c) for row in col for c in row)[len(col) * W * 17 // 100]  # (the maria: about 17 % of the surface)
    elif world == "Mars":
        classify, names = mars, MARS
        ctx["vm"] = -1000
    else:
        classify, names = other(world, radius_km)
        if hts is not None:
            ctx["low"], ctx["high"] = tercile([h for row in hts for h in row[::4]])
            names += ["Lowlands", "Midlands", "Highlands"]
        else:
            ctx["low"], ctx["high"] = tercile([bright(c) for row in col for c in row[::4]])
            names += ["Dark Terrain", "Plains", "Bright Terrain"]
    colours = {n: PALETTE[k % len(PALETTE)] for k, n in enumerate(names)}
    counts = dict.fromkeys(names, 0)
    south_first = []
    for i in range(H):
        lat = lat_of(i, H)
        row = []
        for j in range(W):
            lon = lon_of(j, W)
            n = classify(lat, lon, hts[i][j] if hts else None, col[i][j] if col else None, ctx)
            counts[n] += 1
            row.append(colours[n])
        south_first.append(row)
    os.makedirs(os.path.join(OUT, world), exist_ok=True)
    png(os.path.join(OUT, world, "biomes.png"), south_first[::-1])
    used = [n for n in names if counts[n] > 0]
    share = ", ".join("%s %.1f%%" % (n, 100.0 * counts[n] / (W * H)) for n in used)
    print("%s: %s" % (world, share))
    return [{"name": n, "colour": colours[n]} for n in used]

def main():
    sys.path.insert(0, HERE)
    from bodies import BODIES
    worlds = sys.argv[1:] or [w for w, b in BODIES.items() if not b.get("giant") and w != "Sun"]
    made = json.load(open(MADE)) if os.path.exists(MADE) else {}
    for w in worlds:
        biomes = make(w)
        if biomes:
            e = made.setdefault(w, {})
            e["biomes"] = biomes
            e["textures"] = sorted(set(e.get("textures", [])) | {"biomes.png"})
    json.dump(made, open(MADE, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
