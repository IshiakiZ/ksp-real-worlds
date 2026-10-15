#!/usr/bin/env python3
"""Real Worlds' Kopernicus configs, written from the figures in bodies.py, elements.py and air.py (2026-10-14).

    python3 tools/realworlds/make_configs.py     # writes src/RealWorlds/Configs/*.cfg (they are not edited by hand)

The game's own worlds are taken over where one fits (Kerbin becomes Earth, the Mun the Moon, Duna Mars, Jool Jupiter...),
keeping their names inside the game so that everything else that knows them (contracts, science, other mods' configs)
still finds them; what the player sees is the real name. The worlds the game lacks (Saturn, Uranus, Neptune, Triton,
Charon) are made from the nearest of its own.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import elements  # noqa: E402
import air  # noqa: E402
from bodies import BODIES  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "src", "RealWorlds", "Configs")
MOD = "RealWorlds"
MADE_PATH = os.path.join(HERE, "made.json")
MADE = json.load(open(MADE_PATH)) if os.path.exists(MADE_PATH) else {}
TEX = MOD + "/PluginData/"

# The stock worlds' terrain modifiers that make up heights or colours of their own: taken off where a measured map takes
# their place (names as the game's types, without PQSMod_; the probe of 2026-10-14 listed each world's).
MADE_UP_HEIGHTS = ["VertexHeightMap", "VertexRidgedAltitudeCurve", "VertexSimplexHeightAbsolute", "VertexHeightNoiseVertHeightCurve2",
                   "VertexSimplexHeight", "VertexHeightNoise", "VertexHeightNoiseVertHeight", "VertexSimplexHeightMap", "VoronoiCraters",
                   "VertexPlanet", "VertexHeightOffset", "FlattenOcean"]
MADE_UP_COLOURS = ["PQSLandControl", "VertexColorMap", "VertexColorMapBlend", "VertexSimplexNoiseColor", "HeightColorMap"]

# The colour of each atmosphere's glow from space, as the three wavelengths KSP's glow is worked out from (see body_block):
# Venus yellow-white (its haze), Titan orange, Jupiter a faint bluish white, Saturn pale yellow, Uranus cyan, Neptune blue.
# Earth keeps Kerbin's and Mars Duna's, which are right for them.
GLOW = {
    "Venus": (0.55, 0.57, 0.72),
    "Titan": (0.52, 0.62, 0.78),
    "Jupiter": (0.60, 0.58, 0.56),
    "Saturn": (0.56, 0.57, 0.62),
    "Uranus": (0.70, 0.58, 0.56),
    "Neptune": (0.72, 0.60, 0.52),
}

# Where each large world's far picture fades in over its terrain (metres up), see body_block.
FADE = {"Earth": (60000, 120000), "Venus": (60000, 120000), "Mars": (40000, 100000)}

# Fine detail under the measured maps (see body_block): metres high, kilometres across its widest waves.
DETAIL = {"Moon": (60, 3.0), "Mercury": (60, 3.0), "Mars": (50, 3.0), "Venus": (40, 3.0)}

# Launch sites taken out (see main): every one Making History adds, the island airfield among them.
SITES_OUT = ["Island_Airfield", "Woomerang_Launch_Site", "Desert_Airfield", "Desert_Launch_Site", "Crater_Launch_Site",
             "MahiMahi_Launch_Site", "Cove_Launch_Site", "GlacierLake_Launch_Site"]

def max_level(radius):
    """The terrain's finest level: points about 100 m apart at the ground (a cube face's edge is a quarter of the way round,
    halved at each level, with 15 points along a piece), never coarser than the game's own small moons (6)."""
    return max(6, int(math.ceil(math.log(math.pi / 2 * radius / (15 * 100.0), 2))))

# A short description for the tracking station (written here; figures from bodies.py and the fact sheets).
DESCRIPTIONS = {
    "Sun": "The star at the middle of it all: a ball of hydrogen and helium 1.39 million km across, holding 99.86 % of the system's mass.",
    "Mercury": "The smallest planet and the closest to the Sun: airless, cratered, baked to 430 C by day and frozen to -180 C by night. It turns three times for every two of its years.",
    "Venus": "Earth's near twin in size, under 92 bars of carbon dioxide and clouds of sulphuric acid. Its ground is hotter than Mercury's, about 465 C, day and night. It turns backwards, once every 243 days.",
    "Earth": "Home. A world of liquid water, 71 % ocean, under an atmosphere of nitrogen and oxygen. To orbit it takes about 9.4 km/s of speed.",
    "Moon": "Earth's only natural satellite, 384,400 km away, always turning the same face to us. Twelve people walked on it between 1969 and 1972.",
    "Mars": "A cold desert world under a thin carbon dioxide air, about 0.6 % of Earth's. Home to Olympus Mons, the tallest volcano known, and Valles Marineris, a canyon as long as the United States is wide.",
    "Phobos": "The larger and nearer of Mars's two small moons, 27 km long, so close that it rises in the west and crosses the sky twice a day. It is slowly falling towards Mars.",
    "Deimos": "The smaller and farther of Mars's moons, 15 km long, smooth under a blanket of dust.",
    "Ceres": "The largest body in the asteroid belt and a dwarf planet, 940 km across, with bright salt deposits in its craters. Visited by Dawn from 2015.",
    "Jupiter": "The largest planet, 318 times Earth's mass: hydrogen and helium in bands of cloud, with a storm larger than Earth that has blown for centuries. It has no surface to land on.",
    "Io": "The most volcanic world known, heated by Jupiter's tides; its volcanoes throw sulphur hundreds of kilometres high.",
    "Europa": "A moon of ice over a salty ocean deeper than all of Earth's together, one of the best places to look for life beyond Earth.",
    "Ganymede": "The largest moon in the Solar System, bigger than Mercury, the only moon with a magnetic field of its own.",
    "Callisto": "The most heavily cratered world known, an old surface of dark ice and rock, outside the worst of Jupiter's radiation.",
    "Saturn": "The ringed planet: hydrogen and helium, light enough on the whole to float in water, with rings 280,000 km across and mostly less than a hundred metres thick.",
    "Enceladus": "A small bright moon of Saturn whose south pole sprays water from an ocean under the ice into space.",
    "Titan": "Saturn's largest moon, with a thick nitrogen air, 1.5 bars at the ground, and lakes and rivers of liquid methane. Huygens landed there in 2005.",
    "Uranus": "An ice giant tipped on its side, turning backwards, its blue-green from methane in its air.",
    "Neptune": "The farthest planet, an ice giant with the fastest winds measured, up to 2,100 km/h.",
    "Triton": "Neptune's large moon, going round it backwards: probably a captured object from the Kuiper belt, with geysers of nitrogen.",
    "Pluto": "A dwarf planet of the Kuiper belt, with a heart-shaped plain of nitrogen ice and mountains of water ice. Visited by New Horizons in 2015.",
    "Charon": "Pluto's largest moon, half its size; the two face each other always, going round a point between them.",
}

STOCK_IDENTIFIER = {b["stock"]: "Squad/" + b["stock"] for b in BODIES.values() if "stock" in b}

def ident(name):
    """The body's identifier as Kopernicus knows it."""
    b = BODIES[name]
    return "Squad/" + b["stock"] if "stock" in b else MOD + "/" + name

def internal(name):
    b = BODIES[name]
    return b.get("stock", name)

def f(x, digits=10):
    """A number as a config writes it."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    s = ("%." + str(digits) + "g") % x
    return s

def era_at_j2000_tt():
    """The Earth's rotation angle at J2000.0 (2000-01-01 12:00 TT, the game's time nought): the IERS formula with UT1 at
    that moment (TT - UTC = 64.184 s, UT1 - UTC = +0.3550 s)."""
    du = (-64.184 + 0.355) / 86400.0
    return (360.0 * (0.7790572732640 + 1.00273781191135448 * du)) % 360.0

def kepler_position(el, t):
    """A body's direction from its parent (unit vector, Earth's equatorial frame) t seconds after J2000."""
    mu = BODIES[el["parent"]]["gm"] if el["parent"] in BODIES else None
    a = el["sma_m"]
    n = math.sqrt(mu / a ** 3)
    M = math.radians(el["M0"]) + n * t
    e = el["e"]
    E = M
    for _ in range(60):
        E = M + e * math.sin(E)
    nu = 2.0 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
    o = elements.orientation(el["inc"], el["lan"], el["aop"])
    p, q = elements.col(o, 0), elements.col(o, 1)
    return [math.cos(nu) * p[i] + math.sin(nu) * q[i] for i in range(3)], 2 * math.pi / n

def facing_rotation(el, backwards):
    """For a moon that keeps one face to its planet: the angle of its prime meridian at time nought that, turning
    uniformly at its orbit's rate (backwards where its orbit runs backwards in the game's frame), keeps it facing the
    planet on the mean over an orbit (the true direction swings about it, the moon's libration)."""
    _, period = kepler_position(el, 0.0)
    rate = (-360.0 if backwards else 360.0) / period
    n = 720
    sx = sy = 0.0
    for k in range(n):
        t = period * k / n
        r, _ = kepler_position(el, t)
        towards = math.atan2(-r[1], -r[0])  # from the moon to the planet, seen from above the pole
        a = towards - math.radians(rate * t)
        sx += math.cos(a)
        sy += math.sin(a)
    return math.degrees(math.atan2(sy, sx)) % 360.0, period

def warp_limits(name, top_km):
    """Rails time warp's lowest heights (m) for each of KSP's eight rates: a craft must not fall from its height into the
    air (or the highest ground) within one frame's step at that rate, at a quarter of low-orbit speed, at 50 frames a
    second."""
    b = BODIES[name]
    floor = top_km * 1000.0 if top_km else (b["highest"] * 1000.0 + max(2000.0, 0.002 * b["radius"]))
    v = math.sqrt(b["gm"] / (b["radius"] + floor))
    rates = [1, 5, 10, 50, 100, 1000, 10000, 100000]
    out = []
    for r in rates:
        if r == 1:
            out.append(0.0)
            continue
        out.append(floor + r / 50.0 * 0.25 * v)
    return out

def write_curve(lines, name, keys, indent):
    lines.append(indent + name)
    lines.append(indent + "{")
    for k in keys:
        lines.append(indent + "\tkey = " + " ".join(f(x, 8) for x in k))
    lines.append(indent + "}")

def body_block(name, els, ref_drag, tops):
    b = BODIES[name]
    new = b.get("new", False)
    L = []
    T = "\t\t"
    if new:
        L.append("\tBody")
        L.append("\t{")
        L.append(T + "name = " + name)
        L.append(T + "identifier = " + ident(name))
        L.append(T + "Template")
        L.append(T + "{")
        L.append(T + "\tname = " + b["template"])
        L.append(T + "}")
        P, O, A = "Properties", "Orbit", "Atmosphere"
    else:
        L.append("\t@Body[%s]" % b["stock"])
        L.append("\t{")
        if b["stock"] in ("Eve", "Laythe"):  # Venus and Titan: no sea of water
            L.append(T + "@Template")
            L.append(T + "{")
            L.append(T + "\t%removeOcean = true")
            L.append(T + "}")
        P, O, A = "@Properties", "%Orbit", "%Atmosphere"
    # -- size, mass, spin
    L.append(T + P)
    L.append(T + "{")
    p = T + "\t" + ("" if new else "%")
    L.append(p + "displayName = %s^N" % name)
    L.append(p + "description = " + DESCRIPTIONS[name])
    L.append(p + "radius = " + f(b["radius"]))
    L.append(p + "gravParameter = " + f(b["gm"], 15))
    spin = b["spin"]
    if name == "Sun":
        L.append(p + "rotationPeriod = " + f(spin * 86400.0))
        L.append(p + "initialRotation = " + f((b["alpha0"] + 90.0 + b["w0"]) % 360.0, 8))
    elif spin == "locked":
        el = els[name]
        backwards = el["inc"] > 90.0
        rot, period = facing_rotation(el, backwards)
        if backwards:
            L.append(p + "tidallyLocked = false")
            L.append(p + "rotationPeriod = " + f(-period))
        else:
            L.append(p + "tidallyLocked = true")
        L.append(p + "initialRotation = " + f(rot, 8))
    else:
        L.append(p + "tidallyLocked = false")
        # (Earth: the IERS rate, 1.00273781191135448 turns a day of UT1: 86164.0989 s, as era_at_j2000_tt counts it)
        L.append(p + "rotationPeriod = " + f(86400.0 / 1.00273781191135448 if name == "Earth" else spin * 86400.0))
        if name == "Earth":
            L.append(p + "initialRotation = " + f(era_at_j2000_tt(), 8))
        else:
            L.append(p + "initialRotation = " + f((b["alpha0"] + 90.0 + b["w0"]) % 360.0, 8))
    # (the period given is the world's turn against the stars, not its day: Kerbin's own counts its day instead)
    L.append(p + "solarRotationPeriod = false")
    if name != "Sun":
        L.append(p + "albedo = " + f(b["albedo"]))
        # (a moon so small and so close to its planet that the game's sphere of influence, a (m/M)^0.4, falls inside it, as
        # Phobos's does: the Hill sphere, where its own pull still holds a stone, so that the game can land on it)
        el = els[name]
        parent_gm = BODIES[b["parent"]]["gm"]
        laplace = el["sma_m"] * (b["gm"] / parent_gm) ** 0.4
        if laplace < 1.5 * b["radius"]:
            hill = el["sma_m"] * (1 - el["e"]) * (b["gm"] / (3 * parent_gm)) ** (1.0 / 3.0)
            L.append(p + "sphereOfInfluence = " + "%.0f" % max(hill, 1.5 * b["radius"]))
        top = tops.get(name, 0.0)
        L.append(p + "timewarpAltitudeLimits = " + " ".join("%.0f" % x for x in warp_limits(name, top)))
        floor = top * 1000.0 if top else b["highest"] * 1000.0
        L.append(p + "inverseRotThresholdAltitude = " + "%.0f" % max(floor * 1.15 + 10000.0, min(0.1 * b["radius"], 100000.0)))
    if name == "Earth":
        # the navball turns to orbit mode from 100 km up (90 km coming down), not from 6 % of Earth's radius (382 km)
        L.append(p + "navballSwitchRadiusMult = " + f(100000.0 / b["radius"], 6))
        L.append(p + "navballSwitchRadiusMultLow = " + f(90000.0 / b["radius"], 6))
    biomes = MADE.get(name, {}).get("biomes")
    if biomes:
        # -- its regions for science, from its own maps (make_biomes.py), in place of the template's
        L.append(p + "biomeMap = " + TEX + name + "/biomes.png")
        if not new:
            L.append(T + "\t!Biomes {}")
        L.append(T + "\tBiomes")
        L.append(T + "\t{")
        for bm in biomes:
            r, g, bl = bm["colour"]
            L += [T + "\t\tBiome", T + "\t\t{", T + "\t\t\tname = " + bm["name"].replace(" ", "").replace("-", ""),
                  T + "\t\t\tdisplayName = " + bm["name"], T + "\t\t\tvalue = 1",
                  T + "\t\t\tcolor = %.4f,%.4f,%.4f,1" % (r / 255.0, g / 255.0, bl / 255.0), T + "\t\t}"]
        L.append(T + "\t}")
    L.append(T + "}")
    # -- orbit
    if name != "Sun":
        el = els[name]
        L.append(T + O)
        L.append(T + "{")
        q = T + "\t" + ("" if new else "%")
        L.append(q + "referenceBody = " + ident(b["parent"]))
        L.append(q + "semiMajorAxis = " + f(el["sma_m"], 12))
        L.append(q + "eccentricity = " + f(el["e"], 8))
        L.append(q + "inclination = " + f(el["inc"], 8))
        L.append(q + "longitudeOfAscendingNode = " + f(el["lan"], 8))
        L.append(q + "argumentOfPeriapsis = " + f(el["aop"], 8))
        L.append(q + "meanAnomalyAtEpochD = " + f(el["M0"], 8))
        L.append(q + "epoch = 0")
        c = b["colour"]
        L.append(q + "color = %.3f,%.3f,%.3f,1" % c)
        L.append(T + "}")
    # -- air
    if name in air.ATMOSPHERES:
        a = air.Air(name, b["gm"], b["radius"])
        top = tops[name]
        pk, tk = air.curve_keys(a, top)
        L.append(T + A)
        L.append(T + "{")
        q = T + "\t" + ("" if new else "%")
        L.append(q + "enabled = true")
        L.append(q + "oxygen = " + f(a.oxygen))
        L.append(q + "altitude = " + "%.0f" % (top * 1000.0))
        L.append(q + "staticPressureASL = " + f(a.p0 / 1000.0, 8))
        L.append(q + "temperatureSeaLevel = " + f(a.temperature(0.0), 6))
        L.append(q + "atmosphereMolarMass = " + f(a.molar, 8))
        L.append(q + "adiabaticIndex = " + f(a.gamma, 4))
        if name in GLOW:
            # (the glow round the world seen from space, where Scatterer does not draw its sky: KSP colours it by 1/wavelength^4
            # of these three, so the shortest is the brightest. The templates' were Eve's purple, Laythe's blue, Jool's green.)
            L.append(T + "\t" + ("AtmosphereFromGround" if new else "%AtmosphereFromGround"))
            L.append(T + "\t{")
            L.append(T + "\t\t" + ("" if new else "%") + "waveLength = %.2f,%.2f,%.2f,0.5" % GLOW[name])
            L.append(T + "\t}")
        L.append(q + "pressureCurveIsNormalized = false")
        L.append(q + "temperatureCurveIsNormalized = false")
        if not new:
            for c in ("pressureCurve", "temperatureCurve"):
                L.append(T + "\t!%s {}" % c)
        write_curve(L, "pressureCurve", pk, T + "\t")
        write_curve(L, "temperatureCurve", tk, T + "\t")
        if a.weather == "still":
            # (no change of air temperature over a day or with latitude: Venus's and Titan's thick air hardly varies, and
            # the giants have no ground to warm)
            for c in ("temperatureSunMultCurve", "temperatureLatitudeBiasCurve", "temperatureLatitudeSunMultCurve",
                      "temperatureAxialSunBiasCurve", "temperatureAxialSunMultCurve", "temperatureEccentricityBiasCurve"):
                if not new:
                    L.append(T + "\t!%s {}" % c)
                write_curve(L, c, [(0, 0, 0, 0), (1, 0, 0, 0)], T + "\t")
        else:
            # (the template's own variations over a day and with latitude are kept as the game has them)
            pass
        L.append(T + "}")
    made = MADE.get(name, {})
    texs = made.get("textures", [])
    if not b.get("giant") and name != "Sun":
        # -- the terrain: its finest level for its size, and the measured maps in place of the template's made-up ones
        heights = "height.dds" in texs
        colours = "colour.dds" in texs
        relief = b.get("relief") if not heights else None
        take = (MADE_UP_HEIGHTS if heights or relief else []) + (MADE_UP_COLOURS if colours else [])
        if take:
            if new:
                L.insert(L.index(T + "Template") + 3, T + "\tremovePQSMods = " + ", ".join(take))
            else:
                L.append(T + "@Template")
                L.append(T + "{")
                L.append(T + "\t%removePQSMods = " + ", ".join(take))
                L.append(T + "}")
        L.append(T + ("PQS" if new else "@PQS"))
        L.append(T + "{")
        q = T + "\t" + ("" if new else "%")
        L.append(q + "maxLevel = %d" % max_level(b["radius"]))
        if heights or colours or relief:
            L.append(T + "\t" + ("Mods" if new else "%Mods"))
            L.append(T + "\t{")
            if heights:
                h = made["height"]
                L += [T + "\t\tVertexHeightMap", T + "\t\t{",
                      T + "\t\t\tmap = " + TEX + name + "/height.dds",
                      T + "\t\t\toffset = " + f(h["offset"]),
                      T + "\t\t\tdeformity = " + f(h["deformity"]),
                      T + "\t\t\tscaleDeformityByRadius = false",
                      T + "\t\t\torder = 10", T + "\t\t\tenabled = true", T + "\t\t}"]
            if heights and name in DETAIL:
                # (below the map's own pixels, two to five kilometres apart, the ground would be smooth slopes: a light noise
                # from about 3 km down to 200 m, a few tens of metres high. Only on worlds with no sea: on Earth it would
                # raise the low coasts out of the water.)
                amp, size_km = DETAIL[name]
                L += [T + "\t\tVertexSimplexHeightAbsolute", T + "\t\t{",
                      T + "\t\t\tdeformity = %d" % amp,
                      T + "\t\t\tfrequency = " + f(b["radius"] / (size_km * 1000.0), 5),
                      T + "\t\t\toctaves = 5",
                      T + "\t\t\tpersistence = 0.45",
                      T + "\t\t\tseed = %d" % (sum(ord(ch) * 7907 ** i for i, ch in enumerate(name)) % 100000000),
                      T + "\t\t\torder = 15", T + "\t\t\tenabled = true", T + "\t\t}"]
            if relief:
                # (no measured heights: a made-up surface at the world's real range of heights, in place of the template's,
                # which was made for a world ten to a hundred times smaller)
                amp, size_km, octaves = relief
                L += [T + "\t\tVertexSimplexHeightAbsolute", T + "\t\t{",
                      T + "\t\t\tdeformity = %d" % amp,
                      T + "\t\t\tfrequency = " + f(b["radius"] / (size_km * 1000.0), 5),
                      T + "\t\t\toctaves = %d" % octaves,
                      T + "\t\t\tpersistence = 0.5",
                      T + "\t\t\tseed = %d" % (sum(ord(ch) * 7919 ** i for i, ch in enumerate(name)) % 100000000),
                      T + "\t\t\torder = 10", T + "\t\t\tenabled = true", T + "\t\t}"]
            if colours:
                L += [T + "\t\tVertexColorMap", T + "\t\t{",
                      T + "\t\t\tmap = " + TEX + name + "/colour.dds",
                      T + "\t\t\torder = 20", T + "\t\t\tenabled = true", T + "\t\t}"]
            L.append(T + "\t}")
        L.append(T + "}")
    if "colour.dds" in texs:
        # -- its far-away look: the same colour, and the light and shade of its relief where its heights are measured
        L.append(T + ("ScaledVersion" if new else "@ScaledVersion"))
        L.append(T + "{")
        if b.get("giant"):
            # (the plain lit planet: Jool's own shader is stripped by Kopernicus from any Jool not of Jool's size, and what is
            # left takes no new picture; a gas giant seen from afar is a lit disc darkening to its edge, which this gives)
            L.append(T + "\t" + ("" if new else "%") + "type = Vacuum")
        if name in FADE:
            # (where the far picture takes over from the terrain, in metres up: the template's were for a world a tenth the
            # size, and from 10 km up Earth's mountains would have gone flat; the terrain now shows to fadeStart)
            L.append(T + "\t" + ("" if new else "%") + "fadeStart = %d" % FADE[name][0])
            L.append(T + "\t" + ("" if new else "%") + "fadeEnd = %d" % FADE[name][1])
        L.append(T + "\t" + ("Material" if new else "%Material"))
        L.append(T + "\t{")
        # (every template's own tint and shine are the stock world's, not the real one's: Vall's grey 0.6 made Europa darker
        # than the Moon, Minmus's tint and minty shine lay on Enceladus, Jool tints its picture green. White, and no shine,
        # but on Earth, whose seas glint from space)
        L.append(T + "\t\t" + ("" if new else "%") + "color = 1,1,1,1")
        if name != "Earth":
            L.append(T + "\t\t" + ("" if new else "%") + "specColor = 0,0,0,1")
        # (Venus: its cloud tops, not its ground, are what is seen from space)
        far = "clouds.dds" if "clouds.dds" in texs else "colour.dds"
        L.append(T + "\t\t" + ("" if new else "%") + "texture = " + TEX + name + "/" + far)
        if "normals.dds" in texs and far == "colour.dds":
            L.append(T + "\t\t" + ("" if new else "%") + "normals = " + TEX + name + "/normals.dds")
        elif b.get("giant") or far == "clouds.dds":
            # (a giant's template normal map is Jool's own swirls of cloud, which would shade bands that are not there, and Eve's
            # is its hills, under Venus's cloud tops and Titan's haze: flat)
            # (the giants are drawn with the plain far shader, Jool's template's and the one Worlds.cs gives Jupiter, which reads
            # a normal's sideways part from alpha: theirs is written for it; see draw_textures.flat_normals)
            L.append(T + "\t\t" + ("" if new else "%") + "normals = " + TEX + ("flat_normals_alpha.dds" if b.get("giant") else "flat_normals.dds"))
        else:
            # (a world whose relief is not measured kept its template's normal map: the stock moon's own hills and craters
            # shaded over the real one's map from afar (Pol's lumps on Io, Vall's on Europa). Flat, for the plain shader the
            # airless worlds are drawn with: the mosaics carry the light and shade of their photographs already)
            L.append(T + "\t\t" + ("" if new else "%") + "normals = " + TEX + "flat_normals_alpha.dds")
        if not new and not b.get("giant") and "rim.dds" in texs:
            # (a world drawn with KSP's rim shader has its edge coloured by a ramp: Eve's is purple and Laythe's blue; Venus's
            # and Titan's are their own colours. Jupiter's material is replaced in Worlds.cs.)
            L.append(T + "\t\t%rimColorRamp = " + TEX + name + "/rim.dds")
        L.append(T + "\t}")
        L.append(T + "}")
    if "rings" in made:
        # -- Saturn's rings: their measured radii (in thousandths of the planet's radius, as Kopernicus counts a ring), in
        # the planet's real equatorial plane (pole RA 40.589, Dec 83.537: tilted 6.463 degrees to Earth's equator, rising
        # at RA 130.589; the plane Titan's and Enceladus's orbits lie in, as they do)
        rg = made["rings"]
        L += [T + "Rings", T + "{", T + "\tRing", T + "\t{",
              T + "\t\tinnerRadius = " + f(1000.0 * rg["inner_km"] * 1000.0 / b["radius"], 7),
              T + "\t\touterRadius = " + f(1000.0 * rg["outer_km"] * 1000.0 / b["radius"], 7),
              T + "\t\tangle = 6.463", T + "\t\tlongitudeOfAscendingNode = 130.589",
              T + "\t\ttexture = " + TEX + name + "/rings.dds",
              T + "\t\tcolor = 1,1,1,1", T + "\t\tlockRotation = false", T + "\t\tunlit = false", T + "\t\tuseNewShader = true",
              T + "\t}", T + "}"]
    if name == "Sun":
        L.append(T + "@ScaledVersion")
        L.append(T + "{")
        L.append(T + "\t%Light")
        L.append(T + "\t{")
        L.append(T + "\t\t%sunAU = " + f(elements.AU * 1000.0, 12))
        L.append(T + "\t\t%luminosity = 1360.8")
        L.append(T + "\t}")
        L.append(T + "}")
    if name == "Earth":
        # Cape Canaveral, Launch Complex 39A
        L.append(T + "%SpaceCenter")
        L.append(T + "{")
        L.append(T + "\t%latitude = 28.608389")
        L.append(T + "\t%longitude = -80.604333")
        L.append(T + "\t%decalLatitude = 28.608389")
        L.append(T + "\t%decalLongitude = -80.604333")
        # (the stock centre stands on a 65 m plateau, its decal raising the ground to that; the Cape is a few metres above
        # the sea: both brought down by 60 m, the ground under the buildings to about 5 m)
        L.append(T + "\t%absoluteOffset = -60")
        # (and the flattened ground no wider than the centre itself: the stock 7.5 km pushed the Atlantic's shore out into a
        # circle round it)
        L.append(T + "\t%radius = 3000")
        L.append(T + "\t%repositionRadiusOffset = -17.3")
        L.append(T + "}")
    L.append("\t}")
    return L

def main():
    els = elements.all_elements()
    ref = air.earth_reference_drag(BODIES["Earth"]["gm"], BODIES["Earth"]["radius"])
    tops = {}
    for name in air.ATMOSPHERES:
        b = BODIES[name]
        tops[name] = air.ceiling(air.Air(name, b["gm"], b["radius"]), ref)
    os.makedirs(OUT, exist_ok=True)
    header = ["// Real Worlds: %s.", "// Written by tools/realworlds/make_configs.py from NASA's and JPL's figures; do not edit by hand.", ""]
    written = []
    for name in BODIES:
        lines = [header[0] % name, header[1], header[2], "@Kopernicus:FOR[%s]" % MOD, "{"]
        if name == "Earth":
            # (Making History's launch sites, and the island airfield it makes one of, stand where they stood on Kerbin: on the
            # real Earth the desert sites, the crater and Mahi Mahi are three to six kilometres under the Pacific, Woomerang in
            # the mountains of Russia's Far East, the airfield in the Amazon. They are taken out until they are moved to real
            # sites. Kopernicus removes them only where Making History is installed.)
            lines.append("\tremoveLaunchSites = " + ", ".join(SITES_OUT))
        lines += body_block(name, els, ref, tops)
        lines.append("}")
        path = os.path.join(OUT, name + ".cfg")
        with open(path, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        written.append(path)
    # The terrain's finest level, by the game's own detail setting: KSP's presets (Low, Default, High) set each world's
    # deepest subdivision and override the world's own; the real worlds' are put in them (High: points about 100 m apart
    # at the ground; Default one level coarser; Low two).
    lines = ["// Real Worlds: the terrain's finest level for each world, in each of the game's terrain detail settings.",
             "// Written by tools/realworlds/make_configs.py; do not edit by hand.", "",
             "@Kopernicus:FOR[%s]" % MOD, "{"]
    for preset, less in (("Low", 2), ("Default", 1), ("High", 0)):
        lines += ["\tPreset", "\t{", "\t\tname = " + preset]
        for name, b in BODIES.items():
            if b.get("giant") or name == "Sun":
                continue
            lines += ["\t\tPLANET", "\t\t{", "\t\t\tname = " + internal(name), "\t\t\tminDistance = 6", "\t\t\tminSubdivision = 2",
                      "\t\t\tmaxSubdivision = %d" % max(6, max_level(b["radius"]) - less), "\t\t}"]
        lines += ["\t}"]
    lines += ["}", ""]
    with open(os.path.join(OUT, "Presets.cfg"), "w") as fh:
        fh.write("\n".join(lines))
    # The game's start: the asteroid generator made for the stock worlds is put aside (it lays asteroids on Kerbin and
    # Dres's paths); Kopernicus's own lays none until asteroids are given it.
    with open(os.path.join(OUT, "Settings.cfg"), "w") as fh:
        fh.write("\n".join([
            "// Real Worlds: Kopernicus's settings that the real system needs.",
            "// Written by tools/realworlds/make_configs.py; do not edit by hand.",
            "",
            "@Kopernicus_config:FOR[%s]" % MOD,
            "{",
            "\t%UseKopernicusAsteroidSystem = True",
            "}",
            "",
        ]))
    for p in written:
        print(os.path.relpath(p, os.path.join(HERE, "..", "..")))
    print("air ends at: " + ", ".join("%s %.0f km" % (n, t) for n, t in tops.items()))

if __name__ == "__main__":
    main()
