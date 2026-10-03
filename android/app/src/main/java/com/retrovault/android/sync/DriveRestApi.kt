package com.retrovault.android.sync

import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.time.Instant

/** Escapa un valor para usarlo entre comillas simples en el parámetro `q` de Drive. */
internal fun escapeDriveQuery(value: String): String = value.replace("\\", "\\\\").replace("'", "\\'")

internal fun formatDriveTime(millis: Long): String = Instant.ofEpochMilli(millis).toString()

internal fun parseDriveTime(value: String?): Long =
    value?.let { runCatching { Instant.parse(it).toEpochMilli() }.getOrNull() } ?: 0L

/**
 * [DriveApi] sobre la API REST de Drive v3 con `HttpURLConnection` — sin
 * dependencias nuevas (el cliente oficial añade ~MB al APK y no aporta nada
 * que esto no cubra). [tokenProvider] devuelve un access token vigente
 * (scope `drive.file`); de dónde sale lo resuelve el Picker/auth (Fase 2).
 *
 * Los errores HTTP se lanzan como [IOException] con el cuerpo de Drive, para
 * que aparezcan en el historial de sync igual que los de Dropbox.
 *
 * **Sin probar contra Drive real todavía** — no hay token hasta que exista el
 * flujo de autorización con Picker; solo está cubierto lo puro (escape,
 * fechas) y el transporte con un [DriveApi] falso.
 */
class DriveRestApi(private val tokenProvider: () -> String) : DriveApi {
    private companion object {
        const val API = "https://www.googleapis.com/drive/v3"
        const val UPLOAD = "https://www.googleapis.com/upload/drive/v3"
        const val FIELDS = "id,name,mimeType,modifiedTime,size"
        const val FOLDER_MIME = "application/vnd.google-apps.folder"
        const val BOUNDARY = "retrovault_boundary_7f3a"
    }

    private fun enc(value: String) = URLEncoder.encode(value, "UTF-8")

    private fun open(
        url: String,
        method: String,
    ): HttpURLConnection {
        val conn = URL(url).openConnection() as HttpURLConnection
        conn.connectTimeout = 15_000
        conn.readTimeout = 60_000
        // HttpURLConnection no admite PATCH: Google acepta el override sobre POST.
        if (method == "PATCH") {
            conn.requestMethod = "POST"
            conn.setRequestProperty("X-HTTP-Method-Override", "PATCH")
        } else {
            conn.requestMethod = method
        }
        conn.setRequestProperty("Authorization", "Bearer ${tokenProvider()}")
        return conn
    }

    private fun HttpURLConnection.checkedStream() =
        if (responseCode in 200..299) {
            inputStream
        } else {
            val body = errorStream?.bufferedReader()?.readText().orEmpty()
            throw IOException("Drive HTTP $responseCode: ${body.take(300)}")
        }

    private fun HttpURLConnection.readJson() = JSONObject(checkedStream().bufferedReader().use { it.readText() })

    private fun itemFrom(json: JSONObject) =
        DriveItem(
            id = json.getString("id"),
            name = json.getString("name"),
            isFolder = json.optString("mimeType") == FOLDER_MIME,
            modifiedMillis = parseDriveTime(json.optString("modifiedTime", null)),
            size = json.optString("size", "0").toLongOrNull() ?: 0L,
        )

    override fun listChildren(parentId: String): List<DriveItem> {
        val out = mutableListOf<DriveItem>()
        var pageToken: String? = null
        do {
            val q = "'${escapeDriveQuery(parentId)}' in parents and trashed=false"
            val url =
                "$API/files?q=${enc(q)}&fields=${enc("nextPageToken,files($FIELDS)")}&pageSize=1000" +
                    (pageToken?.let { "&pageToken=${enc(it)}" } ?: "")
            val json = open(url, "GET").readJson()
            val files: JSONArray = json.optJSONArray("files") ?: JSONArray()
            for (i in 0 until files.length()) out += itemFrom(files.getJSONObject(i))
            pageToken = json.optString("nextPageToken", "").ifEmpty { null }
        } while (pageToken != null)
        return out
    }

    override fun createFolder(
        parentId: String,
        name: String,
    ): DriveItem {
        val conn = open("$API/files?fields=${enc(FIELDS)}", "POST")
        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8")
        conn.doOutput = true
        val body = JSONObject().put("name", name).put("mimeType", FOLDER_MIME).put("parents", JSONArray().put(parentId))
        conn.outputStream.use { it.write(body.toString().toByteArray()) }
        return itemFrom(conn.readJson())
    }

    override fun uploadFile(
        parentId: String,
        existingId: String?,
        name: String,
        file: File,
        modifiedMillis: Long,
    ): DriveItem {
        val metadata = JSONObject().put("name", name).put("modifiedTime", formatDriveTime(modifiedMillis))
        if (existingId == null) metadata.put("parents", JSONArray().put(parentId))
        val head =
            (
                "--$BOUNDARY\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n$metadata\r\n" +
                    "--$BOUNDARY\r\nContent-Type: application/octet-stream\r\n\r\n"
            ).toByteArray()
        val tail = "\r\n--$BOUNDARY--".toByteArray()
        val url =
            if (existingId == null) {
                "$UPLOAD/files?uploadType=multipart&fields=${enc(FIELDS)}"
            } else {
                "$UPLOAD/files/${enc(existingId)}?uploadType=multipart&fields=${enc(FIELDS)}"
            }
        val conn = open(url, if (existingId == null) "POST" else "PATCH")
        conn.setRequestProperty("Content-Type", "multipart/related; boundary=$BOUNDARY")
        conn.doOutput = true
        conn.setFixedLengthStreamingMode(head.size.toLong() + file.length() + tail.size)
        conn.outputStream.use { out ->
            out.write(head)
            file.inputStream().use { it.copyTo(out) }
            out.write(tail)
        }
        return itemFrom(conn.readJson())
    }

    override fun downloadFile(
        fileId: String,
        dest: File,
    ) {
        dest.parentFile?.mkdirs()
        // .part: un corte a mitad no deja un save truncado con el nombre real
        // (la extensión .part no la rastrea LocalFileScanner).
        val tmp = File(dest.parentFile, dest.name + ".part")
        open("$API/files/${enc(fileId)}?alt=media", "GET").checkedStream().use { input ->
            tmp.outputStream().use { input.copyTo(it) }
        }
        if (!tmp.renameTo(dest)) {
            tmp.copyTo(dest, overwrite = true)
            tmp.delete()
        }
    }
}
