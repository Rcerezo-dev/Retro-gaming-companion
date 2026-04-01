# Roadmap — Retro Vault para cualquier jugador

> Originado en: `Día13-Grandes-pasos.md` — "qué necesitaría esta app para ser útil para cualquier jugador retro que no quiera comerse mucho la cabeza configurando"
> Fecha: 2026-03-17

---

## El problema central

Ahora mismo la app asume demasiado:
- Que tienes Python y Conda instalados
- Que sabes editar un `config.toml`
- Que conoces las rutas de RetroArch, de tus ROMs, de tu consola
- Que tienes DATs de No-Intro descargados
- Que entiendes qué es un "core" o un "save state"

Un jugador normal no tiene nada de eso. El objetivo es que pueda pasar de cero a jugando en menos de 15 minutos, sin tocar ningún archivo de texto.

---

## Bugs críticos a resolver antes de cualquier otra cosa

Estos problemas afectan al uso diario y deben corregirse primero.

| # | Problema | Síntoma | Solución |
|---|---------|---------|---------|
| **B1** | **Las rutas no se guardan entre sesiones** | Hay que volver a introducir `library_root` y `android_root` cada vez que se abre la app | Investigar si `config.toml` se está escribiendo en la ruta correcta y si se lee al arrancar. Asegurarse de que la UI carga los valores guardados al abrir Settings. |
| **B2** | **Batch run de Tools incompleto** | Solo ejecuta ZIPs, CHD y Health Check — faltan Scan, Match, Scraper, RetroAchievements, Orphan Finder | Añadir los tools que faltan al batch run con checkboxes, respetar el orden lógico (ver Fase 0) |
| **B3** | **Bibliotecas PC y Android no se sincronizan por completo** | Solo se sincronizan saves, no ROMs — las dos bibliotecas pueden tener contenido distinto sin que la app lo detecte | Ver Fase 0 |

---

## Fase 0 — Parches funcionales (antes de pensar en otros usuarios)

Mejoras que afectan al uso diario tuyo ahora mismo.

### 0A — Batch run completo en Tools

El botón "Ejecutar todo" debería lanzar **todos** los tools en el orden correcto, tanto para PC como para la consola Android según el selector de contexto activo.

Orden lógico de ejecución:
1. Escanear biblioteca (Scan)
2. Comparar contra catálogos DAT (Match)
3. Comprobar salud de archivos (Health Check)
4. Buscar saves huérfanos (Orphan Finder)
5. Descomprimir ZIPs (Extract ZIP)
6. Convertir a CHD (Convert CHD)
7. Scraper de metadatos y carátulas (Scraper)
8. Comprobar RetroAchievements (RA Check)

Cada tool ya existe — solo hay que añadirlos al batch run con sus checkboxes y respetar que cada uno espera al anterior.

### 0B — Bibliotecas exactamente iguales en PC y Android

El objetivo final del sync no son solo los saves — es que ambas bibliotecas sean **idénticas**: mismos ROMs, mismas carátulas, mismos metadatos.

Lo que falta:
- **Comparador de bibliotecas**: pantalla que muestre qué juegos están en PC pero no en Android y viceversa
- **Sync bidireccional de ROMs**: copiar los que faltan en cada lado (ya existe para saves, falta para ROMs)
- **Verificación post-sync**: después del sync, re-comparar y confirmar que ambas listas son iguales
- **Política de conflictos para ROMs**: si el mismo juego existe en ambos lados con SHA1 distinto (versión diferente), qué hacer — mostrar al usuario, no decidir solo

### 0C — Persistencia de rutas

Las rutas introducidas en Settings deben persistir entre reinicios. Investigar:
1. ¿Se escribe el `config.toml` en la ruta correcta? (`project_root/config.toml`)
2. ¿La UI carga los valores de `config.toml` al abrir la pestaña Settings?
3. ¿El servidor recarga `config.toml` al arrancar en vez de usar valores en memoria del arranque anterior?

---

## Fase 1 — Primer arranque sin fricción

**Objetivo:** wizard de configuración que detecta todo automáticamente. El usuario solo confirma, no escribe rutas.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Wizard en la web** | Pantalla de bienvenida la primera vez que no existe `config.toml`. Pasos guiados: detectar biblioteca → detectar RetroArch → detectar dispositivo → crear estructura | Alto |
| **Auto-detección de RetroArch** | Buscar `retroarch.exe` en rutas comunes (`C:\RetroArch-Win64`, Steam, RetroBat, `Program Files`) y ofrecer la encontrada como opción | Medio |
| **Auto-detección de cores** | Leer la carpeta `cores/` de RetroArch y mapear automáticamente qué sistemas están disponibles. Avisar si falta algún core relevante. | Medio |
| **Generador de `es_systems.cfg`** | Con lo anterior, generar el config de EmulationStation automáticamente. El usuario no toca el archivo nunca. | Medio |
| **Auto-detección de dispositivo Android** | Al conectar un cable USB, detectar el dispositivo via ADB y proponer sus rutas de saves automáticamente | Medio |
| **Selector de carpeta de biblioteca** | Botón "Examinar" que abre el explorador de Windows en vez de escribir la ruta a mano | Bajo |

---

## Fase 2 — DATs sin esfuerzo

**Objetivo:** el usuario no debería saber qué es un DAT ni tener que buscarlo.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Descarga guiada de DATs** | Botón en la UI: "Descargar catálogos". Explica qué son, descarga los DATs relevantes para los sistemas que tiene el usuario | Alto |
| **DATs mínimos incluidos** | Incluir en el instalador DATs para los sistemas más comunes (NES, SNES, GBA, PSX). Matching funciona out-of-the-box. | Alto |
| **Matching sin DAT claro en UI** | Dejar claro cuándo el match es "con DAT" vs "por nombre". | Bajo |

---

## Fase 3 — Sync sin configuración

**Objetivo:** el sync de saves y ROMs funciona sin que el usuario sepa qué es rclone.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Wizard de sync cloud** | Elige proveedor → abre navegador para autorizar → genera config de rclone automáticamente | Alto |
| **WiFi sync directo (sin nube)** | Sync PC ↔ consola en la misma red via SFTP. Prerequisito: Termux + sshd (guía ya escrita). | Medio |
| **Sync automático al conectar** | Al detectar el dispositivo, preguntar "¿Sincronizar ahora?". Un clic. | Bajo |
| **Estado de sync siempre visible** | "Último sync hace 2 horas · 3 archivos actualizados". Sin buscar logs. | Bajo |

---

## Fase 4 — UX para no-técnicos

**Objetivo:** que alguien que nunca ha tocado una terminal pueda usar la app.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Errores en lenguaje humano** | Ningún stack trace. Cada error tiene un mensaje claro y una acción concreta. | Medio |
| **Ayuda contextual** | Tooltips e iconos `?` en cada sección. Sin necesidad de leer documentación externa. | Medio |
| **UI responsive** | Funciona desde el navegador de la consola Android (tablet mode). | Medio |
| **Notificaciones del sistema** | Toast de Windows al terminar un sync o detectar juegos nuevos en inbox. | Bajo |
| **Nombres sin jerga** | "Catálogos DAT" → "Base de datos de juegos", "SHA1 match" → "Identificación automática", etc. | Bajo |

---

## Fase 5 — Autenticación y acceso remoto

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **PIN de acceso** | Cuando `host = 0.0.0.0`, pedir PIN antes de mostrar la UI. | Bajo |
| **QR code de acceso** | QR en la pantalla principal con `http://{ip_local}:7777` para conectar desde la consola sin escribir la IP. | Bajo |

---

## Fase 6 — Distribución (la última, cuando todo lo anterior funciona)

No tiene sentido empaquetar hasta que la app funcione sin fricción para ti. Cuando estés seguro de que funciona end-to-end, entonces:

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Tests de integración sólidos** | Suite que valide el pipeline completo antes de cada release. Imprescindible antes de distribuir. | Alto |
| **Ejecutable único** | PyInstaller → `RetroVault.exe` con Python embebido. Doble clic y funciona. | Alto |
| **Instalador Windows** | Inno Setup: acceso directo en escritorio, entrada en "Programas y características" | Medio |
| **Auto-arranque opcional** | Opción en Settings para iniciar con Windows (bandeja del sistema). | Bajo |
| **Auto-update** | Al arrancar, comprobar si hay versión nueva en GitHub Releases y avisar. | Bajo |
| **Nombre definitivo** | Decidir entre Retro Vault y Retro Companion. README orientado al usuario final. | Bajo |

---

## Orden de prioridad real

```
Bugs críticos (B1, B2, B3)
        ↓
Fase 0 (parches funcionales: batch run completo, bibliotecas iguales, persistencia)
        ↓
Fase 1 (wizard primer arranque) + Fase 4 (UX) — en paralelo
        ↓
Fase 2 (DATs) + Fase 3 (sync completo) — en paralelo
        ↓
Fase 5 (auth) → Fase 6 (distribución) ← solo cuando todo lo anterior funciona
```

---

## Lo que ya funciona y no hay que rehacer

- Todo el pipeline técnico (scan, match, rename, CHD, scraper, RA, sync de saves) implementado.
- La estructura de biblioteca en disco es correcta y compatible con RetroArch y ES.
- La integración con RetroArch y EmulationStation está configurada y documentada.

El trabajo que queda es de producto y UX — envolver lo que existe para que sea accesible sin conocimientos previos.
