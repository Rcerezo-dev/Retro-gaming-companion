package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class SyncResultTest {
    @Test
    fun `plus sums counters and concatenates errors`() {
        val saves = SyncResult(uploaded = 2, downloaded = 1, upToDate = 5, conflicts = 1, errors = listOf("a"))
        val states = SyncResult(uploaded = 0, downloaded = 3, upToDate = 2, conflicts = 0, errors = listOf("b"))

        val merged = saves + states

        assertEquals(2, merged.uploaded)
        assertEquals(4, merged.downloaded)
        assertEquals(7, merged.upToDate)
        assertEquals(1, merged.conflicts)
        assertEquals(listOf("a", "b"), merged.errors)
    }

    @Test
    fun `plus with empty result is identity`() {
        val result = SyncResult(uploaded = 3, downloaded = 1, upToDate = 2)

        assertEquals(result, result + SyncResult())
    }
}
