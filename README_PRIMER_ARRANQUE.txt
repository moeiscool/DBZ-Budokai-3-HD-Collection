FIRST START - DBZ Budokai 3 HD Collection
================================================

This package is ONE FILE: run dbz3.exe and that's it. There are no variants
and no folders to choose: the runtime works on any x64 CPU (Core 2, 2006,
onwards). If your machine does not start it, it is not because of "a missing
variant" (there are none).

-----------------------------------------------------------------------
STEP 1 - Place the game data
-----------------------------------------------------------------------
There are FOUR valid ways (use whichever you prefer):

  Option A (recommended) - an "assets" folder:
    <game folder>\
      dbz3.exe
      assets\
        default.xex
        us\
        eu\

  Option B - loose folders next to the executable:
    <game folder>\
      dbz3.exe
      default.xex
      us\
      eu\

  Option C - the disc dump AS IS (most convenient):
    <game folder>\
      dbz3.exe
      DBZ3\
        yae3_xenon.xex     <- whatever it is called, no renaming
        us\
        eu\
    The launcher finds the Budokai 3 executable by itself (by size and
    checksum) and mounts the DBZ3\ folder automatically.

  Option D - the ISO directly (easiest):
    Put your Budokai 3 HD Collection .iso next to dbz3.exe. The launcher
    detects it and plays straight from the disc image: nothing to extract or
    copy. You can also pick the file with "ISO (.iso)" in the launcher. It
    works with the full ORIGINAL ISO (the one with the HD Collection menu at
    the root): the launcher takes the Budokai 3 executable from inside.
    (Note: mods need the extracted folder, options A or B.)

The launcher detects which one you use. You can also choose the source with
the "Extracted folder" or "ISO (.iso)" buttons in the launcher if the data is
somewhere else.

IMPORTANT - the executable:
- You do NOT need to rename anything to "default.xex": the launcher looks for
  the Budokai 3 executable by size and checksum (typical names:
  yae3_xenon.xex, yae3_xenon_eu.xex) and prepares it itself in its
  user_data\xex_cache folder. It NEVER writes inside your game folder.
- You can use the US/NA executable (yae3_xenon.xex) or the EU/PAL one
  (yae3_xenon_eu.xex): the game contains the recompilation of both and picks
  the right one automatically.
- The EU/PAL region (eu/ folder) and the language are chosen in the launcher.
- If you place the HD Collection MENU (the default.xex at the root of the
  disc), the launcher warns you and blocks Play: that executable is not in the
  core.
- If you place a DBZ Budokai HD (DBZ1) executable by mistake, the launcher
  warns you and asks you to use the DBZ1 launcher (dbz1.exe).

-----------------------------------------------------------------------
STEP 2 - Install mods (optional)
-----------------------------------------------------------------------
Put mods in the "mods" folder (each mod in its own folder, with manifest.txt).
The launcher lists them and enables them in the "Mods" tab. See
MODDING_README.md.

-----------------------------------------------------------------------
STEP 3 - Troubleshooting
-----------------------------------------------------------------------
- If the game closes suddenly, a window shows the path of the log (logs\,
  next to the game). Share that file for diagnosis.
- logs\ records which executable was detected (path, size, checksum), the
  status and the data folder: it is the first thing to check if something
  fails.
- If nothing happens when you press PLAY: usually there is an "unrecognised
  executable" message in the launcher banner (place the Budokai 3 executable,
  not the HD Collection menu).
- Mods and settings are saved in the game folder (next to dbz3.exe).
- You need Microsoft's C++ runtime DLLs (msvcp140.dll, vcruntime140.dll),
  which are already included next to the game.

-----------------------------------------------------------------------
PS5 (jailbroken, experimental)
-----------------------------------------------------------------------
This Windows package does not run on a PS5. A PS5 build is made from your own
copy of the game with ps5/make_ps5.sh in the source repository; see
docs/PS5.md there.
