import os
import glob
from collections import defaultdict

rom_dir = r"E:\Carpetas anbernic"
catalogs_dir = r"c:\Users\rammu\Documents\projects\Retro_gaming_app\.rommgr\catalogs"
output_file = r"c:\Users\rammu\Documents\projects\Retro_gaming_app\check_results.txt"

# 1. Get all catalogs
dat_files = glob.glob(os.path.join(catalogs_dir, '**', '*.dat'), recursive=True)
db_files = glob.glob(os.path.join(catalogs_dir, '**', '*.db'), recursive=True)
catalogs = [os.path.basename(f) for f in dat_files + db_files]

# 2. Get all platforms from E:\Carpetas anbernic
ignore_dirs = {
    'Alarms', 'Android', 'Audiobooks', 'DCIM', 'Documents', 'Download', 
    'Movies', 'Music', 'Notifications', 'Nueva carpeta', 'Pictures', 
    'Podcasts', 'Recordings', 'Ringtones', 'System Volume Information', 
    'Unknown', 'backup', 'bgmusic', 'inbox', 'recovery_log', 'saves', 
    'screenshots', 'states', 'BIOS'
}

platforms = [d for d in os.listdir(rom_dir) if os.path.isdir(os.path.join(rom_dir, d)) and d not in ignore_dirs]

# 3. Check for mismatches in E:\Carpetas anbernic directories
platform_files = defaultdict(list)
platform_extensions = defaultdict(lambda: defaultdict(int))
misplaced_candidates = defaultdict(list)

# Simple expected extensions (lowercase) for some common consoles
EXPECTED_EXTS = {
    'gb': {'.gb', '.zip', '.7z'},
    'gbc': {'.gbc', '.zip', '.7z'},
    'gba': {'.gba', '.zip', '.7z'},
    'nes': {'.nes', '.zip', '.7z'},
    'snes': {'.smc', '.sfc', '.zip', '.7z'},
    'megadrive': {'.md', '.bin', '.gen', '.smd', '.zip', '.7z'},
    'mastersystem': {'.sms', '.zip', '.7z'},
    'gamegear': {'.gg', '.zip', '.7z'},
    'n64': {'.n64', '.v64', '.z64', '.zip', '.7z'},
    'psx': {'.bin', '.cue', '.iso', '.chd', '.pbp', '.m3u'},
    'psp': {'.iso', '.cso', '.pbp'},
    'nds': {'.nds', '.zip', '.7z'},
    '3ds': {'.3ds', '.cia'},
    'Game Boy Advance': {'.gba', '.zip', '.7z'},
    'gamecube': {'.iso', '.rvz', '.gcm', '.ciso'},
    'wii': {'.iso', '.wbfs', '.rvz'},
    'ps2': {'.iso', '.bin', '.chd', '.gz'},
    'ps3': {'.iso', '.m3u', '.chd'},
    'dreamcast': {'.gdi', '.cdi', '.chd'},
    'neogeo': {'.zip', '.7z'},
    'arcade': {'.zip', '.7z'},
    'mame': {'.zip', '.7z'},
    'famicom': {'.fds', '.nes', '.zip', '.7z'},
    'msx1': {'.rom', '.zip', '.7z'},
    'msx2': {'.rom', '.zip', '.7z'},
    'saturn': {'.cue', '.bin', '.iso', '.chd'},
    'ss': {'.cue', '.bin', '.iso', '.chd'},
    'segacd': {'.cue', '.bin', '.iso', '.chd'},
    'sega32x': {'.32x', '.zip', '.7z'}
}

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"--- CATALOGS FOUND ---\n")
    for cat in catalogs:
        f.write(f"{cat}\n")
    f.write(f"\n--- PLATFORMS FOUND ---\n")
    f.write(", ".join(platforms) + "\n\n")

    f.write(f"--- POTENTIALLY MISPLACED GAMES ---\n")
    for plat in platforms:
        plat_path = os.path.join(rom_dir, plat)
        for root, _, files in os.walk(plat_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                platform_extensions[plat][ext] += 1
                
                if plat in EXPECTED_EXTS:
                    if ext and ext not in EXPECTED_EXTS[plat] and ext not in {'.txt', '.png', '.jpg', '.xml', '.dat'}:
                        misplaced_candidates[plat].append(file)
                else:
                    # Gather unusual looking extensions for any unknown platforms
                    if ext in {'.exe', '.dll', '.msi', '.docx', '.mp4', '.mkv'}:
                         misplaced_candidates[plat].append(file)

    for plat in platforms:
        if plat in misplaced_candidates and misplaced_candidates[plat]:
            f.write(f"\nPlatform: {plat}\n")
            for file in misplaced_candidates[plat]:
                f.write(f"  - {file}\n")

    f.write(f"\n--- EXTENSION SUMMARY BY PLATFORM ---\n")
    for plat, exts in platform_extensions.items():
        if exts:
            ext_str = ", ".join(f"{k}: {v}" for k, v in exts.items())
            f.write(f"{plat}: {ext_str}\n")
