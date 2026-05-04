<!-- ===================== Template 区块 ===================== -->
<!-- 说明：借阅记录页，含状态筛选、书名搜索、归还操作；管理员可查看全部记录 -->
<template>
  <div class="borrow-page">
    <div class="page-header">
      <span class="page-title">借阅记录</span>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="query" inline>
        <el-form-item label="书名/作者">
          <el-input
            v-model="query.keyword"
            placeholder="书名或作者"
            clearable
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="借阅中" value="BORROWED" />
            <el-option label="逾期" value="OVERDUE" />
            <el-option label="已归还" value="RETURNED" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isAdmin" label="用户ID">
          <el-input
            v-model="query.user_id_str"
            placeholder="可选"
            clearable
            style="width: 100px"
          />
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
    </div>

    <!-- 数据表格 -->
    <el-card>
      <el-table :data="records" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="记录ID" width="80" />
        <el-table-column label="书名" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.book_title || "-" }}</template>
        </el-table-column>
        <el-table-column label="作者" width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ row.book_author || "-" }}</template>
        </el-table-column>
        <el-table-column v-if="isAdmin" label="借阅人" width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.username || "-" }}</template>
        </el-table-column>
        <el-table-column label="借阅时间" width="160">
          <template #default="{ row }">
            {{ row.borrowed_at.replace("T", " ").slice(0, 16) }}
          </template>
        </el-table-column>
        <el-table-column label="应还时间" width="160">
          <template #default="{ row }">
            <span :class="isOverdueDate(row) ? 'overdue-date' : ''">
              {{ row.due_at.replace("T", " ").slice(0, 16) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="归还时间" width="160">
          <template #default="{ row }">
            {{ row.returned_at ? row.returned_at.replace("T", " ").slice(0, 16) : "-" }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              v-if="canReturn(row)"
              :title="`确认归还《${row.book_title}》？`"
              confirm-button-text="确认"
              cancel-button-text="取消"
              @confirm="handleReturn(row)"
            >
              <template #reference>
                <el-button link type="primary" size="small">归还</el-button>
              </template>
            </el-popconfirm>
            <span v-else class="no-action">-</span>
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
          @size-change="loadRecords"
          @current-change="loadRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含借阅列表加载、状态过滤、归还操作逻辑 -->
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { borrowApi } from "../api/borrowRecords";
import type { BorrowRecord } from "../api/borrowRecords";

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.currentUser?.role === "ADMIN");

const records = ref<BorrowRecord[]>([]);
const total = ref(0);
const loading = ref(false);

const query = reactive({
  keyword: "",
  status: "",
  user_id_str: "",
  page: 1,
  per_page: 20,
});

async function loadRecords() {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: query.page,
      per_page: query.per_page,
    };
    if (query.keyword) params.keyword = query.keyword;
    if (query.status) params.status = query.status;
    if (isAdmin.value && query.user_id_str) {
      params.user_id = parseInt(query.user_id_str);
    }

    const res = await borrowApi.list(params);
    if (res.data.code === 0) {
      records.value = res.data.data.items;
      total.value = res.data.data.total;
    }
  } catch {
    ElMessage.error("加载借阅记录失败");
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  query.page = 1;
  loadRecords();
}

function handleReset() {
  query.keyword = "";
  query.status = "";
  query.user_id_str = "";
  query.page = 1;
  loadRecords();
}

// 归还操作
async function handleReturn(row: BorrowRecord) {
  try {
    const res = await borrowApi.return(row.id);
    if (res.data.code === 0) {
      ElMessage.success(`《${row.book_title}》已归还`);
      loadRecords();
    } else {
      ElMessage.error(res.data.message || "归还失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "归还失败");
  }
}

// 状态显示辅助
function statusLabel(status: string) {
  return { BORROWED: "借阅中", OVERDUE: "逾期", RETURNED: "已归还" }[status] ?? status;
}

function statusType(status: string) {
  return (
    { BORROWED: "primary", OVERDUE: "danger", RETURNED: "success" }[status] ?? "info"
  );
}

// 应还时间已过且未归还
function isOverdueDate(row: BorrowRecord) {
  return row.status !== "RETURNED" && new Date(row.due_at) < new Date();
}

// 只有 BORROWED/OVERDUE 且（本人或管理员）才能归还
function canReturn(row: BorrowRecord) {
  if (row.status === "RETURNED") return false;
  if (isAdmin.value) return true;
  return row.user_id === authStore.currentUser?.id;
}

onMounted(loadRecords);
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.borrow-page {
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

.overdue-date {
  color: #f56c6c;
  font-weight: bold;
}

.no-action {
  font-size: 14px;
  color: #c0c4cc;
}
</style>
