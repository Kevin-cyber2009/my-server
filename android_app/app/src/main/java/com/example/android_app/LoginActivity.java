package com.example.android_app;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
import retrofit2.http.Body;
import retrofit2.http.POST;

interface AuthService {
    @POST("/api/login")
    Call<LoginResponse> login(@Body LoginRequest request);
}

class LoginRequest {
    public String username;
    public String password;

    public LoginRequest(String username, String password) {
        this.username = username;
        this.password = password;
    }
}

class LoginResponse {
    public String token;
    public String error;

    public LoginResponse(String token, String error) {
        this.token = token;
        this.error = error;
    }
}

public class LoginActivity extends AppCompatActivity {
    private EditText usernameEdit, passwordEdit;
    private Button loginButton;
    private Retrofit retrofit;
    private AuthService authService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);  // Tạo layout activity_login.xml với EditText và Button

        usernameEdit = findViewById(R.id.username_edit);
        passwordEdit = findViewById(R.id.password_edit);
        loginButton = findViewById(R.id.login_button);

        retrofit = new Retrofit.Builder()
                .baseUrl("https://my-server-fvfu.onrender.com/")
                .addConverterFactory(GsonConverterFactory.create())
                .build();
        authService = retrofit.create(AuthService.class);

        loginButton.setOnClickListener(v -> {
            String username = usernameEdit.getText().toString().trim();
            String password = passwordEdit.getText().toString().trim();
            if (username.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Vui lòng nhập đầy đủ!", Toast.LENGTH_SHORT).show();
                return;
            }
            authService.login(new LoginRequest(username, password)).enqueue(new Callback<LoginResponse>() {
                @Override
                public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                    if (response.isSuccessful() && response.body() != null && response.body().token != null) {
                        // Lưu token
                        SharedPreferences prefs = getSharedPreferences("app_prefs", MODE_PRIVATE);
                        prefs.edit().putString("auth_token", response.body().token).apply();
                        Toast.makeText(LoginActivity.this, "Đăng nhập thành công!", Toast.LENGTH_SHORT).show();
                        startActivity(new Intent(LoginActivity.this, MainActivity.class));
                        finish();
                    } else {
                        Toast.makeText(LoginActivity.this, "Đăng nhập thất bại: " + (response.body() != null ? response.body().error : "Unknown"), Toast.LENGTH_SHORT).show();
                    }
                }

                @Override
                public void onFailure(Call<LoginResponse> call, Throwable t) {
                    Toast.makeText(LoginActivity.this, "Lỗi mạng: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        });
    }
}