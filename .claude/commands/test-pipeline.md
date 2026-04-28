Ejecuta un test del pipeline completo (scan → match → plan) sobre una biblioteca de prueba sintética.

Pasos:
1. Crea una carpeta temporal en el sistema: usa `import tempfile, os` en Python para crear `tmp_lib/Game Boy Advance/` con 3 ficheros `.gba` ficticios (nombres realistas: `Metroid Fusion (USA).gba`, `Pokemon - Fire Red Version (USA).gba`, `Castlevania - Aria of Sorrow (USA).gba`)
2. Ejecuta el scanner sobre esa carpeta con el comando:
   `C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager scan <tmp_path> --quick`
   Captura stdout/stderr. Verifica que reporta exactamente 3 ROMs detectados y 0 errores.
3. Comprueba que los 3 archivos aparecen en la BD temporal ejecutando una consulta SQLite directa sobre `.rommgr/library_pc.db` en la carpeta del proyecto.
4. Ejecuta `rommgr plan` sobre la carpeta temporal y verifica que devuelve JSON válido con `total >= 0`.
5. Verifica que `prune_stale_entries` funciona: borra uno de los ficheros ficticios, lanza el scan de nuevo, y comprueba que el registro desaparece de la BD.
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
