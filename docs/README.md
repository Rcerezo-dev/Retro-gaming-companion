# Documentación de Retro Vault

Índice completo de documentación técnica, guías de usuario y referencias arquitectónicas.

---

## 📚 Documentación principal

### 🏗️ Arquitectura y diseño

- **[architecture.md](architecture.md)** — Estructura técnica completa del proyecto
- **[platforms-cores.md](platforms-cores.md)** — Plataformas soportadas y núcleos emuladores

### 🎮 Configuración

- **[library-structure.md](library-structure.md)** — Cómo organizar tu biblioteca de ROMs
- **[sync-cable.md](sync-cable.md)** — Sincronización por cable USB (ADB / SD card)
- **[sync-cloud.md](sync-cloud.md)** — Sincronización en la nube (rclone, Dropbox, etc.)
- **[android-sync.md](android-sync.md)** — Setup de sync automático en Anbernic/Android

---

## 📖 Guías prácticas

Ver carpeta **[`guias/`](guias/README.md)** para:

- **[Estructura de saves en Anbernic](guias/retroarch-saves-anbernic.md)** — Mapeo de plataformas, configuración, troubleshooting
- Más guías en desarrollo...

---

## 🔍 Búsqueda rápida

| Busco... | Documento |
|----------|-----------|
| Cómo configurar mi consola Android | [guias/retroarch-saves-anbernic.md](guias/retroarch-saves-anbernic.md) |
| Sincronizar saves automáticamente | [android-sync.md](android-sync.md) |
| Organizar mis ROMs | [library-structure.md](library-structure.md) |
| Entender la arquitectura del código | [architecture.md](architecture.md) |
| Qué emuladores/núcleos se soportan | [platforms-cores.md](platforms-cores.md) |
| Transferir datos por USB | [sync-cable.md](sync-cable.md) |
| Usar Dropbox/Google Drive | [sync-cloud.md](sync-cloud.md) |

---

## 📋 Notas

- **Última actualización:** 2026-03-21
- **Versión:** Retro Vault v1.0 (en desarrollo)
- **Plataforma soportada:** Windows 10+, Python 3.11+

---

## 🔗 Enlaces relacionados

- **GitHub:** https://github.com/anthropics/retro-vault
- **Configuración inicial:** Ver `config.toml.example`
- **Roadmap futuro:** Ver `Tareas/Día16.md`
