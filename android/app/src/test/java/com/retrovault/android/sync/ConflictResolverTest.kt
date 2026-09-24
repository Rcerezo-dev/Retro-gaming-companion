package com.retrovault.android.sync

import org.junit.Assert.assertEquals
import org.junit.Test

class ConflictResolverTest {
    @Test
    fun `both sides absent is up to date`() {
        assertEquals(SyncAction.UP_TO_DATE, ConflictResolver.decide("x.sav", null, null, null).action)
    }

    @Test
    fun `local only is a trivial upload`() {
        assertEquals(SyncAction.UPLOAD, ConflictResolver.decide("x.sav", 1_000L, null, null).action)
    }

    @Test
    fun `remote only is a trivial download`() {
        assertEquals(SyncAction.DOWNLOAD, ConflictResolver.decide("x.sav", null, 1_000L, null).action)
    }

    @Test
    fun `mtimes within tolerance are up to date`() {
        assertEquals(SyncAction.UP_TO_DATE, ConflictResolver.decide("x.sav", 10_000L, 11_000L, null).action)
    }

    @Test
    fun `local newer beyond tolerance uploads`() {
        assertEquals(SyncAction.UPLOAD, ConflictResolver.decide("x.sav", 20_000L, 10_000L, null).action)
    }

    @Test
    fun `remote newer beyond tolerance downloads`() {
        assertEquals(SyncAction.DOWNLOAD, ConflictResolver.decide("x.sav", 10_000L, 20_000L, null).action)
    }

    @Test
    fun `both sides changed since last sync is a conflict`() {
        val lastSync = 10_000L
        assertEquals(SyncAction.CONFLICT, ConflictResolver.decide("x.sav", 20_000L, 30_000L, lastSync).action)
    }

    @Test
    fun `only local changed since last sync uploads, not a conflict`() {
        val lastSync = 10_000L
        // remoto a 500ms de last_sync (dentro de tolerancia) = "sin cambios"
        assertEquals(SyncAction.UPLOAD, ConflictResolver.decide("x.sav", 20_000L, 10_500L, lastSync).action)
    }

    @Test
    fun `only remote changed since last sync downloads, not a conflict`() {
        val lastSync = 10_000L
        assertEquals(SyncAction.DOWNLOAD, ConflictResolver.decide("x.sav", 10_500L, 20_000L, lastSync).action)
    }

    @Test
    fun `tolerance boundary is inclusive`() {
        // diff exacto = 2000ms (tolerancia por defecto) -> up_to_date, no upload
        assertEquals(SyncAction.UP_TO_DATE, ConflictResolver.decide("x.sav", 12_000L, 10_000L, null).action)
    }

    @Test
    fun `just past the tolerance boundary is not up to date`() {
        assertEquals(SyncAction.UPLOAD, ConflictResolver.decide("x.sav", 12_001L, 10_000L, null).action)
    }

    @Test
    fun `custom tolerance is respected`() {
        assertEquals(
            SyncAction.UPLOAD,
            ConflictResolver.decide("x.sav", 10_500L, 10_000L, null, toleranceMillis = 100L).action,
        )
    }

    @Test
    fun `decision carries the original mtimes through`() {
        val decision = ConflictResolver.decide("x.sav", 20_000L, 10_000L, null)
        assertEquals(20_000L, decision.localMtimeMillis)
        assertEquals(10_000L, decision.remoteMtimeMillis)
        assertEquals("x.sav", decision.relative)
    }
}
