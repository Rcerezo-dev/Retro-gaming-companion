package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class RemoteRouterTest {
    @Test
    fun `extensions shared by both lists route to states, not saves`() {
        // Espejo de rclone_transport.py::_resolve_remote(): state_extensions
        // se comprueba antes que save_extensions.
        for (ext in listOf(".state", ".fcs", ".sps", ".psv", ".hi", ".brmc", ".ml1")) {
            assertEquals("$ext debe ir a STATES", RemoteCategory.STATES, RemoteRouter.categorize(ext))
        }
    }

    @Test
    fun `save-only extensions route to saves`() {
        for (ext in
            listOf(
                ".sav", ".srm", ".mcr", ".mem", ".vmp", ".eep", ".fla",
                ".sra", ".sgm", ".brm", ".nv", ".mcd", ".ps2", ".gci",
            )
        ) {
            assertEquals("$ext debe ir a SAVES", RemoteCategory.SAVES, RemoteRouter.categorize(ext))
        }
    }

    @Test
    fun `state-only extension routes to states`() {
        assertEquals(RemoteCategory.STATES, RemoteRouter.categorize(".ppst"))
    }

    @Test
    fun `unknown extensions are unrouted`() {
        assertEquals(RemoteCategory.UNKNOWN, RemoteRouter.categorize(".txt"))
        assertEquals(RemoteCategory.UNKNOWN, RemoteRouter.categorize(""))
    }

    @Test
    fun `matching is case-insensitive`() {
        assertEquals(RemoteCategory.SAVES, RemoteRouter.categorize(".SRM"))
        assertEquals(RemoteCategory.STATES, RemoteRouter.categorize(".STATE"))
    }
}
