package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class DeviceProfileRestoreTest {
    @Test
    fun `remoteBaseFrom drops the last path segment, same criterion as the PC side`() {
        assertEquals(
            "/RetroSync/saves/retroarch",
            DeviceProfileRestore.remoteBaseFrom("/RetroSync/saves/retroarch/saves"),
        )
    }

    @Test
    fun `remoteBaseFrom tolerates a trailing slash`() {
        assertEquals(
            "/RetroSync/saves/retroarch",
            DeviceProfileRestore.remoteBaseFrom("/RetroSync/saves/retroarch/saves/"),
        )
    }

    @Test
    fun `remoteBaseFrom with no slash returns the value unchanged`() {
        assertEquals("saves", DeviceProfileRestore.remoteBaseFrom("saves"))
    }

    @Test
    fun `parseManifest reads name, remote and single_file from each entry`() {
        val json =
            """
            [
              {"name": "RetroArch Autoconfig (mandos)", "local_dir": "{SYSTEM}/../autoconfig", "remote": "/RetroSync/saves/retroarch/autoconfig", "sync_all": true, "single_file": false},
              {"name": "RetroArch Recientes", "local_dir": "{SYSTEM}/../playlists/content_history.lpl", "remote": "/RetroSync/saves/retroarch/content_history.lpl", "sync_all": true, "single_file": true},
              {"name": "Base de datos PC (library_pc.db)", "local_dir": "{PROJECT_ROOT}/.rommgr/library_pc.db", "remote": "/RetroSync/saves/retroarch/library_pc.db", "sync_all": true, "single_file": true}
            ]
            """.trimIndent()

        val entries = DeviceProfileRestore.parseManifest(json)

        assertEquals(3, entries.size)
        assertEquals("RetroArch Autoconfig (mandos)", entries[0].name)
        assertEquals("/RetroSync/saves/retroarch/autoconfig", entries[0].remote)
        assertEquals(false, entries[0].singleFile)
        assertEquals(true, entries[1].singleFile)
        assertEquals("Base de datos PC (library_pc.db)", entries[2].name)
    }

    @Test
    fun `parseManifest defaults single_file to false when the key is missing`() {
        val json = """[{"name": "x", "remote": "/RetroSync/x"}]"""
        val entries = DeviceProfileRestore.parseManifest(json)
        assertEquals(false, entries[0].singleFile)
    }
}
