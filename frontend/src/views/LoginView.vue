<!-- ===================== Template 区块 ===================== -->
<!-- 说明：登录页，包含用户名/密码表单、校验规则与提交逻辑 -->
<template>
  <div class="login-wrapper">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <div class="login-title">bookMS</div>
          <div class="login-subtitle">图书管理系统</div>
        </div>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            clearable
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含表单校验、登录请求与成功后跳转逻辑 -->
<script setup lang="ts">
import { ref, reactive } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import http from "../api/http";

const router = useRouter();
const authStore = useAuthStore();

const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive({ username: "", password: "" });

const rules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

async function handleLogin() {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const res = await http.post<{ code: number; message: string; data: any }>(
      "/auth/login",
      { username: form.username, password: form.password }
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
    loading.value = false;
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

.login-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
