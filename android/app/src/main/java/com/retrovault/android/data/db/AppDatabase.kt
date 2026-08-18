package com.retrovault.android.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

// exportSchema=false: sin historial de migraciones todavía (proyecto v1,
// esquema de una sola tabla) — revisar si hace falta cuando exista una
// primera migración real.
@Database(entities = [SyncWatermarkEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun syncWatermarkDao(): SyncWatermarkDao

    companion object {
        @Volatile
        private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room
                    .databaseBuilder(context.applicationContext, AppDatabase::class.java, "retrovault.db")
                    .build()
                    .also { instance = it }
            }
    }
}
