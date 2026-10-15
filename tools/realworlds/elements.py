#!/usr/bin/env python3
"""The real solar system's orbits for KSP, from JPL's published figures (2026-10-14).

KSP cannot tilt a body's axis of spin: every body turns about the game's one "up". So, as Real Solar System does, the
whole system is laid out against Earth's equator (J2000): Earth then spins upright as it should, and the Sun's path
across its sky is tilted 23.44 degrees to the equator, which gives the seasons. Every orbit is turned from the plane it
is published against (the ecliptic for the planets and the Moon; each planet's Laplace plane for its moons) into that
frame. Epoch: J2000 (2000-01-01 12:00 TDB) is the game's time nought.

    python3 tools/realworlds/elements.py            # prints each body's elements in Earth's equatorial frame
    python3 tools/realworlds/elements.py --json F   # and writes them to F

Sources (read 2026-10-14): JPL "Approximate Positions of the Planets", Table 1 (ecliptic J2000, 1800-2050);
JPL astrodynamic parameters (GM of the Sun, planets' systems, the Moon, the obliquity); JPL planetary physical
parameters (radii, spin); JPL planetary satellites' physical parameters and mean orbital elements (with each Laplace
plane's pole)."""
import json, math, sys

AU = 149597870.7                       # km
EPS = math.radians(84381.412 / 3600)   # obliquity of the ecliptic at J2000

def rx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]
def rz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]
def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def col(m, j):
    return [m[0][j], m[1][j], m[2][j]]
def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def dot(a, b):
    return sum(x * y for x, y in zip(a, b))
def norm(a):
    l = math.sqrt(dot(a, a))
    return [x / l for x in a]

def orientation(inc, node, peri):
    """The orbit's own axes (columns: towards periapsis, 90 degrees on, the pole) for elements in degrees."""
    return mul(mul(rz(math.radians(node)), rx(math.radians(inc))), rz(math.radians(peri)))

def elements_of(m):
    """Inclination, ascending node and argument of periapsis (degrees) of an orbit whose axes are m, against the frame's
    own xy-plane and x-axis."""
    p, w = col(m, 0), col(m, 2)
    inc = math.degrees(math.acos(max(-1.0, min(1.0, w[2]))))
    n = cross([0, 0, 1], w)
    if math.hypot(n[0], n[1]) < 1e-12:
        node, n = 0.0, [1.0, 0.0, 0.0]
    else:
        n = norm(n)
        node = math.degrees(math.atan2(n[1], n[0])) % 360
    q = cross(w, n)
    peri = math.degrees(math.atan2(dot(p, q), dot(p, n))) % 360
    return inc, node, peri

ECLIPTIC_TO_EQUATOR = rx(EPS)

# ---- the planets: JPL Table 1, ecliptic J2000 (a au, e, I, L, long.peri, long.node)
PLANETS = {
    "Mercury": (0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
    "Venus": (0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
    "Earth": (1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
    "Mars": (1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
    "Jupiter": (5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
    "Saturn": (9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
    "Uranus": (19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503),
    "Neptune": (30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
}
# (dwarf planets, ecliptic J2000, from JPL's small-body elements as commonly cited: a au, e, i, node, peri, M at J2000)
DWARFS = {
    "Ceres": (2.7675, 0.0758, 10.593, 80.305, 73.597, 77.372),
    "Pluto": (39.482, 0.2488, 17.140, 110.299, 113.834, 14.53),
}

# ---- the moons: JPL mean elements (a km, e, w, M, i, node), and the plane they are given against
MOONS = {
    "Moon": ("Earth", "ecliptic", (384400.0, 0.0554, 318.15, 135.27, 5.16, 125.08)),
    "Phobos": ("Mars", (317.7, 52.9), (9375.0, 0.015, 216.3, 189.7, 1.1, 169.2)),
    "Deimos": ("Mars", (316.6, 53.5), (23457.0, 0.000, 0.0, 205.0, 1.8, 54.3)),
    "Io": ("Jupiter", (268.1, 64.5), (421800.0, 0.004, 49.1, 330.9, 0.0, 0.0)),
    "Europa": ("Jupiter", (268.1, 64.5), (671100.0, 0.009, 45.0, 345.4, 0.5, 184.0)),
    "Ganymede": ("Jupiter", (268.2, 64.6), (1070400.0, 0.001, 198.3, 324.8, 0.2, 58.5)),
    "Callisto": ("Jupiter", (268.7, 64.8), (1882700.0, 0.007, 43.8, 87.4, 0.3, 309.1)),
    "Enceladus": ("Saturn", (40.6, 83.5), (238400.0, 0.005, 119.5, 57.0, 0.0, 0.0)),
    "Titan": ("Saturn", (36.4, 84.0), (1221900.0, 0.029, 78.3, 11.7, 0.3, 78.6)),
    "Triton": ("Neptune", (299.8, 43.1), (354800.0, 0.000, 0.0, 63.0, 157.3, 178.1)),
    # (Charon: against Pluto's equator, whose pole is RA 132.993, Dec -6.163 (IAU 2015))
    "Charon": ("Pluto", (132.993, -6.163), (19600.0, 0.000, 0.0, 304.1, 0.0, 0.0)),
}

def laplace_basis(ra, dec):
    """The axes of a plane whose pole is at (ra, dec) in Earth's equatorial frame: x along its ascending node on the
    equator, z its pole."""
    ra, dec = math.radians(ra), math.radians(dec)
    pole = [math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)]
    node = cross([0, 0, 1], pole)
    node = norm(node) if math.hypot(node[0], node[1]) > 1e-12 else [1.0, 0.0, 0.0]
    y = cross(pole, node)
    return [[node[0], y[0], pole[0]], [node[1], y[1], pole[1]], [node[2], y[2], pole[2]]]

def all_elements():
    out = {}
    for name, (a, e, I, L, varpi, node) in PLANETS.items():
        peri = varpi - node
        M = (L - varpi) % 360
        m = mul(ECLIPTIC_TO_EQUATOR, orientation(I, node, peri))
        inc, nd, pe = elements_of(m)
        out[name] = {"parent": "Sun", "sma_m": a * AU * 1000.0, "e": e, "inc": inc, "lan": nd, "aop": pe, "M0": M}
    for name, (a, e, I, node, peri, M) in DWARFS.items():
        m = mul(ECLIPTIC_TO_EQUATOR, orientation(I, node, peri))
        inc, nd, pe = elements_of(m)
        out[name] = {"parent": "Sun", "sma_m": a * AU * 1000.0, "e": e, "inc": inc, "lan": nd, "aop": pe, "M0": M % 360}
    for name, (parent, plane, (a, e, w, M, i, node)) in MOONS.items():
        if plane == "ecliptic":
            m = mul(ECLIPTIC_TO_EQUATOR, orientation(i, node, w))
        else:
            m = mul(laplace_basis(*plane), orientation(i, node, w))
        inc, nd, pe = elements_of(m)
        out[name] = {"parent": parent, "sma_m": a * 1000.0, "e": e, "inc": inc, "lan": nd, "aop": pe, "M0": M % 360}
    return out

if __name__ == "__main__":
    els = all_elements()
    for name, v in els.items():
        print("%-10s about %-8s a %16.1f km  e %.5f  i %8.4f  node %8.4f  peri %8.4f  M %8.4f" % (name, v["parent"], v["sma_m"] / 1000.0, v["e"], v["inc"], v["lan"], v["aop"], v["M0"]))
    if "--json" in sys.argv:
        json.dump(els, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
