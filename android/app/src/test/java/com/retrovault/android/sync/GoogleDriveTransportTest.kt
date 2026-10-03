package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test
import java.io.File
import java.io.FileNotFoundException
import java.nio.file.Files

/** Drive en memoria: árbol de IDs, sin red. */
private class FakeDriveApi : DriveApi {
    private var next = 0
    val items = LinkedHashMap<String, Pair<String, DriveItem>>() // id -> (parentId, item)
    val contents = HashMap<String, ByteArray>()
    var listCalls = 0

    private fun newId() = "id${next++}"

    override fun listChildren(parentId: String): List<DriveItem> {
        listCalls++
        return items.values.filter { it.first == parentId }.map { it.second }
    }

    override fun createFolder(
        parentId: String,
        name: String,
    ): DriveItem = DriveItem(newId(), name, true, 0L, 0L).also { items[it.id] = parentId to it }

    override fun uploadFile(
        parentId: String,
        existingId: String?,
        name: String,
        file: File,
        modifiedMillis: Long,
    ): DriveItem {
        val id = existingId ?: newId()
        val item = DriveItem(id, name, false, modifiedMillis, file.length())
        items[id] = parentId to item
        contents[id] = file.readBytes()
        return item
    }

    override fun downloadFile(
        fileId: String,
        dest: File,
    ) {
        dest.writeBytes(contents.getValue(fileId))
    }

    fun addFolder(
        parentId: String,
        name: String,
    ) = createFolder(parentId, name)

    fun addFile(
        parentId: String,
        name: String,
        modified: Long,
        data: ByteArray = byteArrayOf(1, 2, 3),
    ): DriveItem =
        DriveItem(newId(), name, false, modified, data.size.toLong()).also {
            items[it.id] = parentId to it
            contents[it.id] = data
        }
}

class GoogleDriveTransportTest {
    private fun tmp(content: ByteArray = byteArrayOf(9, 9)): File =
        Files.createTempFile("drive-test", ".sav").toFile().also {
            it.writeBytes(content)
            it.deleteOnExit()
        }

    @Test
    fun `listing a root that does not exist is empty, not an error`() {
        val transport = GoogleDriveTransport(FakeDriveApi(), "root")
        assertEquals(emptyList<RemoteSave>(), transport.listFolderRecursive("/RetroSync/saves"))
    }

    @Test
    fun `leading RetroSync segment is dropped so Dropbox style paths work`() {
        val transport = GoogleDriveTransport(FakeDriveApi(), "root")
        assertEquals(listOf("saves", "retroarch"), transport.segmentsOf("/RetroSync/saves/retroarch"))
        assertEquals(listOf("saves"), transport.segmentsOf("saves/"))
        assertEquals(listOf("saves", "RetroSync"), transport.segmentsOf("/saves/RetroSync"))
    }

    @Test
    fun `upload creates nested folders and listing returns the relative path with the set mtime`() {
        val api = FakeDriveApi()
        val transport = GoogleDriveTransport(api, "root")

        val saved = transport.upload(tmp(), "/RetroSync/saves", "gba/Pokemon.srm", 1_700_000_000_000L)

        assertEquals("gba/Pokemon.srm", saved.relative)
        assertEquals(1_700_000_000_000L, saved.clientModifiedMillis)
        val listed = transport.listFolderRecursive("/RetroSync/saves")
        assertEquals(listOf("gba/Pokemon.srm"), listed.map { it.relative })
        assertEquals(1_700_000_000_000L, listed.single().clientModifiedMillis)
        assertEquals(2L, listed.single().size)
    }

    @Test
    fun `uploading the same path twice updates the file instead of duplicating it`() {
        val api = FakeDriveApi()
        val transport = GoogleDriveTransport(api, "root")

        val first = transport.upload(tmp(), "/RetroSync/saves", "a.srm", 1_000L)
        val second = transport.upload(tmp(byteArrayOf(1, 2, 3, 4)), "/RetroSync/saves", "a.srm", 2_000L)

        assertEquals(first.rev, second.rev)
        assertEquals(1, api.items.values.count { !it.second.isFolder })
        assertEquals(4L, transport.listFolderRecursive("/RetroSync/saves").single().size)
    }

    @Test
    fun `a second pass reuses cached folder ids instead of listing again`() {
        val api = FakeDriveApi()
        val transport = GoogleDriveTransport(api, "root")
        transport.upload(tmp(), "/RetroSync/saves", "gba/a.srm", 1_000L)
        val before = api.listCalls

        transport.upload(tmp(), "/RetroSync/saves", "gba/a.srm", 2_000L)

        assertEquals(before, api.listCalls)
    }

    @Test
    fun `download writes the content and returns the remote mtime`() {
        val api = FakeDriveApi()
        val saves = api.addFolder("root", "saves")
        api.addFile(saves.id, "x.srm", 5_000L, byteArrayOf(7, 7, 7))
        val dest = File(Files.createTempDirectory("drive-dl").toFile(), "nested/x.srm")

        val mtime = GoogleDriveTransport(api, "root").download("/RetroSync/saves", "x.srm", dest)

        assertEquals(5_000L, mtime)
        assertTrue(dest.readBytes().contentEquals(byteArrayOf(7, 7, 7)))
    }

    @Test
    fun `download of a missing file throws FileNotFoundException`() {
        val transport = GoogleDriveTransport(FakeDriveApi(), "root")
        try {
            transport.download("/RetroSync/saves", "nope.srm", File("unused"))
            fail("esperaba FileNotFoundException")
        } catch (e: FileNotFoundException) {
            assertTrue(e.message!!.contains("nope.srm"))
        }
    }

    @Test
    fun `duplicate names in Drive resolve to the newest one`() {
        val api = FakeDriveApi()
        val saves = api.addFolder("root", "saves")
        api.addFile(saves.id, "dup.srm", 1_000L)
        api.addFile(saves.id, "dup.srm", 9_000L)

        val listed = GoogleDriveTransport(api, "root").listFolderRecursive("/RetroSync/saves")

        assertEquals(1, listed.size)
        assertEquals(9_000L, listed.single().clientModifiedMillis)
    }

    @Test
    fun `listing only returns files under the requested root, with POSIX relative paths`() {
        val api = FakeDriveApi()
        val saves = api.addFolder("root", "saves")
        val other = api.addFolder("root", "states")
        val core = api.addFolder(saves.id, "snes")
        api.addFile(core.id, "e.srm", 1L)
        api.addFile(other.id, "z.state", 1L)

        val listed = GoogleDriveTransport(api, "root").listFolderRecursive("/RetroSync/saves")

        assertEquals(listOf("snes/e.srm"), listed.map { it.relative })
        assertFalse(listed.any { it.relative.contains("z.state") })
    }

    @Test
    fun `drive query values are escaped`() {
        assertEquals("it\\'s", escapeDriveQuery("it's"))
        assertEquals("a\\\\b", escapeDriveQuery("a\\b"))
    }

    @Test
    fun `drive timestamps round trip and bad values give zero`() {
        assertEquals(1_700_000_000_000L, parseDriveTime(formatDriveTime(1_700_000_000_000L)))
        assertEquals(0L, parseDriveTime(null))
        assertEquals(0L, parseDriveTime("no-es-una-fecha"))
    }
}
