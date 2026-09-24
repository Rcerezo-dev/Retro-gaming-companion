package com.retrovault.android.sync

import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/**
 * FTP-PICK-2 (rediseñado): cliente HTTP para elegir ROMs desde el PC —
 * reutiliza `GET /api/games` (buscar/filtrar) y `GET /api/download-rom`
 * (descargar) del servidor `rommgr serve` que ya existen y ya están
 * probados en `tests/web/test_download_rom.py`. Sin librería nueva:
 * `HttpURLConnection` y `org.json` son parte de la plataforma Android.
 */
data class RemoteGame(
    val id: Long,
    val platform: String?,
    val canonicalTitle: String?,
    val originalFilename: String,
    val sourcePath: String,
    val sizeBytes: Long,
) {
    /** Carpeta de plataforma del PC (p.ej. "megadrive") — el segmento
     * inmediatamente anterior al nombre de archivo en `sourcePath`, sea cual
     * sea la letra de unidad o separador (`/` o `\`) del PC de origen. */
    val platformFolder: String
        get() = sourcePath.replace('\\', '/').trimEnd('/').substringBeforeLast('/').substringAfterLast('/')
}

object PcApiClient {
    private const val TIMEOUT_MS = 15_000

    private fun openConnection(url: String): HttpURLConnection {
        val conn = URL(url).openConnection() as HttpURLConnection
        conn.connectTimeout = TIMEOUT_MS
        conn.readTimeout = TIMEOUT_MS
        conn.requestMethod = "GET"
        return conn
    }

    /** Lanza si el PC no responde 200 (host apagado, puerto equivocado, PIN
     * activo sin sesión...). El mensaje llega tal cual a la UI. */
    private fun requireOk(conn: HttpURLConnection) {
        val code = conn.responseCode
        if (code != HttpURLConnection.HTTP_OK) {
            error("El PC respondió $code — revisa la IP/puerto, o que rommgr serve esté sin PIN")
        }
    }

    fun listPlatforms(baseUrl: String): List<String> {
        val conn = openConnection("$baseUrl/api/games/filter-options")
        requireOk(conn)
        val json = JSONObject(conn.inputStream.bufferedReader().readText())
        val platforms = json.optJSONArray("platforms") ?: JSONArray()
        return (0 until platforms.length()).map { platforms.getString(it) }
    }

    fun listGames(
        baseUrl: String,
        platform: String?,
        search: String?,
        offset: Int = 0,
        limit: Int = 200,
    ): List<RemoteGame> {
        val params =
            buildList {
                add("offset=$offset")
                add("limit=$limit")
                add("filetype=rom")
                platform?.takeIf { it.isNotBlank() }?.let { add("platform=" + URLEncoder.encode(it, "UTF-8")) }
                search?.takeIf { it.isNotBlank() }?.let { add("search=" + URLEncoder.encode(it, "UTF-8")) }
            }
        val conn = openConnection("$baseUrl/api/games?${params.joinToString("&")}")
        requireOk(conn)
        val json = JSONObject(conn.inputStream.bufferedReader().readText())
        val games = json.optJSONArray("games") ?: JSONArray()
        return (0 until games.length()).map { i ->
            val g = games.getJSONObject(i)
            RemoteGame(
                id = g.getLong("id"),
                platform = if (g.isNull("platform")) null else g.optString("platform"),
                canonicalTitle = if (g.isNull("canonical_title")) null else g.optString("canonical_title"),
                originalFilename = g.getString("original_filename"),
                sourcePath = g.getString("source_path"),
                sizeBytes = g.optLong("size_bytes", 0L),
            )
        }
    }

    /** Descarga *game* a `<romsDestPath>/<platformFolder>/<originalFilename>`. */
    fun downloadRom(
        baseUrl: String,
        game: RemoteGame,
        romsDestPath: String,
        onProgress: (transferred: Long, total: Long) -> Unit = { _, _ -> },
    ): File {
        val encodedPath = URLEncoder.encode(game.sourcePath, "UTF-8")
        val conn = openConnection("$baseUrl/api/download-rom?path=$encodedPath")
        requireOk(conn)
        val total = conn.contentLengthLong
        val destFile = File(File(romsDestPath, game.platformFolder), game.originalFilename)
        destFile.parentFile?.mkdirs()
        var transferred = 0L
        conn.inputStream.use { input ->
            FileOutputStream(destFile).use { out ->
                val buf = ByteArray(256 * 1024)
                while (true) {
                    val n = input.read(buf)
                    if (n <= 0) break
                    out.write(buf, 0, n)
                    transferred += n
                    onProgress(transferred, total)
                }
            }
        }
        return destFile
    }
}
