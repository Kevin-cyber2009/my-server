package com.example.android_app;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.room.Room;

import com.google.android.material.button.MaterialButton;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.textfield.TextInputEditText;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

import org.json.JSONException;
import org.json.JSONObject;

import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Path;

// Retrofit API
interface ApiService {
    @GET("/api/schools")
    Call<List<String>> getSchools();

    @GET("/api/violation_types/{school_name}")
    Call<List<ViolationType>> getViolationTypes(@Path("school_name") String schoolName);

    @POST("/api/sync/db")
    Call<SyncResponse> syncViolations(@Body SyncData data);
}

class ViolationType {
    public String name;
    public int points;

    public ViolationType(String name, int points) {
        this.name = name;
        this.points = points;
    }
}

class SyncData {
    public List<Violation> violations;

    public SyncData(List<Violation> violations) {
        this.violations = violations;
    }
}

class SyncResponse {
    public String message;

    public SyncResponse(String message) {
        this.message = message;
    }
}

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    private Retrofit retrofit;
    private ApiService apiService;
    private AppDatabase db;
    private Spinner schoolSpinner;
    private Spinner violationSpinner;
    private TextView studentInfoText;
    private TextInputEditText nameEditText;
    private TextInputEditText classEditText;
    private TextInputEditText manualFullName;
    private TextInputEditText manualClassName;
    private TextInputEditText manualDob;
    private TextInputEditText manualGender;
    private MaterialButton scanButton;
    private MaterialButton manualInputButton;
    private MaterialButton confirmButton;
    private MaterialButton manualConfirmButton;
    private MaterialCardView violationCard;
    private MaterialCardView manualInputCard;
    private String currentStudentId;
    private ExecutorService executor = Executors.newSingleThreadExecutor();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Khởi tạo Room DB
        db = Room.databaseBuilder(getApplicationContext(), AppDatabase.class, "app_database")
                .build();

        // Khởi tạo Retrofit
        retrofit = new Retrofit.Builder()
                .baseUrl("https://your-render.onrender.com/") // Thay bằng URL Render thực tế
                .addConverterFactory(GsonConverterFactory.create())
                .build();
        apiService = retrofit.create(ApiService.class);

        // Khởi tạo UI
        schoolSpinner = findViewById(R.id.school_spinner);
        violationSpinner = findViewById(R.id.violation_spinner);
        studentInfoText = findViewById(R.id.student_info_text);
        nameEditText = findViewById(R.id.name_edit_text);
        classEditText = findViewById(R.id.class_edit_text);
        manualFullName = findViewById(R.id.manual_full_name);
        manualClassName = findViewById(R.id.manual_class_name);
        manualDob = findViewById(R.id.manual_dob);
        manualGender = findViewById(R.id.manual_gender);
        scanButton = findViewById(R.id.scan_button);
        manualInputButton = findViewById(R.id.manual_input_button);
        confirmButton = findViewById(R.id.confirm_button);
        manualConfirmButton = findViewById(R.id.manual_confirm_button);
        violationCard = findViewById(R.id.violation_card);
        manualInputCard = findViewById(R.id.manual_input_card);

        // Ẩn card ban đầu
        violationCard.setVisibility(View.GONE);
        manualInputCard.setVisibility(View.GONE);

        // Load danh sách trường
        loadSchools();

        // Sự kiện chọn trường
        schoolSpinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                String schoolName = parent.getItemAtPosition(position).toString();
                loadViolationTypes(schoolName);
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {}
        });

        // Nút quét QR
        scanButton.setOnClickListener(v -> {
            IntentIntegrator integrator = new IntentIntegrator(this);
            integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE);
            integrator.setPrompt("Quét QR học sinh");
            integrator.initiateScan();
        });

        // Nút nhập tay
        manualInputButton.setOnClickListener(v -> {
            manualInputCard.setVisibility(View.VISIBLE);
            AlphaAnimation fadeIn = new AlphaAnimation(0.0f, 1.0f);
            fadeIn.setDuration(500);
            manualInputCard.startAnimation(fadeIn);
        });

        // Nút xác nhận nhập tay
        manualConfirmButton.setOnClickListener(v -> {
            String fullName = manualFullName.getText().toString().trim();
            String className = manualClassName.getText().toString().trim();
            String dob = manualDob.getText().toString().trim();
            String gender = manualGender.getText().toString().trim();

            if (fullName.isEmpty() || className.isEmpty() || dob.isEmpty() || gender.isEmpty()) {
                Toast.makeText(this, "Vui lòng nhập đầy đủ thông tin!", Toast.LENGTH_SHORT).show();
                return;
            }

            String schoolName = schoolSpinner.getSelectedItem() != null ? schoolSpinner.getSelectedItem().toString() : "";
            currentStudentId = schoolName + "_" + fullName.hashCode();
            studentInfoText.setText("Học sinh: " + fullName + ", Lớp: " + className + ", Ngày sinh: " + dob + ", Giới tính: " + gender);

            AlphaAnimation fadeOut = new AlphaAnimation(1.0f, 0.0f);
            fadeOut.setDuration(500);
            fadeOut.setAnimationListener(new Animation.AnimationListener() {
                @Override
                public void onAnimationEnd(Animation animation) {
                    manualInputCard.setVisibility(View.GONE);
                    violationCard.setVisibility(View.VISIBLE);
                    AlphaAnimation fadeIn = new AlphaAnimation(0.0f, 1.0f);
                    fadeIn.setDuration(500);
                    violationCard.startAnimation(fadeIn);
                }
                @Override
                public void onAnimationStart(Animation animation) {}
                @Override
                public void onAnimationRepeat(Animation animation) {}
            });
            manualInputCard.startAnimation(fadeOut);
        });

        // Nút xác nhận vi phạm
        confirmButton.setOnClickListener(v -> saveViolation());
    }

    private void loadSchools() {
        apiService.getSchools().enqueue(new Callback<List<String>>() {
            @Override
            public void onResponse(Call<List<String>> call, Response<List<String>> response) {
                if (response.isSuccessful() && response.body() != null && !response.body().isEmpty()) {
                    List<String> schools = response.body();
                    ArrayAdapter<String> adapter = new ArrayAdapter<>(MainActivity.this,
                            android.R.layout.simple_spinner_dropdown_item, schools);
                    schoolSpinner.setAdapter(adapter);
                    if (!schools.isEmpty()) {
                        loadViolationTypes(schools.get(0));
                    }
                } else {
                    Toast.makeText(MainActivity.this, "Lỗi tải danh sách trường", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<String>> call, Throwable t) {
                Log.e(TAG, "Lỗi mạng loadSchools: " + t.getMessage());
                Toast.makeText(MainActivity.this, "Lỗi mạng: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void loadViolationTypes(String schoolName) {
        apiService.getViolationTypes(schoolName).enqueue(new Callback<List<ViolationType>>() {
            @Override
            public void onResponse(Call<List<ViolationType>> call, Response<List<ViolationType>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<ViolationType> violations = response.body();
                    List<String> violationNames = new ArrayList<>();
                    for (ViolationType v : violations) {
                        violationNames.add(v.name + " (-" + v.points + ")");
                    }
                    ArrayAdapter<String> adapter = new ArrayAdapter<>(MainActivity.this,
                            android.R.layout.simple_spinner_dropdown_item, violationNames);
                    violationSpinner.setAdapter(adapter);
                } else {
                    Toast.makeText(MainActivity.this, "Lỗi tải nội quy", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<ViolationType>> call, Throwable t) {
                Log.e(TAG, "Lỗi mạng loadViolationTypes: " + t.getMessage());
                Toast.makeText(MainActivity.this, "Lỗi mạng: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        IntentResult result = IntentIntegrator.parseActivityResult(requestCode, resultCode, data);
        if (result != null && result.getContents() != null) {
            String qrData = result.getContents();
            Log.d(TAG, "Raw QR Data: " + qrData);
            try {
                JSONObject json = new JSONObject(qrData);
                JSONObject dataJson = json.has("data") ? json.getJSONObject("data") : json;
                String fullName = dataJson.optString("full_name", "Unknown");
                String className = dataJson.optString("class_name", "Unknown");
                String dob = dataJson.optString("dob", "2000-01-01");
                String gender = dataJson.optString("gender", "Unknown");
                String hash = json.optString("hash", "");

                String schoolName = schoolSpinner.getSelectedItem() != null ? schoolSpinner.getSelectedItem().toString() : "";
                String dataStr = dataJson.toString();
                String expectedHash = getSha256(dataStr + schoolName).substring(0, 16);
                if (!hash.isEmpty() && !hash.equals(expectedHash)) {
                    Toast.makeText(this, "QR không hợp lệ!", Toast.LENGTH_SHORT).show();
                    return;
                }

                currentStudentId = schoolName + "_" + fullName.hashCode();
                studentInfoText.setText("Học sinh: " + fullName + ", Lớp: " + className + ", Ngày sinh: " + dob + ", Giới tính: " + gender);
                violationCard.setVisibility(View.VISIBLE);
                AlphaAnimation fadeIn = new AlphaAnimation(0.0f, 1.0f);
                fadeIn.setDuration(500);
                violationCard.startAnimation(fadeIn);
            } catch (JSONException e) {
                Log.e(TAG, "JSON Parse Error: " + e.getMessage());
                Toast.makeText(this, "Lỗi đọc QR: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            }
        } else {
            Toast.makeText(this, "Không đọc được QR", Toast.LENGTH_SHORT).show();
        }
    }

    private void saveViolation() {
        String schoolName = schoolSpinner.getSelectedItem() != null ? schoolSpinner.getSelectedItem().toString() : "";
        String violationItem = violationSpinner.getSelectedItem() != null ? violationSpinner.getSelectedItem().toString() : "";
        String recorderName = nameEditText.getText().toString().trim();
        String recorderClass = classEditText.getText().toString().trim();

        if (schoolName.isEmpty() || violationItem.isEmpty() || recorderName.isEmpty() || recorderClass.isEmpty() || currentStudentId == null) {
            Toast.makeText(this, "Vui lòng nhập đầy đủ thông tin và quét/nhập QR!", Toast.LENGTH_SHORT).show();
            return;
        }

        String violationType = violationItem.substring(0, violationItem.indexOf(" (-"));
        int points = Integer.parseInt(violationItem.substring(violationItem.indexOf("(-") + 2, violationItem.indexOf(")")));
        String date = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date());
        Violation violation = new Violation(currentStudentId, violationType, points, date, schoolName, recorderName, recorderClass);

        executor.execute(() -> {
            db.violationDao().insert(violation);
            syncViolations(schoolName);
            runOnUiThread(() -> {
                Toast.makeText(MainActivity.this, "Đã lưu vi phạm!", Toast.LENGTH_SHORT).show();
                AlphaAnimation fadeOut = new AlphaAnimation(1.0f, 0.0f);
                fadeOut.setDuration(500);
                fadeOut.setAnimationListener(new Animation.AnimationListener() {
                    @Override
                    public void onAnimationEnd(Animation animation) {
                        violationCard.setVisibility(View.GONE);
                        studentInfoText.setText("Thông tin học sinh: Chưa quét QR");
                        currentStudentId = null;
                    }
                    @Override
                    public void onAnimationStart(Animation animation) {}
                    @Override
                    public void onAnimationRepeat(Animation animation) {}
                });
                violationCard.startAnimation(fadeOut);
            });
        });
    }

    private void syncViolations(String schoolName) {
        executor.execute(() -> {
            List<Violation> violations = db.violationDao().getAll(schoolName);
            if (!violations.isEmpty()) {
                apiService.syncViolations(new SyncData(violations)).enqueue(new Callback<SyncResponse>() {
                    @Override
                    public void onResponse(Call<SyncResponse> call, Response<SyncResponse> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            executor.execute(() -> db.violationDao().deleteAll(schoolName));
                            runOnUiThread(() -> Toast.makeText(MainActivity.this, "Đồng bộ thành công!", Toast.LENGTH_SHORT).show());
                        } else {
                            runOnUiThread(() -> Toast.makeText(MainActivity.this, "Lỗi đồng bộ: " + response.code(), Toast.LENGTH_SHORT).show());
                        }
                    }

                    @Override
                    public void onFailure(Call<SyncResponse> call, Throwable t) {
                        Log.e(TAG, "Lỗi đồng bộ: " + t.getMessage());
                        runOnUiThread(() -> Toast.makeText(MainActivity.this, "Lỗi đồng bộ: " + t.getMessage(), Toast.LENGTH_SHORT).show());
                    }
                });
            }
        });
    }

    private String getSha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes("UTF-8"));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            Log.e(TAG, "SHA-256 Error: " + e.getMessage());
            return "";
        }
    }
}