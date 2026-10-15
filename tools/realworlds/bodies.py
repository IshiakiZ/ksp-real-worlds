#!/usr/bin/env python3
"""The real worlds' sizes, masses and spins, and which of the game's own worlds each one takes over (2026-10-14).

Sources (read 2026-10-14):
  GM (gravity) of the Sun and of each planet's body (its moons taken out): JPL's astrodynamic parameters (DE440).
  GM of moons: JPL's planetary satellite physical parameters. Ceres: Dawn (Konopliv et al. 2018), 62.6284 km^3/s^2.
  Radii (the mean, by volume, of each): JPL's planetary physical parameters and satellite physical parameters; the Sun's
  is the IAU 2015 nominal 695,700 km; Ceres 469.7 km (Dawn).
  Sidereal spin: JPL's planetary physical parameters (days; negative where a world turns backwards); the Sun's is the
  Carrington period, 25.38 days; Ceres 9.07417 h (Dawn).
  The prime meridians (where longitude 0 faces at J2000): the IAU WGCCRE 2015 rotation elements (alpha0 and W0), for the
  worlds that keep their own spin; a moon that keeps one face to its planet is turned to face it at J2000.
  Bond albedos: NASA's planetary fact sheets (planets, the Moon, Pluto); for the other moons, published geometric
  albedos (close enough for the warmth a craft gets back from them).
  Relief where no spacecraft has measured a global height map (amplitude m, feature size km, octaves): a made-up surface at
  the world's real range of heights (Phobos 27 x 22 x 18 km and Deimos 15 x 12 x 11 km, from their mean radii; the
  moons of Jupiter and Saturn, Ceres, Triton, Pluto and Charon from the relief seen by Galileo, Cassini, Dawn, Voyager 2
  and New Horizons).
  Highest ground above the mean (km), for where faster time warp is allowed: Mercury 4.5, Venus 11 (Maxwell Montes),
  Earth 8.85, the Moon 10.8, Mars 21.3 (Olympus Mons above the datum), Io 17.5 (Boosaule Montes), Pluto 6, the rest
  small.

KSP's limits: a world cannot be tilted (every world spins about the game's one axis: here Earth's), so each turns about
Earth's pole, and orbits are laid out against Earth's equator (see elements.py). Moons that face their planet are made to
in that frame; a moon whose orbit runs backwards in it (Triton, and Charon around Pluto, whose pole lies almost in
Earth's equator) is given a backward spin of its orbit's length instead.
"""

# the worlds in the game's order of listing; 'stock' is the game's own world it takes over ('new' are added, made from
# 'template'); km, km^3/s^2, days
BODIES = {
    "Sun": dict(stock="Sun", radius=695700.0, gm=1.32712440041279419e11, spin=25.38, albedo=0.0, highest=0.0,
                alpha0=286.13, w0=84.176, colour=(1.0, 0.95, 0.75)),
    "Mercury": dict(stock="Moho", radius=2439.4, gm=22031.868551, spin=58.6462, albedo=0.088, highest=4.5,
                    alpha0=281.0103, w0=329.5988, colour=(0.62, 0.6, 0.58)),
    "Venus": dict(stock="Eve", radius=6051.8, gm=324858.592, spin=-243.018, albedo=0.76, highest=11.0,
                  alpha0=272.76, w0=160.20, colour=(0.92, 0.82, 0.55)),
    "Earth": dict(stock="Kerbin", radius=6371.0084, gm=398600.435507, spin=0.99726968, albedo=0.306, highest=8.85,
                  colour=(0.3, 0.52, 1.0)),
    "Moon": dict(stock="Mun", parent="Earth", radius=1737.4, gm=4902.800118, spin="locked", albedo=0.11, highest=10.8,
                 colour=(0.7, 0.7, 0.7)),
    "Mars": dict(stock="Duna", radius=3389.5, gm=42828.375214, spin=1.02595676, albedo=0.25, highest=21.3,
                 alpha0=317.269202, w0=176.049863, colour=(0.9, 0.42, 0.2)),
    "Phobos": dict(relief=(2500, 9, 3), stock="Ike", parent="Mars", radius=11.08, gm=0.0007087, spin="locked", albedo=0.071, highest=1.0,
                   colour=(0.55, 0.5, 0.45)),
    "Deimos": dict(relief=(1200, 6, 3), stock="Gilly", parent="Mars", radius=6.2, gm=0.0000962, spin="locked", albedo=0.068, highest=0.5,
                   colour=(0.6, 0.55, 0.5)),
    "Ceres": dict(relief=(2500, 30, 7), stock="Dres", radius=469.7, gm=62.6284, spin=0.378090, albedo=0.034, highest=6.0,
                  alpha0=291.418, w0=170.65, colour=(0.6, 0.6, 0.6)),
    "Jupiter": dict(giant=True, stock="Jool", radius=69911.0, gm=126686531.9, spin=0.41354, albedo=0.343, highest=0.0,
                    alpha0=268.056595, w0=284.95, colour=(0.85, 0.7, 0.52)),
    "Io": dict(relief=(1500, 60, 7), stock="Pol", parent="Jupiter", radius=1821.49, gm=5959.91547, spin="locked", albedo=0.63, highest=17.5,
               colour=(0.95, 0.85, 0.45)),
    "Europa": dict(relief=(300, 20, 7), stock="Vall", parent="Jupiter", radius=1560.8, gm=3202.71210, spin="locked", albedo=0.68, highest=1.0,
                   colour=(0.85, 0.8, 0.72)),
    "Ganymede": dict(relief=(1000, 40, 7), stock="Tylo", parent="Jupiter", radius=2631.2, gm=9887.83275, spin="locked", albedo=0.44, highest=3.0,
                     colour=(0.7, 0.66, 0.62)),
    "Callisto": dict(relief=(1200, 40, 8), stock="Bop", parent="Jupiter", radius=2410.3, gm=7179.28340, spin="locked", albedo=0.13, highest=3.0,
                     colour=(0.5, 0.46, 0.42)),
    "Saturn": dict(giant=True, new=True, template="Jool", radius=58232.0, gm=37931206.234, spin=0.44401, albedo=0.342, highest=0.0,
                   alpha0=40.589, w0=38.90, colour=(0.92, 0.82, 0.58)),
    "Enceladus": dict(relief=(800, 15, 7), stock="Minmus", parent="Saturn", radius=252.1, gm=7.21037, spin="locked", albedo=0.81, highest=1.5,
                      colour=(0.95, 0.95, 0.97)),
    "Titan": dict(relief=(600, 40, 7), stock="Laythe", parent="Saturn", radius=2574.76, gm=8978.13710, spin="locked", albedo=0.27, highest=3.3,
                  colour=(0.9, 0.65, 0.3)),
    "Uranus": dict(giant=True, new=True, template="Jool", radius=25362.0, gm=5793951.256, spin=-0.71833, albedo=0.30, highest=0.0,
                   alpha0=257.311, w0=203.81, colour=(0.6, 0.85, 0.9)),
    "Neptune": dict(giant=True, new=True, template="Jool", radius=24622.0, gm=6835099.97, spin=0.67125, albedo=0.29, highest=0.0,
                    alpha0=299.36, w0=249.978, colour=(0.32, 0.48, 0.95)),
    "Triton": dict(relief=(500, 30, 7), new=True, template="Eeloo", parent="Neptune", radius=1352.6, gm=1428.49546, spin="locked",
                   albedo=0.76, highest=1.0, colour=(0.85, 0.8, 0.78)),
    "Pluto": dict(relief=(2500, 80, 7), stock="Eeloo", radius=1188.3, gm=869.4, spin=-6.3872, albedo=0.72, highest=6.0,
                  alpha0=132.993, w0=302.695, colour=(0.85, 0.72, 0.6)),
    "Charon": dict(relief=(2000, 60, 7), new=True, template="Ike", parent="Pluto", radius=606.0, gm=106.1, spin="locked", albedo=0.25,
                   highest=6.0, colour=(0.62, 0.6, 0.58)),
}

for _name, _b in BODIES.items():  # to the game's units: metres, m^3/s^2
    _b["radius"] = _b["radius"] * 1000.0
    _b["gm"] = _b["gm"] * 1e9
    _b.setdefault("parent", "Sun" if _name != "Sun" else None)
