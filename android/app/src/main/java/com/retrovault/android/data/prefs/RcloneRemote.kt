package com.retrovault.android.data.prefs

/**
 * Recorta un prefijo `remotename:` estilo rclone si el usuario pega un
 * valor tal cual del `config.toml` del PC (p. ej. `"dropbox:/RetroSync/saves"`
 * → `"/RetroSync/saves"`) — la app habla con la API de Dropbox directamente
 * (sin rclone), así que solo necesita el path relativo a Dropbox. Sin esto,
 * un usuario que copia/pega su valor del PC se encuentra con un path roto
 * (ver `Tareas/Roadmap-Android-Sync.md` §1).
 */
fun stripRcloneRemotePrefix(value: String): String {
    val trimmed = value.trim()
    val colonIndex = trimmed.indexOf(':')
    return if (colonIndex >= 0) trimmed.substring(colonIndex + 1) else trimmed
}
