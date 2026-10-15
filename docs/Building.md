# Building it yourself

The configs and the library are in this repository; the textures (about 330 MB) are not: they are made from the
maps, which are downloaded first.

1. `python3 tools/realworlds/sources.py` lists the maps (about 4.6 GB in all); `python3 tools/realworlds/sources.py
   fetch ID ...` downloads them into `~/.ksp-ai-bridge/downloads/realworlds-maps` (or `REALWORLDS_MAPS`).
2. `swiftc -O -o ~/.ksp-ai-bridge/tools/realworlds/maps tools/realworlds/maps.swift` builds the converter (macOS: it
   reads the maps with CoreGraphics).
3. `python3 tools/realworlds/make_textures.py`, then `python3 tools/realworlds/draw_textures.py`, then
   `python3 tools/realworlds/make_biomes.py` make the textures in `src/RealWorlds/PluginData/` and record their ranges
   in `tools/realworlds/made.json`.
4. `python3 tools/realworlds/make_configs.py` writes `src/RealWorlds/Configs/` from the figures and `made.json`.
5. `./build.sh` (with the game's own libraries, Keystone's and Harmony's beside it) builds `RealWorlds.dll`.

Never into a game whose saves you want to keep without it: it replaces every world.
