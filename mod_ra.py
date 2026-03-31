import re
from pathlib import Path

cfg_path = Path(r"E:\Emuladores\Retroarch\retroarch.cfg")

if not cfg_path.exists():
    print("retroarch.cfg no encontrado en E:\\Emuladores\\Retroarch")
else:
    text = cfg_path.read_text(encoding="utf-8", errors="replace")
    
    # Nuevas directrices para el documento de RetroArch
    settings = {
        "savefile_directory": r"E:\Carpetas anbernic\saves",
        "savestate_directory": r"E:\Carpetas anbernic\saves",
        "system_directory": r"E:\Carpetas anbernic\bios",
        "sort_savefiles_enable": "true",
        "sort_savestates_enable": "true"
    }

    for k, v in settings.items():
        pattern = rf'^{k}\s*=.*$'
        replacement = f'{k} = "{v}"'
        if re.search(pattern, text, flags=re.MULTILINE):
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        else:
            text += f'\n{k} = "{v}"'

    cfg_path.write_text(text, encoding="utf-8")
    print("¡retroarch.cfg actualizado con éxito!")
