package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RetroArchPathsTest {
    @Test
    fun `arcade folders match platforms toml Arcade keys and have no duplicates`() {
        // Espejo de las claves "Arcade" en src/rom_manager/detection/platforms.toml
        val expected = listOf("mame", "cps1", "cps2", "cps3", "fbneo", "arcade")

        assertEquals(expected, RetroArchPaths.ARCADE_FOLDERS)
        assertEquals(RetroArchPaths.ARCADE_FOLDERS.size, RetroArchPaths.ARCADE_FOLDERS.toSet().size)
    }

    @Test
    fun `arcade folders are distinct from saves and states`() {
        assertTrue(RetroArchPaths.SAVES !in RetroArchPaths.ARCADE_FOLDERS)
        assertTrue(RetroArchPaths.STATES !in RetroArchPaths.ARCADE_FOLDERS)
    }
}
