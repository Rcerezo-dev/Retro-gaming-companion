package com.retrovault.android.sync

/**
 * Extensiones de save/state que el motor de sync reconoce. Deben mantenerse
 * byte-a-byte idénticas a `save_extensions`/`state_extensions` en
 * `src/rom_manager/config.py:544-576` (AppConfig, plataforma RetroArch) —
 * no hay fuente compartida entre Python y Kotlin, ver
 * `Tareas/Roadmap-Android-Sync.md` §10 sobre este riesgo de deriva.
 */
object SaveExtensions {
    val save: Set<String> =
        setOf(
            ".sav", ".srm", ".state", ".st0", ".st1", ".st2", ".st3", ".st4", ".st5",
            ".fcs", ".dsv", ".sps", ".psv", ".mcr", ".mem", ".vmp", ".eep", ".fla",
            ".sra", ".sgm", ".brm", ".nv", ".hi", ".state1", ".state2", ".brmc",
            ".ml1", ".mcd", ".ps2", ".gci",
        )

    val state: Set<String> =
        setOf(
            ".state", ".state1", ".state2", ".st0", ".st1", ".st2", ".st3", ".st4",
            ".st5", ".ppst", ".fcs", ".sps", ".psv", ".hi", ".brmc", ".ml1",
        )

    /** Unión de ambos conjuntos — nunca se recogen archivos fuera de esto. */
    val tracked: Set<String> = save + state

    fun isTracked(extension: String): Boolean = extension.lowercase() in tracked
}
