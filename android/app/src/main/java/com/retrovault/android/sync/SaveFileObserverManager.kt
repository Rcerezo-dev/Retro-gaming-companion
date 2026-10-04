package com.retrovault.android.sync

import android.os.FileObserver
import android.os.Handler
import android.os.Looper
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean

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
 * Throttle (no debounce) con `Handler`: el primer evento arma un único pase
 * `throttleMillis` después y los siguientes se suman al mismo — un autosave
 * periódico de RetroArch (o la ráfaga `.srm` + `.bak`/`.state.N`) da como mucho
 * un pase por ventana, en vez de reiniciar el temporizador sin llegar a
 * dispararse. [onChange] recibe solo las raíces que cambiaron, para que el
 * pase no recorra las demás.
 */
class SaveFileObserverManager(
    private val roots: List<File>,
    private val throttleMillis: Long = 30_000L,
    private val onChange: (Set<File>) -> Unit,
) {
    private val handler = Handler(Looper.getMainLooper())
    private val dirtyRoots: MutableSet<File> = ConcurrentHashMap.newKeySet()
    private val scheduled = AtomicBoolean(false)
    private val fire =
        Runnable {
            scheduled.set(false)
            val changed = dirtyRoots.toSet()
            dirtyRoots.removeAll(changed)
            if (changed.isNotEmpty()) onChange(changed)
        }
    private var observers: List<FileObserver> = emptyList()

    fun start() {
        val watchMask = FileObserver.CLOSE_WRITE or FileObserver.MOVED_TO or FileObserver.DELETE
        observers =
            roots.flatMap { root -> collectWatchDirs(root).map { it to root } }.map { (dir, root) ->
                @Suppress("DEPRECATION")
                object : FileObserver(dir.absolutePath, watchMask) {
                    override fun onEvent(
                        event: Int,
                        path: String?,
                    ) {
                        dirtyRoots.add(root)
                        if (scheduled.compareAndSet(false, true)) handler.postDelayed(fire, throttleMillis)
                    }
                }.also { it.startWatching() }
            }
    }

    fun stop() {
        observers.forEach { it.stopWatching() }
        observers = emptyList()
        handler.removeCallbacks(fire)
        scheduled.set(false)
        dirtyRoots.clear()
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
