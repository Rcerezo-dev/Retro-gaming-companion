package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SaveExtensionsTest {
    @Test
    fun `save extensions match the PC config exactly`() {
        val expected =
            setOf(
                ".sav", ".srm", ".state", ".st0", ".st1", ".st2", ".st3", ".st4", ".st5",
                ".fcs", ".dsv", ".sps", ".psv", ".mcr", ".mem", ".vmp", ".eep", ".fla",
                ".sra", ".sgm", ".brm", ".nv", ".hi", ".state1", ".state2", ".brmc",
                ".ml1", ".mcd", ".ps2", ".gci",
            )
        assertEquals(expected, SaveExtensions.save)
    }

    @Test
    fun `state extensions match the PC config exactly`() {
        val expected =
            setOf(
                ".state", ".state1", ".state2", ".st0", ".st1", ".st2", ".st3", ".st4",
                ".st5", ".ppst", ".fcs", ".sps", ".psv", ".hi", ".brmc", ".ml1",
            )
        assertEquals(expected, SaveExtensions.state)
    }

    @Test
    fun `isTracked is case-insensitive and rejects unknown extensions`() {
        assertTrue(SaveExtensions.isTracked(".sav"))
        assertTrue(SaveExtensions.isTracked(".SAV"))
        assertFalse(SaveExtensions.isTracked(".txt"))
        assertFalse(SaveExtensions.isTracked(""))
    }
}
