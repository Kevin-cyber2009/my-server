package com.example.android_app;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;

import java.util.List;

@Dao
public interface ViolationDao {
    @Insert
    void insert(Violation violation);

    @Query("SELECT * FROM Violation WHERE school_name = :schoolName")
    List<Violation> getAll(String schoolName);

    @Query("DELETE FROM Violation WHERE school_name = :schoolName")
    void deleteAll(String schoolName);
}