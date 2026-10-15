using System;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace RealWorlds
{
    /// <summary>
    /// Every world's far picture came out black on a Mac (found 2026-10-14). Kopernicus loads its textures through
    /// KSPTextureLoader, which puts a compressed texture (DXT1, DXT5) into a small asset bundle made for Windows and has
    /// Unity stream its pixels from the DDS file; on a Mac Unity fails to read the file ("async texture load: failed to load
    /// ..." in its log) and the texture is left empty, which draws black. Uncompressed textures and Windows (where the
    /// loader uploads straight to Direct3D) never go that way. Where the game is not on Windows, the bundle is not used:
    /// the texture is made directly, as an uncompressed one is. Where a later KSPTextureLoader has no such method, nothing
    /// is changed and a line says so.
    /// </summary>
    [KSPAddon(KSPAddon.Startup.Instantly, true)]
    public sealed class TextureFix : MonoBehaviour
    {
        void Awake()
        {
            try { Apply(); }
            catch (Exception e) { Debug.Log("[RealWorlds] the texture loader was left as it is: " + e.Message); }
            Destroy(gameObject);
        }

        static void Apply()
        {
            if (Application.platform == RuntimePlatform.WindowsPlayer) return;
            Type loader = AccessTools.TypeByName("KSPTextureLoader.Format.DDSLoader");
            if (loader == null) return;
            MethodInfo viaBundle = AccessTools.Method(loader, "ShouldLoadViaBundle");
            if (viaBundle == null || viaBundle.ReturnType != typeof(bool))
            {
                Debug.Log("[RealWorlds] this KSPTextureLoader has no ShouldLoadViaBundle: its compressed textures are loaded as it chooses (on a Mac they may draw black)");
                return;
            }
            new Harmony("RealWorlds.TextureFix").Patch(viaBundle, prefix: new HarmonyMethod(typeof(TextureFix), nameof(NotViaBundle)));
            Debug.Log("[RealWorlds] KSPTextureLoader makes compressed textures directly here (its asset-bundle way leaves them black off Windows)");
        }

        static bool NotViaBundle(ref bool __result)
        {
            __result = false;
            return false;
        }
    }
}
