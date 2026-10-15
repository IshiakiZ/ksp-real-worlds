#!/usr/bin/env python3
"""Real Worlds' textures, made from the maps sources.py downloads (2026-10-14).

    python3 tools/realworlds/make_textures.py [World ...]     # all the worlds whose maps are here, or those named

Each world gets, in src/RealWorlds/PluginData/<World>/ (not kept in git: made again from the maps):
  height.dds    16-bit heights for the terrain (R16), where the world has a measured height map
  colour.dds    its colour, for the terrain and for its far-away look (BC1, with mipmaps)
  normals.dds   the light and shade of its relief, for its far-away look (DXT5, x in alpha, y in green)
and tools/realworlds/made.json records each height map's range (the terrain's offset and deformity in the configs).

The work is done by maps.swift (compiled once into ~/.ksp-ai-bridge/tools/realworlds): see it for the layout the game wants.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from sources import SOURCES, SCRATCH  # noqa: E402
from bodies import BODIES  # noqa: E402

OUT = os.path.join(ROOT, "src", "RealWorlds", "PluginData")
MADE = os.path.join(HERE, "made.json")
TOOL = os.path.expanduser("~/.ksp-ai-bridge/tools/realworlds/maps")

def src(i, inner=None):
    world, what, name, url, size, credit = SOURCES[i]
    p = os.path.join(SCRATCH, i, name)
    if inner:
        return os.path.join(SCRATCH, i + "-x", inner)
    return p

def have(path):
    return os.path.exists(path)

# For each world: the jobs that make its textures. Sizes: 8192 x 4096 for Earth, the Moon and Mars (the worlds most landed
# on), 4096 x 2048 for the rest (the download stays near 350 MB); heights at the map's own size where it is smaller.
def jobs_for(world):
    out = os.path.join(OUT, world)
    R = BODIES[world]["radius"]
    J = []
    def height(**k): J.append(dict(kind="height", out=os.path.join(out, "height.dds"), **k))
    def colour(**k): J.append(dict(kind="colour", out=os.path.join(out, "colour.dds"), **k))
    def normals(**k): J.append(dict(kind="normals", out=os.path.join(out, "normals.dds"), radius=R, **k))
    if world == "Earth":
        dem = os.path.join(SCRATCH, "etopo-x", "ETOPO1_Ice_g_geotiff.tif")
        if not have(dem):
            return []
        height(**{"in": dem, "width": 8192, "height": 4096, "dropLast": True})
        normals(**{"in": dem, "width": 4096, "height": 2048, "dropLast": True, "floorAt": 0, "strength": 1})
        colour(**{"in": src("earth-colour"), "width": 8192, "height": 4096, "lon0": -180})
    elif world == "Moon":
        # (the kit's maps have longitude 0 in their middle; the heights are in km above 1737.4 km)
        height(**{"in": src("moon-height"), "width": 5760, "height": 2880, "lon0": -180, "scale": 1000})
        normals(**{"in": src("moon-height"), "width": 4096, "height": 2048, "lon0": -180, "scale": 1000})
        colour(**{"in": src("moon-colour"), "width": 8192, "height": 4096, "lon0": -180})
    elif world == "Mars":
        mola = {"in": src("mars-height"), "lon0": 0, "raw": {"width": 5760, "height": 2880, "type": "int16be"}}
        height(width=5760, height=2880, **mola)
        normals(width=4096, height=2048, **mola)
        colour(**{"in": src("mars-colour"), "width": 8192, "height": 4096, "nodata": 0})
    elif world == "Venus":
        height(**{"in": src("venus-height"), "width": 4096, "height": 2048, "nodata": -32768})
        normals(**{"in": src("venus-height"), "width": 2048, "height": 1024, "nodata": -32768})
    elif world == "Mercury":
        height(**{"in": src("mercury-height"), "width": 4096, "height": 2048, "nodata": -32768})
        normals(**{"in": src("mercury-height"), "width": 2048, "height": 1024, "nodata": -32768})
        # (MESSENGER's enhanced colour, taken back to its brightness alone, in Mercury's own grey-brown)
        colour(**{"in": src("mercury-colour"), "width": 4096, "height": 2048, "grey": True, "tint": [1.0, 0.94, 0.86], "nodata": 0})
    elif world == "Jupiter":
        colour(**{"in": src("jupiter-colour"), "width": 4096, "height": 2048, "lon0": -180})
    elif world == "Io":
        colour(**{"in": src("io-colour"), "width": 4096, "height": 2048, "nodata": 0})
    elif world == "Europa":
        # (the icy moons are among the brightest things in the Solar System, Europa's ice reflecting two thirds of the light,
        # Enceladus's four fifths, Triton's three quarters, against the Moon's eighth: their mosaics, stretched to a middling
        # grey, are lifted so that they read brighter than the Moon, as they are)
        colour(**{"in": src("europa-colour"), "width": 4096, "height": 2048, "grey": True, "gamma": 0.5, "tint": [1.0, 0.95, 0.87], "nodata": 0})
    elif world == "Ganymede":
        colour(**{"in": src("ganymede-colour"), "width": 4096, "height": 2048, "nodata": 0})
    elif world == "Callisto":
        colour(**{"in": src("callisto-colour"), "width": 4096, "height": 2048, "grey": True, "tint": [1.0, 0.92, 0.82], "nodata": 0})
    elif world == "Titan":
        colour(**{"in": src("titan-colour"), "width": 4096, "height": 2048, "grey": True, "tint": [1.0, 0.78, 0.52], "nodata": 0})
    elif world == "Enceladus":
        colour(**{"in": src("enceladus-colour"), "width": 4096, "height": 2048, "grey": True, "gamma": 0.45, "tint": [1.17, 1.19, 1.2], "nodata": 0})
    elif world == "Ceres":
        colour(**{"in": src("ceres-colour"), "width": 4096, "height": 2048, "grey": True, "tint": [1.0, 0.97, 0.93], "nodata": 0})
    elif world == "Phobos":
        colour(**{"in": src("phobos-colour"), "width": 2048, "height": 1024, "grey": True, "tint": [1.0, 0.88, 0.76], "nodata": 0})
    elif world == "Triton":
        # (Voyager's colour mosaic is green from its filters; Triton is a pale pinkish grey: its light and dark, tinted)
        colour(**{"in": src("triton-colour"), "width": 4096, "height": 2048, "grey": True, "gamma": 0.5, "tint": [1.0, 0.94, 0.91], "nodata": 0})
    elif world == "Pluto":
        # (Pluto reflects half the light that falls on it, four times what the Moon does: its mosaic lifted as the icy moons' are)
        colour(**{"in": src("pluto-colour"), "width": 4096, "height": 2048, "grey": True, "gamma": 0.65, "tint": [1.0, 0.86, 0.72], "nodata": 0})
    elif world == "Charon":
        colour(**{"in": src("charon-colour"), "width": 4096, "height": 2048, "grey": True, "tint": [1.0, 0.97, 0.94], "nodata": 0})
    # keep only the jobs whose maps are here
    return [j for j in J if have(j["in"])]

def build_tool():
    if not os.path.exists(TOOL) or os.path.getmtime(TOOL) < os.path.getmtime(os.path.join(HERE, "maps.swift")):
        os.makedirs(os.path.dirname(TOOL), exist_ok=True)
        subprocess.run(["swiftc", "-O", "-o", TOOL, os.path.join(HERE, "maps.swift")], check=True)

def main():
    worlds = sys.argv[1:] or list(BODIES)
    # the Earth's elevations come zipped: open the archive into a folder of its own
    zipped = os.path.join(SCRATCH, "earth-height", "ETOPO1_Ice_g_geotiff.zip")
    if "Earth" in worlds and have(zipped) and not have(os.path.join(SCRATCH, "etopo-x", "ETOPO1_Ice_g_geotiff.tif")):
        os.makedirs(os.path.join(SCRATCH, "etopo-x"), exist_ok=True)
        subprocess.run(["unzip", "-oq", zipped, "-d", os.path.join(SCRATCH, "etopo-x")], check=True)
    build_tool()
    made = json.load(open(MADE)) if os.path.exists(MADE) else {}
    for w in worlds:
        js = jobs_for(w)
        if not js:
            continue
        os.makedirs(os.path.join(OUT, w), exist_ok=True)
        path = os.path.join(os.path.dirname(TOOL), "jobs-%s.json" % w)
        json.dump(js, open(path, "w"), indent=1)
        r = subprocess.run([TOOL, path], check=True, capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        entry = made.setdefault(w, {})
        for line in r.stdout.splitlines():
            if "offset = " in line and line.startswith(os.path.join(OUT, w, "height.dds")):
                off = float(line.split("offset = ")[1].split(",")[0])
                dfm = float(line.split("deformity = ")[1].split(" ")[0])
                entry["height"] = {"offset": off, "deformity": dfm}
        entry["textures"] = sorted(os.path.basename(j["out"]) for j in js)
    json.dump(made, open(MADE, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
