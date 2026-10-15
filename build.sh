#!/bin/bash
# Build Real Worlds against the local KSP install.
#
#   ./build.sh            build into GameData/RealWorlds here, then install it into KSP
#   ./build.sh check      compile only, install nothing
#   ./build.sh dist       build into GameData/ here without installing anything
#
# It is built against Keystone.dll (https://github.com/IshiakiZ/ksp-keystone), looked for in this order:
# KEYSTONE=/path/to/Keystone.dll, a built copy of that repository beside this one, the copy installed in the game.
# Needs the .NET SDK (`brew install dotnet`). Override the game location with KSP_DIR=/path/to/KSP.
set -euo pipefail

cd "$(dirname "$0")"
MODE="${1:-install}"
. tools/build/common.sh
OUT=GameData/RealWorlds

KEYSTONE="${KEYSTONE:-}"
for candidate in ../ksp-keystone/GameData/Keystone/Keystone.dll "$KSP_DIR/GameData/Keystone/Keystone.dll"; do
  [ -z "$KEYSTONE" ] && [ -f "$candidate" ] && KEYSTONE="$candidate"
done
[ -n "$KEYSTONE" ] && [ -f "$KEYSTONE" ] || { echo "error: Keystone.dll not found: install Keystone into the game, build ../ksp-keystone, or set KEYSTONE=/path/to/Keystone.dll" >&2; exit 1; }
# What else it is built against, if anything (src/RealWorlds/needs.txt: other mods' libraries, by their place in GameData):
# a built copy of that mod's repository beside this one, or the copy installed in the game.
if [ -f src/RealWorlds/needs.txt ]; then
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    found=""
    for candidate in ../*/GameData/"$path" "$KSP_DIR/GameData/$path"; do
      [ -z "$found" ] && [ -f "$candidate" ] && found="$candidate"
    done
    [ -n "$found" ] || { echo "error: $path not found: install that mod into the game, or build its repository beside this one" >&2; exit 1; }
    KEYSTONE="$KEYSTONE:$found"
  done < src/RealWorlds/needs.txt
fi

# A companion library for the Harmony mod, where this mod has one (src/RealWorldsHarmony): built against this mod and against
# Harmony, only where Harmony is installed in the game, and loaded by the game only where it is.
HARMONY="$KSP_DIR/GameData/000_Harmony/0Harmony.dll"
companion() {  # companion <folder the mod's own library is in>
  [ -d src/RealWorldsHarmony ] || return 0
  if [ -f "$HARMONY" ]; then WITH="$KEYSTONE:$1/RealWorlds.dll:$HARMONY" compile "$1/RealWorldsHarmony.dll" "" src/RealWorldsHarmony
  else rm -f "$1/RealWorldsHarmony.dll"; echo "left out: RealWorldsHarmony (Harmony is not installed here to build it against)"; fi
}

case "$MODE" in
  check)
    WITH="$KEYSTONE" compile "$TMP/RealWorlds.dll" "" src/RealWorlds
    companion "$TMP"
    echo "ok: compiles"
    ;;
  dist|install)
    mkdir -p "$OUT"
    WITH="$KEYSTONE" compile "$OUT/RealWorlds.dll" "" src/RealWorlds
    companion "$OUT"
    # (the mod's own shaders, if it has any: made by tools/shaderpack/make_bundle.py and kept ready made in src/RealWorlds/Shaders)
    if ls src/RealWorlds/Shaders/*.bundle >/dev/null 2>&1; then mkdir -p "$OUT/PluginData"; cp src/RealWorlds/Shaders/*.bundle "$OUT/PluginData/"; fi
    # (and anything else it keeps in src/RealWorlds/PluginData: a craft file, say)
    if [ -d src/RealWorlds/PluginData ]; then mkdir -p "$OUT/PluginData"; cp -R src/RealWorlds/PluginData/. "$OUT/PluginData/"; fi
    if [ "$MODE" = dist ]; then echo "ok: built into $OUT"; exit 0; fi
    mkdir -p "$KSP_DIR/GameData/RealWorlds"
    cp "$OUT/RealWorlds.dll" "$KSP_DIR/GameData/RealWorlds/"
    rm -f "$KSP_DIR/GameData/RealWorlds/RealWorldsHarmony.dll"
    [ -f "$OUT/RealWorldsHarmony.dll" ] && cp "$OUT/RealWorldsHarmony.dll" "$KSP_DIR/GameData/RealWorlds/"
    if [ -d "$OUT/PluginData" ]; then mkdir -p "$KSP_DIR/GameData/RealWorlds/PluginData"; cp -R "$OUT/PluginData/." "$KSP_DIR/GameData/RealWorlds/PluginData/"; fi
    echo "ok: Real Worlds installed to $KSP_DIR/GameData/RealWorlds (restart KSP to load it; it needs Keystone there too)"
    ;;
  *)
    echo "usage: ./build.sh [install|check|dist]" >&2; exit 2
    ;;
esac
