package com.retrovault.android.sync

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SyncExclusionsTest {
    @Test
    fun `mirror copies and leftovers at the top level are excluded, any case`() {
        assertTrue(SyncExclusions.isExcluded("retroarch/saves/snes/a.srm"))
        assertTrue(SyncExclusions.isExcluded("RetroArch/saves/a.srm"))
        assertTrue(SyncExclusions.isExcluded("RetroSync/saves/a.srm"))
        assertTrue(SyncExclusions.isExcluded(".stversions/x.srm"))
        assertTrue(SyncExclusions.isExcluded(".stfolder.removed-2025/DO_NOT_DELETE.txt"))
        assertTrue(SyncExclusions.isExcluded("_jubilado_vba_next_20260927/a.srm"))
        assertTrue(SyncExclusions.isExcluded("_descartados/a.srm"))
    }

    @Test
    fun `real core and platform folders are kept`() {
        assertFalse(SyncExclusions.isExcluded("snes/Earthbound.srm"))
        assertFalse(SyncExclusions.isExcluded("Snes9x/Earthbound (1).srm"))
        assertFalse(SyncExclusions.isExcluded("nds/states/x.state"))
        assertFalse(SyncExclusions.isExcluded("loose.sav"))
    }

    @Test
    fun `only the first segment counts, a nested folder with that name is a real one`() {
        assertFalse(SyncExclusions.isExcluded("gba/retroarch/x.sav"))
        assertFalse(SyncExclusions.isExcluded("gba/RetroSync/x.sav"))
    }
}
