package com.example.android_app;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity
public class Violation {
    @PrimaryKey(autoGenerate = true)
    public int id;
    public String student_id;
    public String student_name;  // Thêm
    public String class_name;  // Thêm
    public String dob;  // Thêm
    public String gender;  // Thêm
    public String violation_type;
    public int points_deducted;
    public String violation_date;
    public String school_name;
    public String recorder_name;
    public String recorder_class;

    public Violation(String student_id, String student_name, String class_name, String dob, String gender, String violation_type, int points_deducted, String violation_date, String school_name, String recorder_name, String recorder_class) {
        this.student_id = student_id;
        this.student_name = student_name;
        this.class_name = class_name;
        this.dob = dob;
        this.gender = gender;
        this.violation_type = violation_type;
        this.points_deducted = points_deducted;
        this.violation_date = violation_date;
        this.school_name = school_name;
        this.recorder_name = recorder_name;
        this.recorder_class = recorder_class;
    }
}