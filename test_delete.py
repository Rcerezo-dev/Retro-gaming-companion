import os
from pathlib import Path

p = Path(r"E:\Carpetas anbernic\gb\Metroid II - Return of Samus (World).gb")
print("Existe:", p.exists())
if p.exists():
    try:
        os.remove(str(p))
        print("Borrado OK")
    except Exception as e:
        print("Error:", e)
