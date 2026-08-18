package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

class LocalFileScannerTest {
    @Test
    fun `scan finds tracked extensions recursively and ignores the rest`() {
        val root = Files.createTempDirectory("scanner-test").toFile()
        try {
            File(root, "SNES9x").mkdirs()
            File(root, "SNES9x/Chrono Trigger.srm").writeText("save")
            File(root, "SNES9x/Chrono Trigger.png").writeText("cover art, not a save")
            File(root, "loose.state").writeText("state")
            File(root, "readme.txt").writeText("not tracked")

            val relatives = LocalFileScanner.scan(root).map { it.relative }.toSet()

            assertEquals(setOf("SNES9x/Chrono Trigger.srm", "loose.state"), relatives)
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun `relative path uses forward slashes regardless of OS`() {
        val root = Files.createTempDirectory("scanner-test-2").toFile()
        try {
            File(root, "Core").mkdirs()
            File(root, "Core/Game.sav").writeText("x")

            val result = LocalFileScanner.scan(root).single()

            assertFalse(result.relative.contains('\\'))
            assertEquals("Core/Game.sav", result.relative)
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun `mtime and size are read from the real file`() {
        val root = Files.createTempDirectory("scanner-test-3").toFile()
        try {
            val file = File(root, "Game.srm")
            file.writeText("0123456789")

            val result = LocalFileScanner.scan(root).single()

            assertEquals(10L, result.size)
            assertEquals(file.lastModified(), result.mtimeMillis)
            assertTrue(result.mtimeMillis > 0)
        } finally {
            root.deleteRecursively()
        }
    }

    @Test
    fun `missing root returns empty list instead of throwing`() {
        val parent = Files.createTempDirectory("scanner-test-4").toFile()
        try {
            val missing = File(parent, "does-not-exist")
            assertEquals(emptyList<LocalSave>(), LocalFileScanner.scan(missing))
        } finally {
            parent.deleteRecursively()
        }
    }
}
