<!-- ===================== Template 区块 ===================== -->
<!-- 说明：个人资料页，含基本信息完善、密码修改、我的借阅记录三个区块 -->
<template>
  <div class="profile-page">
    <div class="page-header">
      <span class="page-title">个人资料</span>
    </div>

    <!-- 基本信息 -->
    <el-card class="profile-card">
      <template #header>基本信息</template>
      <el-form
        ref="profileFormRef"
        :model="profileForm"
        label-width="80px"
        style="max-width: 480px"
      >
        <el-form-item label="用户名">
          <el-input :value="authStore.currentUser?.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-input
            :value="authStore.currentUser?.role === 'ADMIN' ? '管理员' : '普通用户'"
            disabled
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="profileForm.real_name" placeholder="请填写真实姓名" clearable />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="profileForm.phone" placeholder="请填写手机号" clearable />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="请填写邮箱" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="profileSaving" @click="saveProfile">
            保存信息
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码 -->
    <el-card class="profile-card">
      <template #header>修改密码</template>
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="80px"
        style="max-width: 480px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="pwdForm.old_password"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="pwdForm.new_password"
            type="password"
            show-password
            placeholder="至少 8 位"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="pwdForm.confirm_password"
            type="password"
            show-password
            placeholder="再次输入新密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="pwdSaving" @click="changePassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 我的借阅 -->
    <el-card class="borrow-card">
      <template #header>
        <div class="borrow-card-header">
          <span>我的借阅</span>
          <router-link to="/borrows" class="view-all-link">查看全部</router-link>
        </div>
      </template>
      <div v-if="borrowLoading" class="borrow-loading">加载中...</div>
      <div v-else-if="borrowRecords.length === 0" class="borrow-empty">暂无借阅记录</div>
      <div v-else class="borrow-list">
        <div v-for="r in borrowRecords" :key="r.id" class="borrow-item">
          <div class="borrow-item-title">{{ r.book_title || "未知书籍" }}</div>
          <div class="borrow-item-meta">
            <span>借阅：{{ r.borrowed_at.slice(0, 10) }}</span>
            <span>应还：{{ r.due_at.slice(0, 10) }}</span>
            <el-tag :type="borrowStatusType(r.status)" size="small">
              {{ borrowStatusLabel(r.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含个人资料加载与更新、密码修改、我的借阅加载逻辑 -->
<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { userApi } from "../api/users";
import { borrowApi } from "../api/borrowRecords";
import type { BorrowRecord } from "../api/borrowRecords";
import http from "../api/http";

const authStore = useAuthStore();

// ——— 基本信息 ———
const profileFormRef = ref<FormInstance>();
const profileSaving = ref(false);

const profileForm = reactive({
  real_name: "",
  phone: "",
  email: "",
});

// 从 /auth/me 加载当前最新资料
async function loadProfile() {
  try {
    const res = await http.get<{ code: number; data: any }>("/auth/me");
    if (res.data.code === 0) {
      const d = res.data.data;
      profileForm.real_name = d.real_name ?? "";
      profileForm.phone = d.phone ?? "";
      profileForm.email = d.email ?? "";
    }
  } catch {
    ElMessage.error("获取资料失败");
  }
}

async function saveProfile() {
  profileSaving.value = true;
  try {
    const res = await userApi.updateProfile({
      real_name: profileForm.real_name || undefined,
      phone: profileForm.phone || undefined,
      email: profileForm.email || undefined,
    });
    if (res.data.code === 0) {
      ElMessage.success("资料已保存");
    } else {
      ElMessage.error(res.data.message || "保存失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "保存失败");
  } finally {
    profileSaving.value = false;
  }
}

// ——— 修改密码 ———
const pwdFormRef = ref<FormInstance>();
const pwdSaving = ref(false);

const pwdForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: "",
});

// 确认密码校验
const validateConfirm = (_: any, value: string, callback: Function) => {
  if (value !== pwdForm.new_password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const pwdRules: FormRules = {
  old_password: [{ required: true, message: "请输入旧密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 8, message: "密码至少 8 位", trigger: "blur" },
  ],
  confirm_password: [
    { required: true, message: "请再次输入新密码", trigger: "blur" },
    { validator: validateConfirm, trigger: "blur" },
  ],
};

async function changePassword() {
  if (!pwdFormRef.value) return;
  const valid = await pwdFormRef.value.validate().catch(() => false);
  if (!valid) return;

  pwdSaving.value = true;
  try {
    const res = await userApi.changePassword(
      pwdForm.old_password,
      pwdForm.new_password
    );
    if (res.data.code === 0) {
      ElMessage.success("密码修改成功，请重新登录");
      pwdForm.old_password = "";
      pwdForm.new_password = "";
      pwdForm.confirm_password = "";
      pwdFormRef.value?.clearValidate();
    } else {
      ElMessage.error(res.data.message || "修改失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "修改失败");
  } finally {
    pwdSaving.value = false;
  }
}

// ——— 我的借阅 ———
const borrowRecords = ref<BorrowRecord[]>([]);
const borrowLoading = ref(false);

async function loadBorrowRecords() {
  borrowLoading.value = true;
  try {
    // 取最近 10 条记录展示在个人资料页
    const res = await borrowApi.list({ page: 1, per_page: 10 });
    if (res.data.code === 0) {
      borrowRecords.value = res.data.data.items;
    }
  } catch {
    // 静默失败，不影响主页面
  } finally {
    borrowLoading.value = false;
  }
}

function borrowStatusLabel(status: string) {
  return { BORROWED: "借阅中", OVERDUE: "逾期", RETURNED: "已归还" }[status] ?? status;
}

function borrowStatusType(status: string) {
  return (
    { BORROWED: "primary", OVERDUE: "danger", RETURNED: "success" }[status] ?? "info"
  );
}

onMounted(loadProfile);
onMounted(loadBorrowRecords);
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.profile-card {
  max-width: 600px;
}

.borrow-card {
  max-width: 600px;
}

.borrow-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.view-all-link {
  font-size: 13px;
  color: #409eff;
  text-decoration: none;
}

.view-all-link:hover {
  text-decoration: underline;
}

.borrow-loading,
.borrow-empty {
  color: #909399;
  font-size: 14px;
  padding: 12px 0;
}

.borrow-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.borrow-item {
  padding: 10px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
}

.borrow-item-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 6px;
}

.borrow-item-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}
</style>
