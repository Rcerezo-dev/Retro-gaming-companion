package com.retrovault.android.sync

import android.os.FileObserver
import android.os.Handler
import android.os.Looper
import java.io.File

/**
 * Detecta escrituras en saves/states para el modo Instantáneo
 * (ANDROID-SYNC-9, reabierto 2026-09-25). `FileObserver` de plataforma no es
 * recursivo — se crea un observer por cada subcarpeta ya existente bajo cada
 * raíz (una por core de RetroArch, ver [collectWatchDirs]).
 *
 * ponytail: un core nuevo que aparezca después de arrancar el observer no se
 * detecta hasta el próximo restart del servicio (no hay watch dinámico de
 * carpetas nuevas) — subir a un `FileObserver` recursivo con re-registro en
 * `CREATE|ISDIR` si esto resulta ser un problema real en uso diario.
 *
 * Debounce con `Handler` en vez de coroutines: RetroArch suele escribir el
 * `.srm` y su `.bak`/`.state.N` casi a la vez — coalesce esa ráfaga en un
 * solo pase de sync.
 */
class SaveFileObserverManager(
    private val roots: List<File>,
    private val debounceMillis: Long = 3_000L,
    private val onChange: () -> Unit,
) {
    private val handler = Handler(Looper.getMainLooper())
    private val debounced = Runnable { onChange() }
    private var observers: List<FileObserver> = emptyList()

    fun start() {
        val watchMask = FileObserver.CLOSE_WRITE or FileObserver.MOVED_TO or FileObserver.DELETE
        observers =
            roots.flatMap { collectWatchDirs(it) }.map { dir ->
                @Suppress("DEPRECATION")
                object : FileObserver(dir.absolutePath, watchMask) {
                    override fun onEvent(
                        event: Int,
                        path: String?,
                    ) {
                        handler.removeCallbacks(debounced)
                        handler.postDelayed(debounced, debounceMillis)
                    }
                }.also { it.startWatching() }
            }
    }

    fun stop() {
        observers.forEach { it.stopWatching() }
        observers = emptyList()
        handler.removeCallbacks(debounced)
    }
}

/**
 * Todas las subcarpetas bajo [root] (inclusive) que ya existen en disco —
 * recorrido puro (solo `java.io.File`), extraído para poder testearlo en JVM
 * sin Android (`SaveFileObserverManagerTest`).
 */
fun collectWatchDirs(root: File): List<File> =
    if (!root.isDirectory) {
        emptyList()
    } else {
        listOf(root) + (root.listFiles(File::isDirectory)?.flatMap(::collectWatchDirs) ?: emptyList())
    }
