Ejecuta un test del pipeline completo (scan → match → plan) sobre una biblioteca de prueba sintética.

Pasos:
1. Crea una carpeta temporal en el sistema: usa `import tempfile, os` en Python para crear `tmp_lib/Game Boy Advance/` con 3 ficheros `.gba` ficticios (nombres realistas: `Metroid Fusion (USA).gba`, `Pokemon - Fire Red Version (USA).gba`, `Castlevania - Aria of Sorrow (USA).gba`)
2. Ejecuta el scanner vía import de Python contra una BD de prueba aislada — **nunca uses el CLI `rommgr scan`**, que siempre escribe en `config.database_path` (la BD real de producción, `.rommgr/library_pc.db`, sin flag para aislarlo — ver `cli.py:466`):
   ```python
   from rom_manager.config import load_config
   from rom_manager.database.repository import LibraryRepository
   from rom_manager.scanner.rom_scanner import scan_library
   import logging
   from pathlib import Path

   cfg = load_config()
   repo = LibraryRepository(Path(tmp_path) / "test.db")
   result = scan_library(Path(tmp_path), cfg, repo, logging.getLogger("test"), quick=True)
   ```
   Verifica que `result.roms_detected == 3` y `result.errors == 0`.
3. Comprueba que los 3 archivos aparecen consultando esa BD de prueba (`Path(tmp_path) / "test.db"`), nunca `.rommgr/library_pc.db`.
4. Ejecuta `build_plan(repo, FormatOptions())` (import directo, mismo `repo` de prueba del paso 2 — `rommgr plan` por CLI tiene el mismo problema que `rommgr scan`, ver `cli.py:1594`) y verifica que no lanza excepción y que `plan.total >= 0`.
5. Verifica que el pruning funciona: borra uno de los ficheros ficticios, vuelve a llamar a `scan_library(...)` con el mismo `repo`, y comprueba que el registro desaparece de la BD de prueba.
6. Limpia la carpeta temporal al terminar.

Presenta los resultados como una tabla:

| Paso | Descripción | Resultado |
|------|-------------|-----------|
| 1 | Crear biblioteca de prueba | ✅/❌ + detalle |
| 2 | Scan | ✅/❌ + ROMs detectados |
| 3 | Verificar BD | ✅/❌ + filas encontradas |
| 4 | Plan | ✅/❌ + JSON válido |
| 5 | Prune stale | ✅/❌ + filas eliminadas |
| 6 | Limpieza | ✅/❌ |

Si algún paso falla, muestra el error completo y sugiere el archivo y línea donde probablemente está el problema.
