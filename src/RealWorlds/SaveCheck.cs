using System;
using UnityEngine;

namespace RealWorlds
{
    /// <summary>
    /// A save made without Real Worlds has craft made for the stock worlds: an orbit 100 km above Kerbin lies 5,600 km inside
    /// Earth, and a base on the Mun stands where the Moon's ground may be kilometres higher or lower. The game destroys what
    /// it finds below a surface (tried: a save of 34 craft lost a fifth of its size on its first load). So a save is marked
    /// once it has been played with Real Worlds, and loading a save with craft and no mark keeps a copy of it as it was
    /// ("persistent (before Real Worlds).sfs" beside it: the game writes the save as it loads it, before any craft is
    /// touched) and says so, once: what is at risk, where the copy is, and that a new save is the way to play with the real
    /// worlds. (The game's own Backup folder holds its five-minute autosaves, not a copy from each load.)
    /// </summary>
    [KSPScenario(ScenarioCreationOptions.AddToAllGames, GameScenes.SPACECENTER, GameScenes.FLIGHT, GameScenes.TRACKSTATION, GameScenes.EDITOR)]
    public sealed class RealWorldsSave : ScenarioModule
    {
        const string Mark = "madeWith", Copy = "persistent (before Real Worlds).sfs";
        static string toldFor;
        bool warn, kept;

        public override void OnLoad(ConfigNode node)
        {
            if (!Worlds.Real || node.HasValue(Mark) || toldFor == HighLogic.SaveFolder) return;
            int craft = 0;
            if (HighLogic.CurrentGame?.flightState?.protoVessels != null)
                foreach (ProtoVessel pv in HighLogic.CurrentGame.flightState.protoVessels)
                    if (pv != null && pv.vesselType != VesselType.Flag && pv.vesselType != VesselType.SpaceObject) craft++;
            warn = craft > 0;
            if (!warn) return;
            try
            {
                string dir = KSPUtil.ApplicationRootPath + "saves/" + HighLogic.SaveFolder + "/";
                if (System.IO.File.Exists(dir + "persistent.sfs") && !System.IO.File.Exists(dir + Copy))
                    System.IO.File.Copy(dir + "persistent.sfs", dir + Copy);
                kept = System.IO.File.Exists(dir + Copy);
            }
            catch (Exception e) { Debug.Log("[Real Worlds] could not keep a copy of the save: " + e.Message); }
            Debug.Log("[Real Worlds] this save was made without Real Worlds and has " + craft + " craft: telling the player" + (kept ? ", a copy kept as " + Copy : ""));
        }

        public override void OnSave(ConfigNode node)
        {
            if (Worlds.Real) node.SetValue(Mark, "Real Worlds " + Worlds.Version, true);
        }

        void Start()
        {
            if (!warn || toldFor == HighLogic.SaveFolder) return;
            toldFor = HighLogic.SaveFolder;
            PopupDialog.SpawnPopupDialog(new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), "RealWorldsSave", "Real Worlds",
                "This save was made without Real Worlds. Its craft were made for the stock worlds: those in orbit or on the ground may now be inside Earth or another world, or far from where they were, and the game destroys what it finds below a surface.\n\n" +
                (kept ? "A copy of this save as it was is kept beside it: saves/" + HighLogic.SaveFolder + "/" + Copy + " (rename it persistent.sfs, with Real Worlds taken out, to go back to it). " : "") +
                "To play with the real worlds, start a new save.",
                "Understood", false, HighLogic.UISkin);
        }
    }
}
