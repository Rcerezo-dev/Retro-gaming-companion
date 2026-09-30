package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File
import java.nio.file.Files

class SaveFileObserverManagerTest {
    @Test
    fun `collectWatchDirs includes root and every existing subdirectory`() {
        val root = Files.createTempDirectory("save-observer-test").toFile()
        try {
            File(root, "snes9x").mkdirs()
            File(root, "mgba/nested").mkdirs()
            File(root, "snes9x/ignored.srm").writeText("not a dir")

            val dirs = collectWatchDirs(root).map { it.path }.toSet()

            val expected = setOf(root, File(root, "snes9x"), File(root, "mgba"), File(root, "mgba/nested")).map { it.path }.toSet()
            assertEquals(expected, dirs)
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun `collectWatchDirs on a non-existent path returns empty`() {
        assertEquals(emptyList<File>(), collectWatchDirs(File("/does/not/exist")))
    }
}
