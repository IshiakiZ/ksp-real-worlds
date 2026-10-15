using System;
using System.Text;
using Keystone;
using UnityEngine;

#if !DEV
[assembly: KSPAssembly("RealWorlds", 0, 1)]
[assembly: KSPAssemblyDependency("Keystone", 0, 8)]
[assembly: KSPAssemblyDependency("HarmonyKSP", 1, 0)]
#endif

namespace RealWorlds
{
    /// <summary>
    /// The real Solar System at its real size, from NASA's and JPL's figures (the owner, 2026-10-11: a real solar system
    /// from NASA's data; 2026-10-13: "the real-size solar system").
    ///
    /// The worlds themselves are Kopernicus configs (Configs/, written by tools/realworlds/make_configs.py). This library
    /// does what configs cannot: the game's clock shows real dates (the game's time nought is J2000, 1 January 2000 at
    /// noon), its days and years are Earth's whatever the game's own "Kerbin time" setting says, and time warp reaches
    /// further, for distances the stock rates were never made for. Both can be switched off on the mod's page.
    ///
    /// Nothing here acts unless the worlds are the real ones (the home world as large as Earth): installed without
    /// Kopernicus or the configs, it does nothing.
    /// </summary>
    [KSPAddon(KSPAddon.Startup.Instantly, true)]
    public sealed class WorldsAtStart : MonoBehaviour
    {
        void Awake() { Worlds.Setup(); Destroy(gameObject); }
    }

    [KSPAddon(KSPAddon.Startup.MainMenu, true)]
    public sealed class WorldsAtMenu : MonoBehaviour
    {
        void Start() { Worlds.Look(); Destroy(gameObject); }
    }

    /// <summary>In every scene with a time warp: its rates, where the faster warp is on.</summary>
    [KSPAddon(KSPAddon.Startup.AllGameScenes, false)]
    public sealed class WorldsInScene : MonoBehaviour
    {
        void Start() { Worlds.Warp(); }
    }

    public static class Worlds
    {
        public const string Version = "0.1.0";
        static Mod mod;
        internal static Toggle calendar, warp;
        /// <summary>The worlds are the real ones (found at the main menu).</summary>
        internal static bool Real;
        static IDateTimeFormatter gameFormatter;
        static readonly RealCalendar ours = new RealCalendar();

        // Time warp's rates on rails: the game's, and these (each ten times the last, to ten million).
        static readonly float[] stockRates = { 1f, 5f, 10f, 50f, 100f, 1000f, 10000f, 100000f };
        static readonly float[] fastRates = { 1f, 10f, 100f, 1000f, 10000f, 100000f, 1000000f, 10000000f };

        public static void Setup()
        {
            if (mod == null || Kit.Find("Real Worlds") != mod)
            {
                mod = Kit.Register("Real Worlds", Version, "The real Solar System at its real size, from NASA's and JPL's figures.");
                calendar = mod.Toggle("calendar", "Real dates", true, "The clock shows the real date and time (UTC), from noon on 1 January 2000; days are 24 hours and years 365 days. Off: the game's own clock.");
                warp = mod.Toggle("warp", "Time warp to 10,000,000x", true, "Time warp's rates on rails go 1, 10, 100 ... 10,000,000 times, for the real distances (Neptune is 30 years from Earth by the cheapest path). Off: the game's own rates, to 100,000 times.");
                calendar.Changed += Clock;
                warp.Changed += Warp;
                mod.Panel = Readout;
            }
        }

        /// <summary>At the main menu, once the worlds are made: are they the real ones?</summary>
        internal static void Look()
        {
            CelestialBody home = FlightGlobals.GetHomeBody();
            Real = home != null && home.Radius > 6.0e6;
            if (!Real) Debug.Log("[Real Worlds] the home world is " + (home != null ? (home.Radius / 1000.0).ToString("0") + " km across its radius" : "not found") + ": not the real worlds (is Kopernicus installed?); the clock and time warp are left as the game has them");
            else
            {
                try { Jupiter(); }
                catch (Exception e) { Debug.Log("[Real Worlds] Jupiter's far look was left as Jool's: " + e.Message); }
            }
            Clock();
        }

        /// <summary>
        /// Jupiter is Jool, whose far body carries two of the game's own pieces: one swaps its whole material for one of
        /// Jool's own when the worlds are made and again whenever the settings are applied (at High terrain shaders, Jool's
        /// animated green clouds), the other drives that animation. Kopernicus's changes are lost under either (Jupiter kept
        /// Jool's green edge). Both are taken off and Jupiter is drawn as the other giants are: its picture, lit plainly.
        /// </summary>
        static void Jupiter()
        {
            CelestialBody jool = FlightGlobals.Bodies.Find(b => b.bodyName == "Jool");
            if (jool == null || jool.scaledBody == null) return;
            GameObject far = jool.scaledBody;
            foreach (MaterialBasedOnGraphicsSetting c in far.GetComponents<MaterialBasedOnGraphicsSetting>()) UnityEngine.Object.Destroy(c);
            foreach (GasGiantMaterialControls c in far.GetComponents<GasGiantMaterialControls>()) UnityEngine.Object.Destroy(c);
            MeshRenderer r = far.GetComponent<MeshRenderer>();
            if (r == null || r.sharedMaterials.Length == 0) return;
            CelestialBody saturn = FlightGlobals.Bodies.Find(b => b.bodyName == "Saturn");
            Material like = saturn != null && saturn.scaledBody != null ? saturn.scaledBody.GetComponent<MeshRenderer>()?.sharedMaterial : null;
            Shader plain = Shader.Find("Terrain/Scaled Planet (Simple)") ?? (like != null ? like.shader : null);
            if (plain == null) return;
            Material[] mats = r.sharedMaterials;
            Material old = mats[0];
            var m = new Material(plain) { name = "Jupiter (Real Worlds)" };
            m.SetColor("_Color", Color.white);
            m.SetColor("_SpecColor", Color.black);
            m.SetFloat("_Shininess", 0.03f);
            m.SetFloat("_Opacity", 1f);
            // (the picture and normal map are loaded and let go as Jupiter comes into view and leaves it, into whichever
            // material the planet has then: what is loaded now is carried over)
            foreach (string p in new[] { "_MainTex", "_BumpMap" })
                if (old != null && old.HasProperty(p) && old.GetTexture(p) != null) m.SetTexture(p, old.GetTexture(p));
            mats[0] = m;
            r.sharedMaterials = mats;
        }

        static void Clock()
        {
            if (gameFormatter == null && !(KSPUtil.dateTimeFormatter is RealCalendar)) gameFormatter = KSPUtil.dateTimeFormatter;
            if (Real && calendar) KSPUtil.dateTimeFormatter = ours;
            else if (KSPUtil.dateTimeFormatter is RealCalendar && gameFormatter != null) KSPUtil.dateTimeFormatter = gameFormatter;
        }

        internal static void Warp()
        {
            TimeWarp tw = TimeWarp.fetch;
            if (tw == null || tw.warpRates == null || tw.warpRates.Length != stockRates.Length) return;
            float[] want = Real && warp ? fastRates : stockRates;
            if (tw.warpRates[tw.warpRates.Length - 1] == want[want.Length - 1]) return;
            if (TimeWarp.CurrentRateIndex > 0 && TimeWarp.WarpMode == TimeWarp.Modes.HIGH) TimeWarp.SetRate(0, true);
            Array.Copy(want, tw.warpRates, want.Length);
            // (where the game limits a rate by the craft's height, rather than by its periapsis as it does as it comes,
            // each world's heights are made for the rates in use: see make_configs.py, warp_limits)
            foreach (CelestialBody b in FlightGlobals.Bodies) Limits(b, want);
        }

        /// <summary>A world's lowest height for each rate, for the rates in use: Real Worlds' configs set them as a floor plus
        /// the fall a craft could make within one frame at each rate; the floor and that fall are read back from them.</summary>
        static void Limits(CelestialBody b, float[] rates)
        {
            float[] l = b.timeWarpAltitudeLimits;
            if (l == null || l.Length != rates.Length) return;
            float[] from = madeFor.TryGetValue(b.bodyName, out float[] was) ? was : stockRates;
            if (from == rates) return;
            // limit = floor + rate * fall, read from the second and the last (the first is always nought)
            float fall = (l[7] - l[1]) / (from[7] - from[1]);
            float floor = l[1] - from[1] * fall;
            if (fall <= 0f || floor < 0f) return;
            for (int i = 1; i < l.Length; i++) l[i] = floor + rates[i] * fall;
            madeFor[b.bodyName] = rates;
        }
        static readonly System.Collections.Generic.Dictionary<string, float[]> madeFor = new System.Collections.Generic.Dictionary<string, float[]>();

        static void Readout()
        {
            if (!Real) { GUILayout.Label("The worlds are not the real ones (Kopernicus or Real Worlds' configs are missing): nothing is changed."); return; }
            GUILayout.Label("Today in the game: " + RealCalendar.Date(Planetarium.GetUniversalTime(), true, true));
        }
    }

    /// <summary>
    /// The game's clock in Earth's days and years, and its dates as real ones. The game's time nought is J2000 (noon on
    /// 1 January 2000, Terrestrial Time), to which every orbit's figures are set; a date is shown in UTC, the leap seconds
    /// since then taken off (TT - UTC is 64.184 s in 2000 and 69.184 s from 2017). Lengths of time (how long until a burn,
    /// a mission's time) are told in the game's own words, in hours of 60 minutes, days of 24 hours and years of 365 days.
    /// </summary>
    public sealed class RealCalendar : IDateTimeFormatter
    {
        public int Minute => 60;
        public int Hour => 3600;
        public int Day => 86400;
        public int Year => 31536000;

        static readonly DateTime J2000 = new DateTime(2000, 1, 1, 12, 0, 0, DateTimeKind.Utc);
        // (the leap seconds since 2000: the UTC day each began, and TAI - UTC from then)
        static readonly DateTime[] leapFrom = { new DateTime(2006, 1, 1), new DateTime(2009, 1, 1), new DateTime(2012, 7, 1), new DateTime(2015, 7, 1), new DateTime(2017, 1, 1) };
        static readonly int[] taiMinusUtc = { 33, 34, 35, 36, 37 };
        static readonly string[] months = { "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" };

        /// <summary>The UTC date and time of a moment of the game's clock.</summary>
        public static DateTime Utc(double ut)
        {
            if (double.IsNaN(ut) || double.IsInfinity(ut)) return J2000;
            // (DateTime reaches the year 9999; the game's clock never does in play)
            ut = Math.Max(-6.0e10, Math.Min(2.5e11, ut));
            DateTime first = J2000.AddSeconds(ut - 64.184);
            int tai = 32;
            for (int i = 0; i < leapFrom.Length; i++) if (first >= leapFrom[i]) tai = taiMinusUtc[i];
            return J2000.AddSeconds(ut - 32.184 - tai);
        }

        public static string Date(double ut, bool time, bool seconds)
        {
            DateTime d = Utc(ut);
            var sb = new StringBuilder(32);
            sb.Append(d.Day).Append(' ').Append(months[d.Month - 1]).Append(' ').Append(d.Year);
            if (time) { sb.Append(", ").Append(d.Hour.ToString("00")).Append(':').Append(d.Minute.ToString("00")); if (seconds) sb.Append(':').Append(d.Second.ToString("00")); sb.Append(" UTC"); }
            return sb.ToString();
        }

        // (the clock in the corner asks for the date every frame: the last answer is kept for as long as it holds)
        double compactAt = double.NaN; bool compactTime, compactSeconds; string compact;

        public string PrintDateCompact(double time, bool includeTime, bool includeSeconds = false)
        {
            double whole = Math.Floor(time);
            if (whole == compactAt && includeTime == compactTime && includeSeconds == compactSeconds && compact != null) return compact;
            DateTime d = Utc(time);
            var sb = new StringBuilder(24);
            sb.Append(d.Year).Append('-').Append(d.Month.ToString("00")).Append('-').Append(d.Day.ToString("00"));
            if (includeTime) { sb.Append(' ').Append(d.Hour.ToString("00")).Append(':').Append(d.Minute.ToString("00")); if (includeSeconds) sb.Append(':').Append(d.Second.ToString("00")); }
            compactAt = whole; compactTime = includeTime; compactSeconds = includeSeconds;
            return compact = sb.ToString();
        }

        public string PrintDate(double time, bool includeTime, bool includeSeconds = false) => Date(time, includeTime, includeSeconds);
        public string PrintDateNew(double time, bool includeTime) => Date(time, includeTime, true);

        // Lengths of time: the game's own formatter, told to count in Earth's days and years for the moment it is asked.
        // (Its unit is the "Kerbin time" setting; it is set to Earth's only while the game's formatter is working, and put
        // back at once, so the player's setting stays as they have it, and nothing writes it to the settings file meanwhile.)
        static IDateTimeFormatter stock;
        static IDateTimeFormatter Stock => stock ?? (stock = new KSPUtil.DefaultDateTimeFormatter());

        static T Earth<T>(Func<T> f)
        {
            bool was = GameSettings.KERBIN_TIME;
            GameSettings.KERBIN_TIME = false;
            try { return f(); }
            finally { GameSettings.KERBIN_TIME = was; }
        }

        public string PrintTimeLong(double time) => Earth(() => Stock.PrintTimeLong(time));
        public string PrintTimeStamp(double time, bool days = false, bool years = false) => Earth(() => Stock.PrintTimeStamp(time, days, years));
        public string PrintTimeStampCompact(double time, bool days = false, bool years = false) => Earth(() => Stock.PrintTimeStampCompact(time, days, years));
        public string PrintTime(double time, int valuesOfInterest, bool explicitPositive) => Earth(() => Stock.PrintTime(time, valuesOfInterest, explicitPositive));
        public string PrintTime(double time, int valuesOfInterest, bool explicitPositive, bool logEnglish) => Earth(() => Stock.PrintTime(time, valuesOfInterest, explicitPositive, logEnglish));
        public string PrintTimeCompact(double time, bool explicitPositive) => Earth(() => Stock.PrintTimeCompact(time, explicitPositive));
        public string PrintDateDelta(double time, bool includeTime, bool includeSeconds, bool useAbs) => Earth(() => Stock.PrintDateDelta(time, includeTime, includeSeconds, useAbs));
        public string PrintDateDeltaCompact(double time, bool includeTime, bool includeSeconds, bool useAbs) => Earth(() => Stock.PrintDateDeltaCompact(time, includeTime, includeSeconds, useAbs));
        public string PrintDateDeltaCompact(double time, bool includeTime, bool includeSeconds, bool useAbs, int interestedPlaces) => Earth(() => Stock.PrintDateDeltaCompact(time, includeTime, includeSeconds, useAbs, interestedPlaces));
    }
}
