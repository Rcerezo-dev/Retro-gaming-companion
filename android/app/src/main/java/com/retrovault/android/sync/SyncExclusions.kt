package com.retrovault.android.sync

/**
 * Carpetas de primer nivel (bajo `saves/` o `states/`) que nunca se sincronizan: no son saves de
 * ningún core, son restos que ya llenaron la cuota de Dropbox (SYNC-REMOTE-TREE-1c).
 *
 * - `retroarch`, `RetroSync`: copias espejo del propio árbol de Dropbox que un sync anterior, con
 *   rutas locales/remotas desalineadas, bajó dentro de `saves/` (p. ej. `saves/retroarch/saves/...`:
 *   233 archivos, ~391 MiB, y otra copia anidada en `saves/RetroSync/saves/retroarch/saves/...`).
 * - `.stversions`, `.stfolder*`: restos de Syncthing.
 * - `_descartados`, `_jubilado*`: papelera/archivo del propio proyecto.
 *
 * Se aplica a los dos lados (local y remoto): si solo se excluyera el local, el motor vería esas
 * rutas como "solo remotas" y las volvería a descargar.
 */
object SyncExclusions {
    private val excludedTopLevel = setOf("retroarch", "retrosync", ".stversions", "_descartados")

    fun isExcluded(relative: String): Boolean {
        val top = relative.trimStart('/').substringBefore('/').lowercase()
        return top in excludedTopLevel || top.startsWith(".stfolder") || top.startsWith("_jubilado")
    }
}
