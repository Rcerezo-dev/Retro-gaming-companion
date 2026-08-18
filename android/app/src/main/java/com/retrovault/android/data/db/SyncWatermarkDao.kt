package com.retrovault.android.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface SyncWatermarkDao {
    @Query("SELECT lastSyncMillis FROM sync_watermark WHERE relative = :relative AND remoteRoot = :remoteRoot")
    suspend fun getLastSync(
        relative: String,
        remoteRoot: String,
    ): Long?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: SyncWatermarkEntity)

    @Query("DELETE FROM sync_watermark WHERE remoteRoot = :remoteRoot")
    suspend fun clearForRoot(remoteRoot: String)
}
