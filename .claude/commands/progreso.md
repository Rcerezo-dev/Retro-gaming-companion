Muestra un resumen visual del estado actual del proyecto. **No leas el backlog entero**: ejecuta

`C:/Users/rammu/anaconda3/envs/rom_manager/python.exe scripts/backlog_stats.py --detalle`

(cuenta secciones y filas ✅/abiertas por epic; `Tareas/backlog.md` es el índice). Con esa salida, y abriendo solo con `grep -rn "<ID>" Tareas/backlog/` las secciones que necesites, presenta:

1. Tareas completadas recientemente (secciones en `Tareas/backlog/hecho/` y filas ✅ recientes)
2. Tareas activas o en progreso (secciones `pendiente`)
3. Bugs abiertos y su prioridad
4. El próximo paso concreto recomendado
5. Cualquier bloqueo o decisión pendiente del usuario

Menciona cuántas secciones están en `revisar` (sin tabla de estado): su estado no es fiable. Formato claro y legible, con secciones separadas.
