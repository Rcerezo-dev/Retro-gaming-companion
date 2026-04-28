Audita la interfaz de usuario de `src/rom_manager/web/frontend.py` desde la perspectiva de un usuario que abre la app por primera vez.

Lee el archivo completo y evalúa los siguientes criterios:

### 1. Texto mezclado (español/inglés)
Busca strings en inglés que deberían estar en español. Ignora: nombres técnicos (SHA1, ROM, CHD, ADB, rclone, API key), código de ejemplo, placeholders de input. Reporta los demás.

### 2. Mensajes de error accionables
Para cada `error` o mensaje de fallo visible al usuario, evalúa si:
- Explica qué salió mal (no solo "Error")
- Dice qué hacer para solucionarlo
- Reporta los que solo dicen el error sin guía de acción

### 3. Estados de carga ausentes
Identifica botones que lanzan operaciones largas (scan, match, sync, apply) y verifica que tienen:
- Estado "cargando" / spinner / texto de progreso mientras trabajan
- Están deshabilitados durante la operación para evitar doble clic
- Reporta los que no cumplan esto

### 4. Flujos incompletos (callejones sin salida)
Busca casos donde el usuario puede llegar a un estado sin saber qué hacer:
- Mensajes vacíos sin sugerencia de próximo paso
- Listas vacías sin explicación de por qué están vacías y cómo poblarlas
- Resultados de error sin botón de reintento o alternativa

### 5. Consistencia visual
- Labels que describen lo mismo de formas distintas (ej. "Consola Android" vs "Anbernic" vs "dispositivo")
- Botones de acción equivalente con estilos diferentes sin razón aparente

Formato del informe:

## UI Audit — Retro Vault
### 🔴 Crítico (rompe la experiencia)
### 🟡 Moderado (confunde al usuario)
### 🟢 Menor (pulido)

Cada ítem: **[Archivo:línea]** Descripción del problema + sugerencia de fix.

Al final, indica los 3 fixes de mayor impacto para hacer primero.
