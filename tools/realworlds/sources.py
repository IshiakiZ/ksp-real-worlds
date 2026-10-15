#!/usr/bin/env python3
"""The maps the real worlds are made from: each world's colour and height, from NASA, NOAA and the USGS (2026-10-14).

All are public-domain works of the US government (or released by NASA missions through the Planetary Data System);
each is credited in the mod's README. They are downloaded only with the owner's yes (each named, with its source and
size; given for all of these on 2026-10-14), into ~/.ksp-ai-bridge/downloads/realworlds-maps, never into the workspace; the textures made from them are what the mod carries.

    python3 tools/realworlds/sources.py              # lists them, with sizes
    python3 tools/realworlds/sources.py fetch ID...  # downloads those named (each into a new folder of its own)
"""
import hashlib, json, os, sys, urllib.request

# (outside the workspace and outside any one chat's scratch folder: 4.6 GB, kept for remaking the textures)
SCRATCH = os.environ.get("REALWORLDS_MAPS", os.path.expanduser("~/.ksp-ai-bridge/downloads/realworlds-maps"))
USGS = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/"

# id: (world, what, file, address, bytes, credit)
SOURCES = {
    "earth-colour": ("Earth", "colour (May 2004, no relief shading)", "world.200405.3x21600x10800.jpg",
                     "https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/bmng-base/may/world.200405.3x21600x10800.jpg",
                     21829549, "NASA Earth Observatory, Blue Marble: Next Generation (Reto Stockli, MODIS)"),
    "earth-height": ("Earth", "height of land and sea floor, 1 arc-minute", "ETOPO1_Ice_g_geotiff.zip",
                     "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/ice_surface/grid_registered/georeferenced_tiff/ETOPO1_Ice_g_geotiff.zip",
                     322544479, "NOAA National Centers for Environmental Information, ETOPO1 (Amante & Eakins 2009)"),
    "moon-colour": ("Moon", "colour, 8192 x 4096", "lroc_color_poles_8k.tif",
                    "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_8k.tif",
                    50641970, "NASA Scientific Visualization Studio, CGI Moon Kit (LRO LROC WAC)"),
    "moon-height": ("Moon", "height, 16 pixels a degree", "ldem_16.tif",
                    "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_16.tif",
                    66378634, "NASA Scientific Visualization Studio, CGI Moon Kit (LRO LOLA)"),
    "mars-height": ("Mars", "height, 16 pixels a degree (MOLA MEGDR)", "megt90n000eb.img",
                    "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg016/megt90n000eb.img",
                    33177600, "NASA Mars Global Surveyor MOLA team, PDS Geosciences Node"),
    "mars-colour": ("Mars", "colour, 925 m a pixel (Viking orbiters)", "Mars_Viking_ClrMosaic_global_925m.tif",
                    USGS + "Mars_Viking_ClrMosaic_global_925m.tif", 797888177, "NASA Viking; USGS Astrogeology Science Center"),
    "jupiter-colour": ("Jupiter", "colour, 3601 x 1801 (Cassini)", "PIA07782.tif",
                       "https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia07/pia07782/PIA07782.tif",
                       19456427, "NASA/JPL/Space Science Institute (Cassini), PIA07782"),
    "venus-height": ("Venus", "height (Magellan)", "Venus_Magellan_Topography_Global_4641m_v02.tif",
                     USGS + "Venus_Magellan_Topography_Global_4641m_v02.tif", 67142279, "NASA Magellan; USGS Astrogeology Science Center"),
    # (the second set: the moons, Mercury and the far worlds)
    "io-colour": ("Io", "colour, 1 km a pixel", "Io_GalileoSSI-Voyager_Global_Mosaic_ClrMerge_1km.tif",
                  USGS + "Io_GalileoSSI-Voyager_Global_Mosaic_ClrMerge_1km.tif", 196637696, "NASA Galileo and Voyager; USGS"),
    "europa-colour": ("Europa", "brightness, 500 m a pixel", "Europa_Voyager_GalileoSSI_global_mosaic_500m.tif",
                      USGS + "Europa_Voyager_GalileoSSI_global_mosaic_500m.tif", 192777263, "NASA Galileo and Voyager; USGS"),
    "ganymede-colour": ("Ganymede", "colour, 1435 m a pixel", "Ganymede_Voyager_GalileoSSI_Global_ClrMosaic_1435m.tif",
                        USGS + "Ganymede_Voyager_GalileoSSI_Global_ClrMosaic_1435m.tif", 199204541, "NASA Galileo and Voyager; USGS"),
    "callisto-colour": ("Callisto", "brightness, 1 km a pixel", "Callisto_Voyager_GalileoSSI_global_mosaic_1km.tif",
                        USGS + "Callisto_Voyager_GalileoSSI_global_mosaic_1km.tif", 114640717, "NASA Galileo and Voyager; USGS"),
    "titan-colour": ("Titan", "the ground seen through the haze, 4 km a pixel (Cassini, 938 nm)", "Titan_ISS_P19658_Mosaic_Global_4km.tif",
                     USGS + "Titan_ISS_P19658_Mosaic_Global_4km.tif", 8169529, "NASA/JPL/Space Science Institute (Cassini); USGS"),
    "enceladus-colour": ("Enceladus", "brightness, 110 m a pixel", "Enceladus_Cassini_mosaic_global_110m.tif",
                         USGS + "Enceladus_Cassini_mosaic_global_110m.tif", 103759864, "NASA/JPL/Space Science Institute (Cassini); USGS"),
    "ceres-colour": ("Ceres", "brightness, 20 pixels a degree", "Ceres_Dawn_FC_DLR_global_20ppd_Oct2015.tif",
                     USGS + "Ceres_Dawn_FC_DLR_global_20ppd_Oct2015.tif", 27280830, "NASA/JPL-Caltech/UCLA/MPS/DLR/IDA (Dawn); USGS"),
    "phobos-colour": ("Phobos", "brightness, 40 pixels a degree (Viking)", "Phobos_Viking_Mosaic_40ppd_DLRcontrol.tif",
                      USGS + "Phobos_Viking_Mosaic_40ppd_DLRcontrol.tif", 103738243, "NASA Viking; DLR; USGS"),
    "triton-colour": ("Triton", "colour, 600 m a pixel (Voyager 2)", "Triton_Voyager2_ClrMosaic_GlobalFill_600m.tif",
                      USGS + "Triton_Voyager2_ClrMosaic_GlobalFill_600m.tif", 299994887, "NASA/JPL (Voyager 2); USGS"),
    "pluto-colour": ("Pluto", "brightness, 300 m a pixel", "Pluto_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif",
                     USGS + "Pluto_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif", 309806463, "NASA/JHUAPL/SwRI (New Horizons); USGS"),
    "charon-colour": ("Charon", "brightness, 300 m a pixel", "Charon_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif",
                      USGS + "Charon_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif", 80613890, "NASA/JHUAPL/SwRI (New Horizons); USGS"),
    "mercury-height": ("Mercury", "height, 665 m a pixel", "Mercury_Messenger_USGS_DEM_Global_665m_v2.tif",
                       USGS + "Mercury_Messenger_USGS_DEM_Global_665m_v2.tif", 530934581, "NASA/JHUAPL/Carnegie (MESSENGER); USGS"),
    "mercury-colour": ("Mercury", "colour, 665 m a pixel (enhanced: to be brought back to its own greys)", "Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m.tif",
                       USGS + "Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m.tif", 796539539, "NASA/JHUAPL/Carnegie (MESSENGER); USGS"),
}

FIRST = ["earth-colour", "earth-height", "moon-colour", "moon-height", "mars-height", "mars-colour", "jupiter-colour", "venus-height"]

def listing():
    total = 0
    for group, ids in (("first", FIRST), ("second", [i for i in SOURCES if i not in FIRST])):
        sub = sum(SOURCES[i][4] for i in ids)
        total += sub
        print("%s set: %.0f MB" % (group, sub / 1e6))
        for i in ids:
            world, what, name, url, size, credit = SOURCES[i]
            print("  %-17s %-9s %8.1f MB  %s  (%s)" % (i, world, size / 1e6, name, url.split("/")[2]))
    print("in all: %.0f MB" % (total / 1e6))

def fetch(ids):
    for i in ids:
        world, what, name, url, size, credit = SOURCES[i]
        folder = os.path.join(SCRATCH, i)
        path = os.path.join(folder, name)
        if os.path.exists(path) and os.path.getsize(path) == size:
            print("%s: already here" % i)
            continue
        os.makedirs(folder, exist_ok=True)
        part = path + ".part"
        h = hashlib.sha256()
        with urllib.request.urlopen(url) as r, open(part, "wb") as out:
            got = 0
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                out.write(b)
                h.update(b)
                got += len(b)
        if got != size:
            raise SystemExit("%s: %d bytes came, %d were expected; kept as %s" % (i, got, size, part))
        os.rename(part, path)
        with open(os.path.join(SCRATCH, "fetched.json"), "a") as log:
            log.write(json.dumps({"id": i, "file": path, "bytes": got, "sha256": h.hexdigest(), "url": url}) + "\n")
        print("%s: %d bytes, sha256 %s" % (i, got, h.hexdigest()))

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "fetch":
        fetch(sys.argv[2:])
    else:
        listing()
