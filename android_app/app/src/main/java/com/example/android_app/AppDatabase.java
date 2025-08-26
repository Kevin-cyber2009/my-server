package com.example.android_app;

import androidx.room.Database;
import androidx.room.RoomDatabase;

@Database(entities = {Violation.class}, version = 1)
public abstract class AppDatabase extends RoomDatabase {
    public abstract ViolationDao violationDao();
}