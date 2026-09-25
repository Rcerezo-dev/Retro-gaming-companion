package com.retrovault.android.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface SyncHistoryDao {
    @Insert
    suspend fun insert(entity: SyncHistoryEntity)

    @Query("SELECT * FROM sync_history ORDER BY timestampMillis DESC LIMIT :limit")
    fun recent(limit: Int = 10): Flow<List<SyncHistoryEntity>>
}
