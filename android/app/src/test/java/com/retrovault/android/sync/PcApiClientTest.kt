package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class PcApiClientTest {
    private fun game(sourcePath: String) =
        RemoteGame(
            id = 1,
            platform = "NES",
            canonicalTitle = "Some Game",
            originalFilename = "Some Game.nes",
            sourcePath = sourcePath,
            sizeBytes = 1024,
        )

    @Test
    fun `extracts platform folder from a Windows-style path`() {
        assertEquals("nes", game("""E:\Carpetas anbernic\nes\Some Game.nes""").platformFolder)
    }

    @Test
    fun `extracts platform folder from a POSIX-style path`() {
        assertEquals("psx", game("/mnt/roms/psx/Some Game.chd").platformFolder)
    }

    @Test
    fun `handles a filename with spaces and parentheses`() {
        assertEquals(
            "megadrive",
            game("""E:\Carpetas anbernic\megadrive\Sonic the Hedgehog (World) (Rev A).md""").platformFolder,
        )
    }
}
