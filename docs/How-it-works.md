# How it works

Real Worlds is Kopernicus configs, written by scripts from published figures, and a small library for what configs
cannot do. Nothing in `Configs/` is written by hand: each file says which script wrote it.

## The worlds

`tools/realworlds/bodies.py` holds each world's size, gravity, spin and prime meridian, and which stock world it takes
over: Kerbin becomes Earth, the Mun the Moon, Duna Mars, Ike Phobos, Gilly Deimos, Eve Venus, Moho Mercury, Dres Ceres,
Jool Jupiter, Pol Io, Vall Europa, Tylo Ganymede, Bop Callisto, Laythe Titan, Minmus Enceladus, Eeloo Pluto; Saturn,
Uranus, Neptune, Triton and Charon are new. The stock worlds keep their names inside the game's files (so other mods and
saves still find "Kerbin"); the player sees the real names.

## The orbits

KSP cannot tilt a world: every world spins about the game's one axis. So, as Real Solar System does, the whole system is
laid out against Earth's equator: Earth spins upright, and the Sun's path across its sky is tilted 23.44 degrees, which
gives the seasons. `elements.py` turns JPL's orbits (the planets against the ecliptic, each moon against its planet's
Laplace plane) into that frame, at J2000 (noon on 1 January 2000), which is the game's time nought. Every world spins
about Earth's pole; the moons that face their planet are turned to face it.

Checked in the game: at time nought the Sun stood overhead within 0.1 degree of where it truly was.

## The air

`air.py` builds each atmosphere the way the reference atmospheres are built: a measured profile of temperature with
height, the pressure at the ground (or at the 1 bar level of a giant), the gas's molar mass and the world's gravity, the
pressure worked out by hydrostatic balance (Earth's and Venus's measured tables are used as they stand). Where each air
ends is put at the same drag for every world: the height where a circular orbit meets the dynamic pressure it meets 140
km above Earth (so Titan's thin, cold air reaches 705 km, Mars's 116).

## The ground

`make_textures.py` turns the maps (see [Sources](Sources.md)) into the game's textures with `maps.swift`: 16-bit
heights, colour, and the light and shade of the relief for the far view. The game reads a terrain map at u = 0.25 -
longitude/360 (it runs west) with its first row at the south pole; the maps are written that way, and the heights the
game gives at known places are the real ones (Tibet 4,985 m, Orlando 33 m, the Mariana Trench -10,180 m).
`draw_textures.py` draws what no map gives: Venus's ground under its clouds and its cloud tops, the bands of Saturn,
Uranus and Neptune, Titan's haze, Saturn's rings from their measured radii and optical depths.

Under the measured maps (pixels 2 to 5 km apart) the worlds without a sea get a light noise a few tens of metres high,
from 3 km down to about 200 m. Earth does not: it would raise its low coasts out of the water.

## The biomes

`make_biomes.py` makes each world's science regions from the same height and colour maps: Earth's sea by depth and its
land by height and by what the Blue Marble shows growing; the Moon's maria, each named for the great mare it lies in;
Mars's caps, volcanoes and basins; named features on the rest. The game reads a biome map with the same turn as a
terrain map.

## The library

* **The calendar**: the clock shows the real date in UTC (the leap seconds since 2000 taken off); days of 24 hours and
  years of 365 days, whatever the game's own "Kerbin time" setting says.
* **Time warp** on rails to 10,000,000 times, and each world's warp heights made for those rates.
* **Far pictures on a Mac**: KSPTextureLoader (which Kopernicus loads every texture through) puts a compressed texture
  into a home-made asset bundle and has Unity stream its pixels from the file; on a Mac that fails and the texture is
  left black (every world drew black). Off Windows, Real Worlds sends such textures the direct way.
* **Jupiter**: Jool's far body carries the game's own pieces that swap its material for Jool's (its green clouds); they
  are taken off and Jupiter drawn plainly, as the other giants are.
* **Old saves**: a save played with Real Worlds is marked; loading one with craft and no mark keeps a copy of it as it
  was (`persistent (before Real Worlds).sfs` beside it) and says that its craft were made for the stock worlds, once.

## With other mods

Where Scatterer is installed, Real Worlds sets its skies for Earth (Bruneton's clear-sky figures), Mars (dust), Venus
(a near-grey haze over its pale cloud tops) and Titan (orange haze), takes Jupiter off its list, takes the seas off Venus
and Titan, and sets each world's eclipses to its real moons. Where EVE is installed, its stock clouds for Eve, Laythe
and Jool (purple, white, green) and Kerbin's city lights are taken off.
