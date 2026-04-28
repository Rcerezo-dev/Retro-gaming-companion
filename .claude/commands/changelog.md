Genera un changelog legible por humanos basado en los commits recientes del proyecto.

Pasos:

1. Ejecuta `git log --oneline -30` para ver los últimos 30 commits.
2. Ejecuta `git log --format="%H %s" -30` para obtener los hashes completos.
3. Para los commits más recientes (últimos 10), ejecuta `git show --stat <hash>` para ver qué archivos cambió cada uno.
4. Lee `Tareas/Día10-Mejoras-Pendientes.md` para cruzar los commits con las features implementadas.

Genera el changelog en este formato:

```markdown
# Changelog — Retro Vault

## [sin versión] — 2026-03-16
### ✨ Nuevas funcionalidades
- **Tracker de partidas**: la app recuerda cuándo jugaste cada juego por última vez (Overview → Últimas partidas)
- ...

### 🐛 Bugs corregidos
- ...

### 🔧 Mejoras técnicas
- ...

### ⚠️ Pendiente de probar en hardware
- ...
```

Agrupa los cambios por tipo (feature / bug / técnico / pendiente), no por commit. Usa lenguaje orientado al usuario final, no al desarrollador (ej: "ahora puedes marcar juegos como Completados" en lugar de "añadida columna play_status a la tabla games").

Guarda el resultado en `CHANGELOG.md` en la raíz del proyecto.
