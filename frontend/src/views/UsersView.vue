<!-- ===================== Template 区块 ===================== -->
<!-- 说明：管理员用户管理页，包含搜索筛选、用户表格、新增/编辑/状态操作 -->
<template>
  <div class="users-page">
    <div class="page-header">
      <span class="page-title">用户管理</span>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="query" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            placeholder="用户名 / 姓名"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="query.role" placeholder="全部" clearable style="width: 120px">
            <el-option label="管理员" value="ADMIN" />
            <el-option label="普通用户" value="USER" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 100px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <div class="action-bar">
      <span class="total-hint">共 {{ total }} 条</span>
      <el-button type="primary" @click="openAddDialog">+ 新增用户</el-button>
    </div>

    <!-- 数据表格 -->
    <el-card>
      <el-table :data="users" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="140" show-overflow-tooltip />
        <el-table-column label="姓名" width="110">
          <template #default="{ row }">{{ row.real_name || "-" }}</template>
        </el-table-column>
        <el-table-column label="手机号" width="130">
          <template #default="{ row }">{{ row.phone || "-" }}</template>
        </el-table-column>
        <el-table-column label="邮箱" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.email || "-" }}</template>
        </el-table-column>
        <el-table-column label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'ADMIN' ? 'danger' : 'info'" size="small">
              {{ row.role === "ADMIN" ? "管理员" : "普通用户" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="170">
          <template #default="{ row }">
            {{ row.created_at.replace("T", " ").slice(0, 19) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)">
              编辑
            </el-button>
            <!-- 不能操作当前登录的管理员自身 -->
            <template v-if="row.id !== currentUserId">
              <el-popconfirm
                v-if="row.status === 1"
                :title="`确认禁用用户「${row.username}」？`"
                confirm-button-text="确认"
                cancel-button-text="取消"
                @confirm="handleToggleStatus(row, 0)"
              >
                <template #reference>
                  <el-button link type="danger" size="small">禁用</el-button>
                </template>
              </el-popconfirm>
              <el-popconfirm
                v-else
                :title="`确认启用用户「${row.username}」？`"
                confirm-button-text="确认"
                cancel-button-text="取消"
                @confirm="handleToggleStatus(row, 1)"
              >
                <template #reference>
                  <el-button link type="success" size="small">启用</el-button>
                </template>
              </el-popconfirm>
            </template>
            <span v-else class="self-tag">（自己）</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.per_page"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 新增 / 编辑 对话框 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.mode === 'add' ? '新增用户' : '编辑用户'"
      width="480px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <!-- 用户名只在新增时可填 -->
        <el-form-item v-if="dialog.mode === 'add'" label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3-64位，字母/数字/下划线" />
        </el-form-item>
        <el-form-item v-if="dialog.mode === 'add'" label="初始密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="至少 8 位"
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.real_name" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="普通用户" value="USER" />
            <!-- 编辑时如果是自己则不能改角色 -->
            <el-option
              label="管理员"
              value="ADMIN"
              :disabled="dialog.mode === 'edit' && editingId === currentUserId"
            />
          </el-select>
        </el-form-item>
        <!-- 编辑时可选择重置密码 -->
        <template v-if="dialog.mode === 'edit'">
          <el-form-item label="">
            <el-checkbox v-model="resetPassword">重置密码</el-checkbox>
          </el-form-item>
          <el-form-item v-if="resetPassword" label="新密码" prop="newPassword">
            <el-input
              v-model="form.newPassword"
              type="password"
              show-password
              placeholder="至少 8 位"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含用户列表加载、新增/编辑/禁用/启用等逻辑 -->
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { userApi } from "../api/users";
import type { User } from "../api/users";

const authStore = useAuthStore();

// 当前登录管理员 id（通过 authStore 存 id）
const currentUserId = computed(() => authStore.currentUser?.id ?? -1);

// 列表状态
const users = ref<User[]>([]);
const total = ref(0);
const loading = ref(false);

// 查询条件
const query = reactive({
  keyword: "",
  role: "" as string,
  status: "" as number | string,
  page: 1,
  per_page: 20,
});

async function loadUsers() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: query.page,
      per_page: query.per_page,
    };
    if (query.keyword) params.keyword = query.keyword;
    if (query.role) params.role = query.role;
    if (query.status !== "") params.status = query.status;

    const res = await userApi.list(params);
    if (res.data.code === 0) {
      users.value = res.data.data.items;
      total.value = res.data.data.total;
    }
  } catch {
    ElMessage.error("加载用户列表失败");
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  query.page = 1;
  loadUsers();
}

function handleReset() {
  query.keyword = "";
  query.role = "";
  query.status = "";
  query.page = 1;
  loadUsers();
}

// ——— 新增 / 编辑 对话框 ———
const formRef = ref<FormInstance>();
const submitting = ref(false);
const dialog = reactive({ visible: false, mode: "add" as "add" | "edit" });
let editingId: number | null = null;
const resetPassword = ref(false);

const form = reactive({
  username: "",
  password: "",
  real_name: "",
  phone: "",
  email: "",
  role: "USER" as "ADMIN" | "USER",
  newPassword: "",
});

const formRules = computed<FormRules>(() => ({
  username:
    dialog.mode === "add"
      ? [{ required: true, message: "用户名不能为空", trigger: "blur" }]
      : [],
  password:
    dialog.mode === "add"
      ? [{ required: true, message: "初始密码不能为空", trigger: "blur" }]
      : [],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
  newPassword:
    dialog.mode === "edit" && resetPassword.value
      ? [{ required: true, message: "新密码不能为空", trigger: "blur" }]
      : [],
}));

function openAddDialog() {
  editingId = null;
  dialog.mode = "add";
  resetPassword.value = false;
  dialog.visible = true;
}

function openEditDialog(row: User) {
  editingId = row.id;
  dialog.mode = "edit";
  resetPassword.value = false;
  form.username = row.username;
  form.real_name = row.real_name ?? "";
  form.phone = row.phone ?? "";
  form.email = row.email ?? "";
  form.role = row.role;
  form.newPassword = "";
  dialog.visible = true;
}

function resetForm() {
  form.username = "";
  form.password = "";
  form.real_name = "";
  form.phone = "";
  form.email = "";
  form.role = "USER";
  form.newPassword = "";
  resetPassword.value = false;
  formRef.value?.clearValidate();
}

async function submitForm() {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  submitting.value = true;
  try {
    if (dialog.mode === "add") {
      const payload: any = {
        username: form.username,
        password: form.password,
        role: form.role,
        real_name: form.real_name || undefined,
        phone: form.phone || undefined,
        email: form.email || undefined,
      };
      const res = await userApi.create(payload);
      if (res.data.code === 0) {
        ElMessage.success("用户创建成功");
        dialog.visible = false;
        loadUsers();
      } else {
        ElMessage.error(res.data.message || "创建失败");
      }
    } else if (editingId !== null) {
      const payload: any = {
        real_name: form.real_name || undefined,
        phone: form.phone || undefined,
        email: form.email || undefined,
        role: form.role,
      };
      if (resetPassword.value && form.newPassword) {
        payload.password = form.newPassword;
      }
      const res = await userApi.update(editingId, payload);
      if (res.data.code === 0) {
        ElMessage.success("保存成功");
        dialog.visible = false;
        loadUsers();
      } else {
        ElMessage.error(res.data.message || "保存失败");
      }
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "操作失败");
  } finally {
    submitting.value = false;
  }
}

// ——— 禁用 / 启用 ———
async function handleToggleStatus(row: User, newStatus: 0 | 1) {
  try {
    const res = await userApi.toggleStatus(row.id, newStatus);
    if (res.data.code === 0) {
      ElMessage.success(newStatus === 1 ? "已启用" : "已禁用");
      loadUsers();
    } else {
      ElMessage.error(res.data.message || "操作失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "操作失败");
  }
}

onMounted(loadUsers);
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.users-page {
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

.search-card :deep(.el-card__body) {
  padding: 16px 20px 0;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.total-hint {
  font-size: 14px;
  color: #909399;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.self-tag {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}
</style>
