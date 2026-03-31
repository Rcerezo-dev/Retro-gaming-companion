import os
import shutil
from pathlib import Path

root = Path("H:\\")

save_exts = {".sav", ".srm", ".mcd", ".ps2", ".gci", ".nv", ".hi", ".brm", ".brmc", ".ml1"}
state_exts = {".state", ".state1", ".state2", ".st0", ".st1", ".st2", ".st3", ".st4", ".st5", ".sgm", ".ppst"}

folder_aliases = {
    "Atari 2600": "atari2600",
    "Famicom Disk System": "fds",
    "Game Boy": "gb",
    "Game Boy Advance": "gba",
    "Game Boy Color": "gbc",
    "Game Gear": "gamegear",
    "Master System": "mastersystem",
    "Nintendo 64DD": "n64dd",
    "Nintendo DS": "nds",
    "NGC": "gamecube",
    "ss": "saturn",
    "Saturn": "saturn"
}


def ensure_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)

deleted_arcade_files = 0
moved_files = 0

for plat_dir in list(root.iterdir()):
    if not plat_dir.is_dir() or plat_dir.name in ("saves", "states", "bios", "inbox", "screenshots", "media", "configs", "_descartados"):
        continue

    actual_plat = plat_dir.name
    is_alias = actual_plat in folder_aliases
    target_plat = folder_aliases.get(actual_plat, actual_plat)

    for f in list(plat_dir.iterdir()):
        if not f.is_file():
            continue
            
        ext = f.suffix.lower()
        name = f.name.lower()

        # 1. States
        if ext in state_exts:
            dst = root / "saves" / target_plat / "states" / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue
            
        # 2. Saves
        if ext in save_exts:
            dst = root / "saves" / target_plat / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue
            
        # 3. Videos
        if ext == ".mp4":
            dst = root / "media" / target_plat / "videos" / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue
            
        # 4. Images
        if ext in (".png", ".jpg", ".jpeg"):
            dst = root / "media" / target_plat / "images" / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue
            
        # 5. Configs & Special Files
        if ext == ".cfg" or name == "vmu_save_a1.bin":
            if name == "vmu_save_a1.bin":
                dst = root / "saves" / target_plat / f.name
            else:
                dst = root / "configs" / target_plat / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue
            
        # 6. Shaders / Sys Files
        if actual_plat == "arcade" and ext == ".bin" and (name.startswith("fs_") or name.startswith("vs_")):
            dst = root / "bios" / "shaders" / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue
            
        if actual_plat == "wii" and ext == ".bin" and name in ("fst.bin", "misc.bin", "nwc24dl.bin", "nwc24fl.bin", "nwc24fls.bin", "wiimmfi.bin"):
            dst = root / "bios" / "wii" / f.name
            ensure_dir(dst.parent)
            shutil.move(str(f), dst)
            moved_files += 1
            continue

        # 7. Arcade cleanup (delete loose unzipped files)
        if actual_plat in ("arcade", "mame", "neogeo", "cps1", "cps2", "cps3", "fbneo"):
            # If it's a known unzipped ROM structure
            is_unzipped_part = False
            if ext in (".rom", ".bin", ".key"):
                is_unzipped_part = True
            elif len(ext) >= 2 and ext[1].isdigit(): # e.g. .04, .06a, .13m
                is_unzipped_part = True
            elif len(ext) >= 3 and ext[1] in 'cvmps' and ext[2].isdigit(): # e.g. .c1, .v2
                is_unzipped_part = True
            elif ext == "":
                is_unzipped_part = True
                
            if is_unzipped_part:
                try:
                    os.remove(f)
                    deleted_arcade_files += 1
                except OSError:
                    pass
                continue

        # 8. Merge duplicated folders (e.g., move the leftover validated ROMs)
        if is_alias:
            dst = root / target_plat / f.name
            ensure_dir(dst.parent)
            if not dst.exists():
                shutil.move(str(f), dst)
                moved_files += 1

    # Remove the alias folder if it's now empty
    if is_alias:
        try:
            os.rmdir(plat_dir)
        except OSError:
            pass

# Process the old 'states' directory at root
old_states = root / "states"
if old_states.exists() and old_states.is_dir():
    for plat_dir in list(old_states.iterdir()):
        if plat_dir.is_dir():
            for f in list(plat_dir.iterdir()):
                if f.is_file():
                    dst = root / "saves" / plat_dir.name / "states" / f.name
                    ensure_dir(dst.parent)
                    shutil.move(str(f), dst)
                    moved_files += 1
            try:
                os.rmdir(plat_dir)
            except OSError:
                pass
    try:
        os.rmdir(old_states)
    except OSError:
        pass

print(f"DONE. Moved {moved_files} files to their standard directories.")
print(f"DONE. Deleted {deleted_arcade_files} loose unzipped arcade files.")
