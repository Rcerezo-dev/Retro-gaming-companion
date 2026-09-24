package com.retrovault.android.permissions

import android.os.Build
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StoragePermissionPolicyTest {
    @Test
    fun `needsManageExternalStorage is true from API 30 up`() {
        assertFalse(StoragePermissionPolicy.needsManageExternalStorage(Build.VERSION_CODES.Q)) // 29
        assertTrue(StoragePermissionPolicy.needsManageExternalStorage(Build.VERSION_CODES.R)) // 30
        assertTrue(StoragePermissionPolicy.needsManageExternalStorage(34))
    }

    @Test
    fun `needsLegacyStoragePermission is true only below API 30`() {
        assertTrue(StoragePermissionPolicy.needsLegacyStoragePermission(26))
        assertTrue(StoragePermissionPolicy.needsLegacyStoragePermission(Build.VERSION_CODES.Q)) // 29
        assertFalse(StoragePermissionPolicy.needsLegacyStoragePermission(Build.VERSION_CODES.R)) // 30
    }

    @Test
    fun `needsManageExternalStorage and needsLegacyStoragePermission are mutually exclusive`() {
        for (sdkInt in 26..35) {
            val needsManage = StoragePermissionPolicy.needsManageExternalStorage(sdkInt)
            val needsLegacy = StoragePermissionPolicy.needsLegacyStoragePermission(sdkInt)
            assertTrue(
                "sdkInt=$sdkInt debe tomar exactamente una rama de storage",
                needsManage != needsLegacy,
            )
        }
    }

    @Test
    fun `needsNotificationPermission is true only from API 33 up`() {
        assertFalse(StoragePermissionPolicy.needsNotificationPermission(32))
        assertTrue(StoragePermissionPolicy.needsNotificationPermission(Build.VERSION_CODES.TIRAMISU)) // 33
        assertTrue(StoragePermissionPolicy.needsNotificationPermission(34))
    }
}
