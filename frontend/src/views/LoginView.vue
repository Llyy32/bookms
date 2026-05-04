<!-- ===================== Template 区块 ===================== -->
<!-- 说明：登录/注册页，通过 el-tabs 切换登录与注册表单 -->
<template>
  <div class="login-wrapper">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <div class="login-title">bookMS</div>
          <div class="login-subtitle">图书管理系统</div>
        </div>
      </template>
      <el-tabs v-model="activeTab" stretch>
        <!-- 登录 Tab -->
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @keyup.enter="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                clearable
                autocomplete="username"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
                autocomplete="current-password"
              />
            </el-form-item>
            <el-button
              type="primary"
              :loading="loginLoading"
              class="submit-btn"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <!-- 注册 Tab -->
        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名（4-20个字符）"
                clearable
                autocomplete="username"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码（至少6位）"
                show-password
                autocomplete="new-password"
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
                autocomplete="new-password"
              />
            </el-form-item>
            <el-button
              type="primary"
              :loading="registerLoading"
              class="submit-btn"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含登录与注册两套表单校验、请求与跳转逻辑 -->
<script setup lang="ts">
import { ref, reactive } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import http from "../api/http";

const router = useRouter();
const authStore = useAuthStore();

// 当前激活的 Tab
const activeTab = ref<"login" | "register">("login");

// ---- 登录 ----
const loginFormRef = ref<FormInstance>();
const loginLoading = ref(false);
const loginForm = reactive({ username: "", password: "" });

const loginRules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

async function handleLogin() {
  if (!loginFormRef.value) return;
  const valid = await loginFormRef.value.validate().catch(() => false);
  if (!valid) return;

  loginLoading.value = true;
  try {
    const res = await http.post<{ code: number; message: string; data: any }>(
      "/auth/login",
      { username: loginForm.username, password: loginForm.password }
    );
    if (res.data.code === 0) {
      authStore.setUser({
        id: res.data.data.id,
        username: res.data.data.username,
        role: res.data.data.role,
      });
      router.push("/books");
    } else {
      ElMessage.error(res.data.message || "登录失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "登录失败，请稍后重试");
  } finally {
    loginLoading.value = false;
  }
}

// ---- 注册 ----
const registerFormRef = ref<FormInstance>();
const registerLoading = ref(false);
const registerForm = reactive({
  username: "",
  password: "",
  confirmPassword: "",
});

// 确认密码校验器
function validateConfirm(_rule: any, value: string, callback: any) {
  if (value !== registerForm.password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
}

const registerRules: FormRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 4, max: 20, message: "用户名长度为 4-20 个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少 6 位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: validateConfirm, trigger: "blur" },
  ],
};

async function handleRegister() {
  if (!registerFormRef.value) return;
  const valid = await registerFormRef.value.validate().catch(() => false);
  if (!valid) return;

  registerLoading.value = true;
  try {
    const res = await http.post<{ code: number; message: string; data: any }>(
      "/auth/register",
      { username: registerForm.username, password: registerForm.password }
    );
    if (res.data.code === 0) {
      ElMessage.success("注册成功，请登录");
      // 注册成功后切换到登录 Tab，并预填用户名
      loginForm.username = registerForm.username;
      loginForm.password = "";
      registerForm.username = "";
      registerForm.password = "";
      registerForm.confirmPassword = "";
      registerFormRef.value.resetFields();
      activeTab.value = "login";
    } else {
      ElMessage.error(res.data.message || "注册失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "注册失败，请稍后重试");
  } finally {
    registerLoading.value = false;
  }
}
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.login-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  letter-spacing: 4px;
}

.login-subtitle {
  font-size: 14px;
  color: #909399;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
