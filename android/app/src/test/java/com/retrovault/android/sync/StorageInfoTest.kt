package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StorageInfoTest {
    private val mib = 1024L * 1024
    private val gib = mib * 1024

    @Test
    fun `bytes are formatted with a Spanish decimal comma`() {
        assertEquals("540 MB", formatBytes(540 * mib))
        assertEquals("2,25 GB", formatBytes(gib * 9 / 4))
        assertEquals("12 KB", formatBytes(12 * 1024L))
    }

    @Test
    fun `a library under 2 GB shows no hint`() {
        val info = storageInfo(540 * mib, dropboxUsed = 1 * gib, dropboxTotal = 2 * gib)
        assertNull(info.hint)
        assertTrue(info.summary.contains("Biblioteca de saves: 540 MB"))
        assertTrue(info.summary.contains("Dropbox: 1,00 GB usados de 2,00 GB"))
    }

    @Test
    fun `a library over 2 GB points the user to Google Drive`() {
        val hint = storageInfo(3 * gib, null, null).hint
        assertNotNull(hint)
        assertTrue(hint!!.contains("Google Drive"))
    }

    @Test
    fun `exactly 2 GB still fits, no hint`() {
        assertNull(storageInfo(DROPBOX_FREE_BYTES, null, null).hint)
    }

    @Test
    fun `without Dropbox quota only the library line is shown`() {
        assertEquals("Biblioteca de saves: 540 MB", storageInfo(540 * mib, null, null).summary)
    }
}
