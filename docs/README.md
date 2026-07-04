# Retro Vault — Documentación

Índice de toda la documentación técnica, guías y referencias del proyecto.

---

## Guías de uso

| Documento | Contenido |
|-----------|-----------|
| [guia-pruebas.md](guia-pruebas.md) | Instalación desde cero y verificación de cada función — para probar en un PC nuevo |
| [arcade-setup.md](arcade-setup.md) | Configuración de ROMs arcade: MAME/FBNeo, cores y DATs |
| [emulator-compat.md](emulator-compat.md) | Matriz de compatibilidad de saves PC ↔ Android por emulador |

## Desarrollo

| Documento | Contenido |
|-----------|-----------|
| [ci-cd.md](ci-cd.md) | Pipeline CI/CD: GitHub Actions, branch protection, ramas, pre-commit, gotchas |
| [SKILLS-QUICK-START.md](SKILLS-QUICK-START.md) | Skills y agents de Claude Code disponibles en el proyecto |

## Arquitectura

| Documento | Contenido |
|-----------|-----------|
| [architecture.md](architecture/architecture.md) | Estructura técnica completa: módulos, base de datos, flujos |
| [frontend.md](architecture/frontend.md) | Arquitectura del frontend JS: tabs, estado, polling |
| [platforms-cores.md](architecture/platforms-cores.md) | Plataformas soportadas y núcleos RetroArch |
| [Roadmap-Arquitectura-Frontend.md](architecture/Roadmap-Arquitectura-Frontend.md) | Diseño original de la migración frontend (referencia histórica) |

## Configuración

| Documento | Contenido |
|-----------|-----------|
| [library-structure.md](config/library-structure.md) | Estructura de carpetas de la biblioteca (ES-DE compatible) |
| [Rutas-Referencia.md](config/Rutas-Referencia.md) | Rutas absolutas de plataformas en PC y consola |
| [Configuración-ES-DE.md](config/Configuración-ES-DE.md) | Guía de configuración de EmulationStation DE |
| [esde-themes.md](config/esde-themes.md) | Temas y personalización de ES-DE |

## Sincronización

| Documento | Contenido |
|-----------|-----------|
| [android-save-paths-RG556.md](sync/android-save-paths-RG556.md) | Rutas ADB de saves por emulador — verificadas en RG556 |
| [sync-cable.md](sync/sync-cable.md) | Cable Sync: ADB, SD card, SFTP — cómo conectar y transferir |
| [sync-cloud.md](sync/sync-cloud.md) | Cloud Sync: rclone + Dropbox — setup y flujo |
| [Guia-Termux-Anbernic.md](sync/Guia-Termux-Anbernic.md) | Guía completa: Termux + rclone en la Anbernic RG556 |
| [sync-wifi-sftp.md](sync/sync-wifi-sftp.md) | WiFi Sync: servidor SFTP en Termux + transferencia sin cable |

## Ideas y propuestas

| Documento | Contenido |
|-----------|-----------|
| [Idea_final.md](ideas/Idea_final.md) | Visión completa de la app: tabs, flujo, problemas abiertos |
| [propuestas-recomendador-nlp.md](ideas/propuestas-recomendador-nlp.md) | Análisis de viabilidad de recomendador de juegos con NLP |

## Archivo

Documentos obsoletos o supersedidos, conservados como referencia histórica.

| Documento | Por qué está archivado |
|-----------|------------------------|
| [refactor-plan.md](_archive/refactor-plan.md) | El refactor está completado |
| [retroarch-saves-anbernic.md](_archive/retroarch-saves-anbernic.md) | Supersedido por `android-save-paths-RG556.md` |
| [android-sync.md](_archive/android-sync.md) | Supersedido por `Guia-Termux-Anbernic.md` |
| [guia-consola-android.md](_archive/guia-consola-android.md) | Supersedido por `Guia-Termux-Anbernic.md` |
