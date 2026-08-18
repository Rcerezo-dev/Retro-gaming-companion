package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class DropboxTransportPathsTest {
    @Test
    fun `remotePathFor joins root and relative like rclone_transport rstrip plus slash`() {
        assertEquals("/RetroSync/saves/SNES9x/Game.srm", remotePathFor("/RetroSync/saves", "SNES9x/Game.srm"))
    }

    @Test
    fun `remotePathFor strips a trailing slash on the root`() {
        assertEquals("/RetroSync/saves/Game.srm", remotePathFor("/RetroSync/saves/", "Game.srm"))
    }

    @Test
    fun `relativePathFrom computes the path relative to the root`() {
        assertEquals(
            "SNES9x/Chrono Trigger.srm",
            relativePathFrom("/RetroSync/saves", "/RetroSync/saves/SNES9x/Chrono Trigger.srm"),
        )
    }

    @Test
    fun `relativePathFrom handles a root with a trailing slash`() {
        assertEquals(
            "Game.srm",
            relativePathFrom("/RetroSync/saves/", "/RetroSync/saves/Game.srm"),
        )
    }

    @Test
    fun `relativePathFrom of a file directly in the root has no leading slash`() {
        val relative = relativePathFrom("/RetroSync/saves", "/RetroSync/saves/loose.state")
        assertEquals("loose.state", relative)
        org.junit.Assert.assertFalse(relative.startsWith("/"))
    }
}
