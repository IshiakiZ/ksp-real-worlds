# What was tested

All on a Mac (macOS, OpenGL), in a copy of the game made for it, with Kopernicus release-251, ModularFlightIntegrator
1.2.10.0, KSPTextureLoader 1.0.36, Scatterer, EVE and the other mods of this workspace. Nothing on Windows or Linux yet.

## The worlds

* Every world's radius, gravity, spin and orbit, read back from the game (AI Bridge's `bodies`) against the configs.
* At time nought the Sun stood overhead within 0.1 degree of where it truly was at noon on 1 January 2000.
* The terrain's heights at known places, read back from the game: Tibet 4,985 m, Orlando 33 m, the Mariana Trench
  -10,180 m, the Apollo 11 site -1,878 m (LOLA: about -1,880), Olympus Mons near 20 km, Hellas -6 km; places mirrored
  east to west came out wrong, as they should.
* The space centre's ground at LC-39A: 4.8 m; the pad and both ends of the runway read from the game (the runway lies on
  heading 84.4, turned six degrees by the move from Kerbin).

## The biomes

Read back at known places: LC-39A Shores, the Sahara and central Australia Deserts, the Himalaya Mountains, the Mariana
Trench Trenches, the Amazon Rainforests, Greenland Ice Sheets, Kansas Grasslands; the Apollo 11 site Mare
Tranquillitatis, Apollo 15's Mare Imbrium, the far side's South Pole-Aitken Basin; Olympus Mons and Hellas Planitia.

## The far pictures

Every world looked at in the map view and the tracking station, from the sunward side. Found and mended on the way:
every compressed texture black on the Mac (KSPTextureLoader; see How it works), Jupiter's green edge (Jool's own
material pieces), Venus purple (EVE's and Scatterer's stock Eve), Titan blue (Scatterer's stock sea and sky for
Laythe), EVE's stock layers never taken off (a patch that matched nothing).

## Flight

* **Re-entry from low Earth orbit** with a stock capsule (Mk1-3 pod, 2.5 m heat shield, Mk16-XL parachute), from an orbit
  of 200 by 40 km: into the air at 7,396 m/s, a peak of 12.3 g, parachutes out at 20.7 km, splashed down in the South
  Atlantic at 9.7 m/s; nothing lost to heat.
* **A launch from LC-39A** with the stock Kerbal X on AI Bridge's ascent program: it flew its stages as planned and,
  on its last stage, reached 5.7 km/s (orbital, Earth's own turn included) 140 km up, about three quarters of the 7.8
  km/s an orbit takes there: a rocket made for Kerbin falls short, as it should.

## Saves made without it

A save made in the stock game, with 7 craft, loaded with Real Worlds: the warning came up and a copy of the save as it
was was kept beside it. Without the copy, the first load lost the craft that now lay inside a world (the save shrank
from 321 KB to 261 KB). Found on the way: AI Bridge's `load_save` added a newly installed mod's scenarios without writing
the save before the game started, as the game's own menu does, so they were lost; it now does as the menu does.
