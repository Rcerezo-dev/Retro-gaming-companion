package com.retrovault.android.util

import org.junit.Assert.assertEquals
import org.junit.Test

class ByteFormatTest {
    @Test
    fun `formats bytes below 1 KB as bytes`() {
        assertEquals("0 B", formatBytes(0))
        assertEquals("1023 B", formatBytes(1023))
    }

    @Test
    fun `formats between 1 KB and 1 MB as kilobytes`() {
        assertEquals("1.0 KB", formatBytes(1024))
        assertEquals("2.5 KB", formatBytes((2.5 * 1024).toLong()))
    }

    @Test
    fun `formats 1 MB and above as megabytes`() {
        assertEquals("1.0 MB", formatBytes(1024L * 1024))
        assertEquals("5.0 MB", formatBytes(5L * 1024 * 1024))
    }
}
