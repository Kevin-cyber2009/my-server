package com.example.android_app;

import androidx.room.Database;
import androidx.room.RoomDatabase;
import androidx.room.migration.Migration;
import androidx.sqlite.db.SupportSQLiteDatabase;

@Database(entities = {Violation.class}, version = 2)
public abstract class AppDatabase extends RoomDatabase {
    public abstract ViolationDao violationDao();

    // Migration từ version 1 lên 2 (thêm columns)
    public static final Migration MIGRATION_1_2 = new Migration(1, 2) {
        @Override
        public void migrate(SupportSQLiteDatabase database) {
            database.execSQL("ALTER TABLE Violation ADD COLUMN student_name TEXT");
            database.execSQL("ALTER TABLE Violation ADD COLUMN class_name TEXT");
            database.execSQL("ALTER TABLE Violation ADD COLUMN dob TEXT");
            database.execSQL("ALTER TABLE Violation ADD COLUMN gender TEXT");
        }
    };
}