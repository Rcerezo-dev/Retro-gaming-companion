package com.retrovault.android.data.db

import org.junit.Assert.assertEquals
import org.junit.Test

class SyncHistoryEntityTest {
    private fun entity(
        conflicts: Int = 0,
        errorCount: Int = 0,
        trigger: String = "MANUAL",
    ) = SyncHistoryEntity(
        timestampMillis = 0,
        trigger = trigger,
        uploaded = 1,
        downloaded = 2,
        upToDate = 3,
        conflicts = conflicts,
        errorCount = errorCount,
        errorsText = null,
    )

    @Test
    fun `outcome is ERROR when errorCount is positive, even with conflicts`() {
        assertEquals(SyncOutcome.ERROR, entity(conflicts = 1, errorCount = 1).outcome())
    }

    @Test
    fun `outcome is WARNING when only conflicts are present`() {
        assertEquals(SyncOutcome.WARNING, entity(conflicts = 1).outcome())
    }

    @Test
    fun `outcome is SUCCESS with no conflicts or errors`() {
        assertEquals(SyncOutcome.SUCCESS, entity().outcome())
    }

    @Test
    fun `triggerLabel maps known trigger names to Spanish labels`() {
        assertEquals("Manual", entity(trigger = "MANUAL").triggerLabel())
        assertEquals("Automático", entity(trigger = "PERIODIC").triggerLabel())
        assertEquals("Instantáneo", entity(trigger = "INSTANT").triggerLabel())
    }

    @Test
    fun `summary appends conflicts and errors only when present`() {
        assertEquals("Subidos: 1 · Descargados: 2 · Al día: 3", entity().summary())
        assertEquals(
            "Subidos: 1 · Descargados: 2 · Al día: 3 · Conflictos: 1 · Errores: 2",
            entity(conflicts = 1, errorCount = 2).summary(),
        )
    }
}
