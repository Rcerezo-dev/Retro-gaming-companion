package com.retrovault.android.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

// exportSchema=false: sin historial de migraciones todavía (proyecto v1,
// esquema de una sola tabla) — revisar si hace falta cuando exista una
// primera migración real.
@Database(
    entities = [SyncWatermarkEntity::class, SyncHistoryEntity::class],
    version = 2,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun syncWatermarkDao(): SyncWatermarkDao
    abstract fun syncHistoryDao(): SyncHistoryDao

    companion object {
        // v1 -> v2 (ANDROID-SYNC-14): tabla nueva únicamente — aditiva, no
        // toca sync_watermark, así que no hace falta destructiva ni perder
        // los watermarks ya guardados.
        private val MIGRATION_1_2 =
            object : Migration(1, 2) {
                override fun migrate(db: SupportSQLiteDatabase) {
                    db.execSQL(
                        """
                        CREATE TABLE IF NOT EXISTS sync_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            timestampMillis INTEGER NOT NULL,
                            trigger TEXT NOT NULL,
                            uploaded INTEGER NOT NULL,
                            downloaded INTEGER NOT NULL,
                            upToDate INTEGER NOT NULL,
                            conflicts INTEGER NOT NULL,
                            errorCount INTEGER NOT NULL,
                            errorsText TEXT
                        )
                        """.trimIndent(),
                    )
                }
            }

        @Volatile
        private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room
                    .databaseBuilder(context.applicationContext, AppDatabase::class.java, "retrovault.db")
                    .addMigrations(MIGRATION_1_2)
                    .build()
                    .also { instance = it }
            }
    }
}
