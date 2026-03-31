import os
import shutil
from pathlib import Path

root = Path(r"E:\Carpetas anbernic")

save_exts = {".sav", ".srm", ".mcd", ".ps2", ".gci", ".nv", ".hi", ".brm", ".brmc", ".ml1"}
state_exts = {".state", ".state1", ".state2", ".st0", ".st1", ".st2", ".st3", ".st4", ".st5", ".sgm", ".ppst"}

folder_aliases = {
    "Game Boy Advance": "gba",
    "ss": "saturn",
    "Saturn": "saturn"
}

def ensure_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)

moved_files = 0
deleted_arcade_files = 0

def safe_move(src, dst):
    global moved_files
    try:
        if dst.exists():
            src.unlink() # remove source if duplicate exists in target
            return
        shutil.move(str(src), dst)
        moved_files += 1
    except Exception as e:
        print(f"Error moviendo {src.name}: {e}")

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

        # States
        if ext in state_exts:
            dst = root / "saves" / target_plat / "states" / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue
            
        # Saves
        if ext in save_exts:
            dst = root / "saves" / target_plat / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue
            
        # Videos
        if ext == ".mp4":
            dst = root / "media" / target_plat / "videos" / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue
            
        # Images
        if ext in (".png", ".jpg", ".jpeg"):
            dst = root / "media" / target_plat / "images" / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue
            
        # Configs
        if ext == ".cfg" or name == "vmu_save_a1.bin":
            dst = root / ("saves" if name == "vmu_save_a1.bin" else "configs") / target_plat / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue
            
        # Shaders/Bios
        if actual_plat == "arcade" and ext == ".bin" and (name.startswith("fs_") or name.startswith("vs_")):
            dst = root / "bios" / "shaders" / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue
            
        if actual_plat == "wii" and ext == ".bin" and name in ("fst.bin", "misc.bin", "nwc24dl.bin", "nwc24fl.bin", "nwc24fls.bin", "wiimmfi.bin"):
            dst = root / "bios" / "wii" / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)
            continue

        # Arcade cleanup
        if actual_plat in ("arcade", "mame", "neogeo", "cps1", "cps2", "cps3", "fbneo"):
            is_unzipped = False
            if ext in (".rom", ".bin", ".key"): is_unzipped = True
            elif len(ext) >= 2 and ext[1].isdigit(): is_unzipped = True
            elif len(ext) >= 3 and ext[1] in 'cvmps' and ext[2].isdigit(): is_unzipped = True
            elif ext == "": is_unzipped = True
            if is_unzipped:
                try:
                    f.unlink()
                    deleted_arcade_files += 1
                except Exception:
                    pass
                continue

        # Folder Merge
        if is_alias:
            dst = root / target_plat / f.name
            ensure_dir(dst.parent)
            safe_move(f, dst)

    if is_alias:
        try:
            plat_dir.rmdir()
        except OSError:
            pass

print(f"TERMINADO. {moved_files} reubicados. {deleted_arcade_files} limpiados.")
