package com.retrovault.android.data.prefs

import org.junit.Assert.assertEquals
import org.junit.Test

class RcloneRemoteTest {
    @Test
    fun `strips an rclone remote prefix pasted from the PC config`() {
        assertEquals("/RetroSync/saves", stripRcloneRemotePrefix("dropbox:/RetroSync/saves"))
    }

    @Test
    fun `leaves a plain Dropbox path untouched`() {
        assertEquals("/RetroSync/saves", stripRcloneRemotePrefix("/RetroSync/saves"))
    }

    @Test
    fun `trims surrounding whitespace`() {
        assertEquals("/RetroSync/saves", stripRcloneRemotePrefix("  dropbox:/RetroSync/saves  "))
    }

    @Test
    fun `only strips up to the first colon`() {
        assertEquals("/x:y", stripRcloneRemotePrefix("dropbox:/x:y"))
    }

    @Test
    fun `empty input stays empty`() {
        assertEquals("", stripRcloneRemotePrefix(""))
    }
}
