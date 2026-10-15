#!/usr/bin/env python3
"""The real worlds' air, as KSP's curves of pressure and temperature by height (2026-10-14).

Each atmosphere is built the way the reference atmospheres themselves are: a measured profile of temperature with height,
the pressure at the ground (or at the 1 bar level of a giant planet), the gas's mean molar mass, and the world's own
gravity, with the pressure worked out from them by hydrostatic balance. Where a measured table of pressure exists it is
used as it stands (Earth: the 1976 US Standard Atmosphere; Venus: VIRA up to 100 km).

Where the air ends (where KSP's atmosphere stops and time warp on rails is allowed) is put at the same drag for every
world: the height at which a craft in a circular orbit meets the dynamic pressure that it meets at 140 km above Earth
(KSP's ceiling for Earth, where an orbit decays in about a day). So a thin, cold, slow-orbit air like Titan's reaches
far higher than Earth's, as it does.

    python3 tools/realworlds/air.py     # prints each atmosphere's figures, for checking

Sources (read 2026-10-14):
  Earth    U.S. Standard Atmosphere 1976 (COESA), as tabulated by Public Domain Aeronautical Software
           (pdas.com/bigtables.html, 5 km steps), and its defining temperature profile.
  Venus    VIRA (Seiff et al. 1985) 0-100 km, as listed in Wikipedia's "Atmosphere of Venus"; above 100 km a day-night
           mean of the thermosphere (day 250-350 K above 110 km, night about 100 K above 150 km).
  Mars     Viking 1 and 2 entry profiles (Seiff & Kirk 1977, NASA PDS atmospheres node, marstemppres.txt), their mean,
           smoothed; the ground brought to the global mean (about 210 K); 610 Pa at the datum.
  Titan    Huygens HASI (Fulchignoni et al. 2005): 1467 hPa and 93.65 K at the ground, tropopause about 70 K at 44 km,
           stratopause about 187 K at 250 km, mesopause near 500 km, about 170 K from 500 to 1100 km.
  Jupiter  Galileo probe and the review figures in Wikipedia's "Atmosphere of Jupiter": 166 K at 1 bar, tropopause 110 K
           at 0.1 bar about 50 km up, about 200 K at 320 km (1 microbar), 1000 K at about 1000 km (1 nanobar).
  Saturn   134 K at 1 bar, about 90 K at the 0.1 bar tropopause; a warm thermosphere (about 400 K) above.
  Uranus   76 K at 1 bar, 53 K at the 0.1 bar tropopause (50 km), 100-130 K at 160-320 km, rising to 800-850 K at
           4000 km (Wikipedia, "Atmosphere of Uranus", from Voyager 2).
  Neptune  72 K at 1 bar, 55 K at the 0.1 bar tropopause, a thermosphere of about 750 K (Voyager 2).
  Molar masses: NASA planetary fact sheets (Venus 43.45, Earth 28.97, Mars 43.34, Saturn 2.07 g/mol); Jupiter from the
  Galileo probe's helium (He/H2 = 0.157 by number: 2.29); Uranus 2.32 (H2 and 15.2 % helium, its methane frozen out
  below the 1 bar level); Neptune 2.61 (80 % H2, 19 % He, 1.5 % CH4); Titan 27.8 (98.4 % N2, 1.4 % CH4).
"""
import math

RGAS = 8.314462618  # J/(mol K)

def lerp_table(table, x):
    """Piecewise-linear value of a list of (x, y) points, held flat beyond its ends."""
    if x <= table[0][0]:
        return table[0][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[-1][1]

# ---- Earth: the 1976 US Standard Atmosphere ------------------------------------------------------------------------
R0_USSA = 6356.766  # km, the standard's own radius for geopotential height
USSA_LAYERS = [(0.0, -6.5), (11.0, 0.0), (20.0, 1.0), (32.0, 2.8), (47.0, 0.0), (51.0, -2.8), (71.0, -2.0), (84.852, None)]

def ussa_temperature(z_km):
    """The standard's temperature (K) at geometric height z (km), from its defining formulas."""
    if z_km < 86.0:
        h = R0_USSA * z_km / (R0_USSA + z_km)  # geopotential
        t = 288.15
        for (hb, lapse), (hn, _) in zip(USSA_LAYERS, USSA_LAYERS[1:]):
            if h <= hn or lapse is None:
                return t + lapse * (h - hb)
            t += lapse * (hn - hb)
        return t
    if z_km < 91.0:
        return 186.8673
    if z_km < 110.0:
        return 263.1905 - 76.3232 * math.sqrt(max(0.0, 1.0 - ((z_km - 91.0) / -19.9429) ** 2))
    if z_km < 120.0:
        return 240.0 + 12.0 * (z_km - 110.0)
    xi = (z_km - 120.0) * (R0_USSA + 120.0) / (R0_USSA + z_km)
    return 1000.0 - 640.0 * math.exp(-0.01875 * xi)

# The standard's pressures (Pa), geometric km, from the PDAS tabulation.
USSA_P = [(0, 1.0132e5), (5, 5.4048e4), (10, 2.6500e4), (15, 1.2112e4), (20, 5.5293e3), (25, 2.5492e3), (30, 1.1970e3),
          (35, 5.7459e2), (40, 2.8714e2), (45, 1.4910e2), (50, 7.9779e1), (55, 4.2525e1), (60, 2.1959e1), (65, 1.0930e1),
          (70, 5.2209e0), (75, 2.3881e0), (80, 1.0525e0), (85, 4.4568e-1), (90, 1.8435e-1), (95, 7.5775e-2),
          (100, 3.2012e-2), (105, 1.4423e-2), (110, 7.1493e-3), (115, 4.0037e-3), (120, 2.5366e-3), (125, 1.7360e-3),
          (130, 1.2503e-3), (135, 9.3569e-4), (140, 7.2029e-4), (145, 5.6690e-4), (150, 4.5422e-4)]
USSA_P[0] = (0, 101325.0)

# ---- Venus: VIRA, 0-100 km (deg C and bar as listed) ---------------------------------------------------------------
VIRA = [(0, 462, 92.10), (5, 424, 66.65), (10, 385, 47.39), (15, 348, 33.04), (20, 306, 22.52), (25, 264, 14.93),
        (30, 222, 9.851), (35, 180, 5.917), (40, 143, 3.501), (45, 110, 1.979), (50, 75, 1.066), (55, 27, 0.5314),
        (60, -10, 0.2357), (65, -30, 0.09765), (70, -43, 0.03690), (80, -76, 0.004760), (90, -104, 0.0003736),
        (100, -112, 0.00002660)]
VENUS_T = [(-3, 757.0)] + [(z, c + 273.15) for z, c, _ in VIRA] + [(110, 172.0), (120, 186.0), (130, 197.0), (150, 215.0), (200, 230.0)]
VENUS_P = [(z, b * 1e5) for z, _, b in VIRA]

# ---- Mars: the Viking entries' mean, smoothed; ground to the global mean ---------------------------------------------
MARS_T = [(-10, 236.0), (0, 214.0), (5, 206.0), (10, 199.0), (20, 187.0), (28, 177.0), (32, 171.0), (36, 165.0),
          (40, 160.0), (44, 158.0), (48, 156.0), (52, 151.0), (56, 145.0), (60, 144.0), (64, 147.0), (68, 145.0),
          (72, 137.0), (76, 131.0), (80, 134.0), (84, 142.0), (88, 147.0), (92, 147.0), (96, 148.0), (100, 147.0),
          (104, 142.0), (108, 136.0), (112, 133.0), (116, 131.0), (120, 130.0), (130, 145.0), (140, 165.0), (160, 190.0),
          (200, 210.0)]

# ---- Titan: Huygens HASI ---------------------------------------------------------------------------------------------
TITAN_T = [(-1, 94.5), (0, 93.65), (10, 85.0), (20, 78.0), (32, 72.0), (44, 70.4), (60, 95.0), (80, 125.0), (100, 140.0),
           (150, 165.0), (200, 180.0), (250, 187.0), (300, 182.0), (350, 175.0), (400, 165.0), (450, 157.0), (500, 152.0),
           (600, 165.0), (700, 170.0), (1100, 170.0), (1500, 170.0)]

# ---- the giant planets (height from the 1 bar level) ------------------------------------------------------------------
JUPITER_T = [(0, 166.0), (20, 145.0), (50, 110.0), (80, 125.0), (120, 155.0), (200, 175.0), (320, 200.0), (350, 400.0),
             (400, 600.0), (500, 800.0), (700, 950.0), (1000, 1000.0), (2000, 1000.0)]
SATURN_T = [(0, 134.0), (40, 108.0), (90, 88.0), (150, 110.0), (250, 135.0), (400, 145.0), (500, 200.0), (700, 350.0),
            (1000, 420.0), (3000, 420.0)]
URANUS_T = [(0, 76.0), (25, 60.0), (50, 53.0), (100, 62.0), (160, 100.0), (320, 130.0), (500, 300.0), (1000, 550.0),
            (2000, 750.0), (4000, 810.0), (6000, 830.0)]
NEPTUNE_T = [(0, 72.0), (20, 60.0), (40, 55.0), (100, 85.0), (200, 140.0), (300, 160.0), (500, 300.0), (800, 550.0),
             (1200, 700.0), (2000, 750.0), (5000, 750.0)]

# name: (ground pressure Pa, temperature table, molar mass kg/mol, adiabatic index, oxygen, pressure table or None,
#        lowest height km, how the air's temperature changes over a day and with latitude ('stock': the template's own
#        curves are kept; 'still': none))
ATMOSPHERES = {
    "Earth": (101325.0, None, 0.0289644, 1.40, True, USSA_P, -1.0, "stock"),
    "Venus": (92.10e5, VENUS_T, 0.04345, 1.25, False, VENUS_P, -3.0, "still"),
    "Mars": (610.0, MARS_T, 0.04334, 1.29, False, None, -10.0, "stock"),
    "Titan": (146700.0, TITAN_T, 0.0278, 1.40, False, None, -1.0, "still"),
    "Jupiter": (1.0e5, JUPITER_T, 0.00229, 1.45, False, None, 0.0, "still"),
    "Saturn": (1.0e5, SATURN_T, 0.00207, 1.45, False, None, 0.0, "still"),
    "Uranus": (1.0e5, URANUS_T, 0.00232, 1.45, False, None, 0.0, "still"),
    "Neptune": (1.0e5, NEPTUNE_T, 0.00261, 1.45, False, None, 0.0, "still"),
}

EARTH_CEILING_KM = 140.0

class Air:
    """One world's air: pressure (Pa) and temperature (K) at any height (m), worked out on a fine grid."""
    def __init__(self, name, gm, radius):
        p0, ttab, molar, gamma, oxygen, ptab, lowest, weather = ATMOSPHERES[name]
        self.name, self.gm, self.radius, self.molar, self.gamma, self.oxygen, self.weather = name, gm, radius, molar, gamma, oxygen, weather
        self.p0 = p0
        self.temperature = (lambda z: ussa_temperature(max(z, 0.0)) + (6.5 * -z if z < 0 else 0.0)) if ttab is None else (lambda z, t=ttab: lerp_table(t, z))
        self.step = 0.05  # km
        self.z0 = lowest
        top = 6000.0
        n = int((top - lowest) / self.step) + 1
        self.zs = [lowest + i * self.step for i in range(n)]
        # hydrostatic balance from the ground (z = 0) up and down
        lnp = [0.0] * n
        i0 = int(round(-lowest / self.step))
        lnp[i0] = math.log(p0)
        def k(z):  # d ln p / dz, per km
            g = gm / (radius + z * 1000.0) ** 2
            return -molar * g / (RGAS * self.temperature(z)) * 1000.0
        for i in range(i0, n - 1):
            z = self.zs[i]
            lnp[i + 1] = lnp[i] + 0.5 * (k(z) + k(z + self.step)) * self.step
        for i in range(i0, 0, -1):
            z = self.zs[i]
            lnp[i - 1] = lnp[i] - 0.5 * (k(z) + k(z - self.step)) * self.step
        if ptab is not None:
            # the measured pressures where they are given: between two of them the pressure falls exponentially at the
            # rate they set, and the hydrostatic shape is kept beyond the last (joined smoothly at it)
            last_z, last_p = ptab[-1]
            j_last = int(round((last_z - lowest) / self.step))
            shift = math.log(last_p) - lnp[j_last]
            for i, z in enumerate(self.zs):
                if 0.0 <= z <= last_z:
                    lnp[i] = math.log(self._table_pressure(ptab, z))
                elif z > last_z:
                    lnp[i] += shift
                else:  # below the ground: the hydrostatic slope, from the measured ground value
                    lnp[i] += math.log(ptab[0][1]) - math.log(p0)
        self.lnp = lnp

    @staticmethod
    def _table_pressure(ptab, z):
        for (z0, p0), (z1, p1) in zip(ptab, ptab[1:]):
            if z <= z1:
                return p0 * (p1 / p0) ** ((z - z0) / (z1 - z0))
        return ptab[-1][1]

    def pressure(self, z_km):
        i = (z_km - self.z0) / self.step
        i0 = max(0, min(len(self.zs) - 2, int(math.floor(i))))
        f = i - i0
        return math.exp(self.lnp[i0] * (1 - f) + self.lnp[i0 + 1] * f)

    def density(self, z_km):
        return self.pressure(z_km) * self.molar / (RGAS * self.temperature(z_km))

    def scale_height(self, z_km):
        g = self.gm / (self.radius + z_km * 1000.0) ** 2
        return RGAS * self.temperature(z_km) / (self.molar * g) / 1000.0

    def drag_at(self, z_km):
        """Dynamic pressure (Pa) on a craft in a circular orbit at this height."""
        return 0.5 * self.density(z_km) * self.gm / (self.radius + z_km * 1000.0)

def earth_reference_drag(earth_gm, earth_radius):
    return Air("Earth", earth_gm, earth_radius).drag_at(EARTH_CEILING_KM)

def ceiling(air, reference):
    """The height (km) at which the orbital drag falls to the reference, rounded up to a whole kilometre (5 above 500)."""
    if air.name == "Earth":
        return EARTH_CEILING_KM
    z = air.zs[-1]
    hi = None
    zz = 0.0
    while zz < air.zs[-1]:
        if air.drag_at(zz) < reference:
            hi = zz
            break
        zz += 0.25
    if hi is None:
        raise ValueError("%s: the air does not thin out enough within the table" % air.name)
    lo = hi - 0.25
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if air.drag_at(mid) < reference:
            hi = mid
        else:
            lo = mid
    step = 1.0 if hi < 500 else 5.0
    return math.ceil(hi / step) * step

def curve_keys(air, top_km):
    """KSP's pressure (kPa) and temperature (K) keys, by height in metres, with their slopes, close enough together that
    the game's cubic between them stays within a part in a thousand of the worked-out values."""
    pressure, temperature = [], []
    z = air.z0
    while True:
        h = air.scale_height(max(z, 0.0))
        p = air.pressure(z)
        dpdz = -p * air.molar * (air.gm / (air.radius + z * 1000.0) ** 2) / (RGAS * air.temperature(z))  # Pa per m
        pressure.append((z * 1000.0, p / 1000.0, dpdz / 1000.0))
        if z >= top_km:
            break
        z = min(top_km, z + max(0.25, min(h / 3.0, 50.0)))
    # temperature: the table's own corners, and every 2 km between, with the slopes either side of each point
    zs = set()
    z = air.z0
    while z < top_km:
        zs.add(round(z, 3))
        z += 2.0 if top_km <= 300 else 10.0
    zs.add(top_km)
    for ttab in (VENUS_T, MARS_T, TITAN_T, JUPITER_T, SATURN_T, URANUS_T, NEPTUNE_T):
        if air.temperature.__defaults__ and air.temperature.__defaults__[0] is ttab:
            zs.update(z for z, _ in ttab if air.z0 <= z <= top_km)
    for z in sorted(zs):
        e = 0.01
        t = air.temperature(z)
        left = (t - air.temperature(z - e)) / (e * 1000.0)
        right = (air.temperature(z + e) - t) / (e * 1000.0)
        temperature.append((z * 1000.0, t, left, right))
    return pressure, temperature

if __name__ == "__main__":
    import elements  # noqa: F401  (beside this file)
    from bodies import BODIES
    ref = earth_reference_drag(BODIES["Earth"]["gm"], BODIES["Earth"]["radius"])
    print("reference orbital drag at Earth's 140 km: %.4f Pa" % ref)
    for name in ATMOSPHERES:
        b = BODIES[name]
        air = Air(name, b["gm"], b["radius"])
        top = ceiling(air, ref)
        print("%-8s ground %10.1f Pa  %6.1f K  density %8.4f kg/m3  scale height %5.1f km  air ends at %6.0f km  (%.3g Pa there)"
              % (name, air.pressure(0), air.temperature(0), air.density(0), air.scale_height(0), top, air.pressure(top)))
        if name == "Earth":
            for z in (10, 50, 86, 100, 120, 140):
                print("          %4d km: %.4g Pa (the standard: %s)" % (z, air.pressure(z), dict(USSA_P).get(z, "-")))
        if name == "Venus":
            for z in (50, 100, 120, 150):
                print("          %4d km: %.4g Pa" % (z, air.pressure(z)))
        if name == "Jupiter":
            for z in (50, 320, 1000):
                print("          %4d km: %.4g Pa  (the review: 0.1 bar at 50 km, 1 microbar = 0.1 Pa at 320 km, 1 nanobar = 1e-4 Pa at 1000 km)" % (z, air.pressure(z)))
        if name == "Titan":
            for z in (44, 250, 500, 975):
                print("          %4d km: %.4g Pa  (HASI: about 10000 Pa at 44-50 km, 1 Pa at 250 km, 0.1 Pa at 500 km)" % (z, air.pressure(z)))
        if name == "Uranus":
            for z in (50, 320, 4000):
                print("          %4d km: %.4g Pa  (0.1 bar at 50 km; 1e-10 bar = 1e-5 Pa near 4000 km)" % (z, air.pressure(z)))
