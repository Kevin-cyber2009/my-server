package com.example.android_app;

import androidx.room.Database;
import androidx.room.RoomDatabase;
import androidx.room.migration.Migration;
import androidx.sqlite.db.SupportSQLiteDatabase;

@Database(entities = {Violation.class}, version = 2, exportSchema = false)
public abstract class AppDatabase extends RoomDatabase {
    public abstract ViolationDao violationDao();

    public static final Migration MIGRATION_1_2 = new Migration(1, 2) {
        @Override
        public void migrate(SupportSQLiteDatabase database) {
            // Tạo table nếu chưa tồn tại (dùng 'Violation' match class name, hoặc 'violations' nếu @Entity định nghĩa lowercase)
            database.execSQL("CREATE TABLE IF NOT EXISTS Violation (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                    "student_id TEXT, " +
                    "violation_type TEXT, " +
                    "points_deducted INTEGER NOT NULL, " +
                    "violation_date TEXT, " +
                    "school_name TEXT, " +
                    "recorder_name TEXT, " +
                    "recorder_class TEXT, " +
                    "student_name TEXT, " +  // Thêm cột mới ngay từ create
                    "class_name TEXT, " +
                    "dob TEXT, " +
                    "gender TEXT" +
                    ")");

            // Nếu table đã tồn tại, thêm columns (sử dụng TRY-CATCH nếu cần, nhưng Room execSQL không throw nếu column tồn tại)
            try {
                database.execSQL("ALTER TABLE Violation ADD COLUMN student_name TEXT DEFAULT ''");
                database.execSQL("ALTER TABLE Violation ADD COLUMN class_name TEXT DEFAULT ''");
                database.execSQL("ALTER TABLE Violation ADD COLUMN dob TEXT DEFAULT ''");
                database.execSQL("ALTER TABLE Violation ADD COLUMN gender TEXT DEFAULT ''");
            } catch (Exception e) {
                // Bỏ qua nếu column đã tồn tại
            }
        }
    };
}