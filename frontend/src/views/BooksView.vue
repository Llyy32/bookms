<!-- ===================== Template 区块 ===================== -->
<!-- 说明：图书管理页，包含搜索筛选、数据表格、分页，以及新增/编辑/库存调整对话框 -->
<template>
  <div class="books-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <span class="page-title">图书管理</span>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :model="query" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            placeholder="书名 / 作者 / ISBN"
            clearable
            style="width: 220px"
            @keyup.enter="loadBooks"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-input
            v-model="query.category"
            placeholder="分类名称"
            clearable
            style="width: 160px"
            @keyup.enter="loadBooks"
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
      <el-button
        v-if="isAdmin"
        type="primary"
        @click="openAddDialog"
      >
        + 新增图书
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-card>
      <el-table
        :data="books"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="书名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="100" show-overflow-tooltip>
          <template #default="{ row }">{{ row.category || "-" }}</template>
        </el-table-column>
        <el-table-column prop="isbn" label="ISBN" width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.isbn || "-" }}</template>
        </el-table-column>
        <el-table-column label="库存（总/可借）" width="130" align="center">
          <template #default="{ row }">
            {{ row.total_stock }} / {{ row.available_stock }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? "在架" : "下架" }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- 借阅列：所有登录用户可见 -->
        <el-table-column label="借阅" width="90" align="center">
          <template #default="{ row }">
            <el-popconfirm
              v-if="row.status === 1 && row.available_stock > 0"
              :title="`确认借阅《${row.title}》？`"
              confirm-button-text="确认"
              cancel-button-text="取消"
              @confirm="handleBorrow(row)"
            >
              <template #reference>
                <el-button link type="primary" size="small">借阅</el-button>
              </template>
            </el-popconfirm>
            <span v-else class="no-borrow">不可借</span>
          </template>
        </el-table-column>
        <!-- 预约列：在架图书均可预约 -->
        <el-table-column label="预约" width="90" align="center">
          <template #default="{ row }">
            <el-popconfirm
              v-if="row.status === 1"
              :title="`确认预约《${row.title}》？`"
              confirm-button-text="确认"
              cancel-button-text="取消"
              @confirm="handleReserve(row)"
            >
              <template #reference>
                <el-button link type="warning" size="small">预约</el-button>
              </template>
            </el-popconfirm>
            <span v-else class="no-borrow">不可约</span>
          </template>
        </el-table-column>
        <el-table-column v-if="isAdmin" label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button link type="primary" size="small" @click="openStockDialog(row)">
              调库存
            </el-button>
            <template v-if="row.status === 1">
              <el-popconfirm
                :title="`确认下架《${row.title}》？`"
                confirm-button-text="确认"
                cancel-button-text="取消"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button link type="danger" size="small">下架</el-button>
                </template>
              </el-popconfirm>
            </template>
            <template v-else>
              <el-popconfirm
                :title="`确认将《${row.title}》恢复上架？`"
                confirm-button-text="确认"
                cancel-button-text="取消"
                @confirm="handleRestore(row)"
              >
                <template #reference>
                  <el-button link type="success" size="small">上架</el-button>
                </template>
              </el-popconfirm>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.per_page"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadBooks"
          @current-change="loadBooks"
        />
      </div>
    </el-card>

    <!-- 新增/编辑 对话框 -->
    <el-dialog
      v-model="bookDialog.visible"
      :title="bookDialog.mode === 'add' ? '新增图书' : '编辑图书'"
      width="520px"
      @close="resetBookForm"
    >
      <el-form
        ref="bookFormRef"
        :model="bookForm"
        :rules="bookRules"
        label-width="80px"
      >
        <el-form-item label="书名" prop="title">
          <el-input v-model="bookForm.title" placeholder="请输入书名" />
        </el-form-item>
        <el-form-item label="作者" prop="author">
          <el-input v-model="bookForm.author" placeholder="请输入作者" />
        </el-form-item>
        <el-form-item label="ISBN">
          <el-input v-model="bookForm.isbn" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="bookForm.category" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="出版社">
          <el-input v-model="bookForm.publisher" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="出版日期">
          <el-date-picker
            v-model="bookForm.publish_date"
            type="date"
            placeholder="可选"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <!-- 总库存仅新增时可设，编辑后续用调库存功能 -->
        <el-form-item v-if="bookDialog.mode === 'add'" label="总库存" prop="total_stock">
          <el-input-number
            v-model="bookForm.total_stock"
            :min="0"
            :precision="0"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bookDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBookForm">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 调整库存 对话框 -->
    <el-dialog
      v-model="stockDialog.visible"
      title="调整库存"
      width="400px"
      @close="stockDelta = 0"
    >
      <div v-if="stockDialog.book" class="stock-info">
        <p>书名：<b>{{ stockDialog.book.title }}</b></p>
        <p>当前总库存：<b>{{ stockDialog.book.total_stock }}</b> 册</p>
        <p>当前可借数量：<b>{{ stockDialog.book.available_stock }}</b> 册</p>
      </div>
      <el-form label-width="80px" style="margin-top: 16px">
        <el-form-item label="调整数量">
          <el-input-number
            v-model="stockDelta"
            :precision="0"
            placeholder="正数增加，负数减少"
            style="width: 100%"
          />
          <div class="stock-hint">正数增加副本，负数减少副本</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitStockAdjust">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含图书列表加载、CRUD 操作、库存调整等逻辑 -->
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { bookApi } from "../api/books";
import { borrowApi } from "../api/borrowRecords";
import { reservationApi } from "../api/reservations";
import type { Book } from "../api/books";

const authStore = useAuthStore();

// 管理员标识，用于控制操作列和新增按钮的显示
const isAdmin = computed(() => authStore.currentUser?.role === "ADMIN");

// 列表状态
const books = ref<Book[]>([]);
const total = ref(0);
const loading = ref(false);

// 查询条件
const query = reactive({ keyword: "", category: "", page: 1, per_page: 20 });

// 加载图书列表
async function loadBooks() {
  loading.value = true;
  try {
    const res = await bookApi.list({
      page: query.page,
      per_page: query.per_page,
      keyword: query.keyword,
      category: query.category,
    });
    if (res.data.code === 0) {
      books.value = res.data.data.items;
      total.value = res.data.data.total;
    }
  } catch {
    ElMessage.error("加载图书列表失败");
  } finally {
    loading.value = false;
  }
}

// 搜索：重置到第 1 页再查
function handleSearch() {
  query.page = 1;
  loadBooks();
}

// 重置搜索条件
function handleReset() {
  query.keyword = "";
  query.category = "";
  query.page = 1;
  loadBooks();
}

// ——— 新增 / 编辑 对话框 ———
const bookFormRef = ref<FormInstance>();
const submitting = ref(false);
const bookDialog = reactive({ visible: false, mode: "add" as "add" | "edit" });
let editingId: number | null = null;

const bookForm = reactive({
  isbn: "",
  title: "",
  author: "",
  category: "",
  publisher: "",
  publish_date: "",
  total_stock: 0,
});

const bookRules: FormRules = {
  title: [{ required: true, message: "书名不能为空", trigger: "blur" }],
  author: [{ required: true, message: "作者不能为空", trigger: "blur" }],
  total_stock: [{ required: true, message: "请填写总库存", trigger: "blur" }],
};

function openAddDialog() {
  editingId = null;
  bookDialog.mode = "add";
  bookDialog.visible = true;
}

function openEditDialog(row: Book) {
  editingId = row.id;
  bookDialog.mode = "edit";
  bookForm.isbn = row.isbn ?? "";
  bookForm.title = row.title;
  bookForm.author = row.author;
  bookForm.category = row.category ?? "";
  bookForm.publisher = row.publisher ?? "";
  bookForm.publish_date = row.publish_date ?? "";
  bookForm.total_stock = row.total_stock;
  bookDialog.visible = true;
}

function resetBookForm() {
  bookForm.isbn = "";
  bookForm.title = "";
  bookForm.author = "";
  bookForm.category = "";
  bookForm.publisher = "";
  bookForm.publish_date = "";
  bookForm.total_stock = 0;
  bookFormRef.value?.clearValidate();
}

async function submitBookForm() {
  if (!bookFormRef.value) return;
  const valid = await bookFormRef.value.validate().catch(() => false);
  if (!valid) return;

  // 构造提交数据，过滤空字符串为 undefined
  const payload: Record<string, any> = {
    title: bookForm.title,
    author: bookForm.author,
    isbn: bookForm.isbn || undefined,
    category: bookForm.category || undefined,
    publisher: bookForm.publisher || undefined,
    publish_date: bookForm.publish_date || undefined,
  };
  if (bookDialog.mode === "add") {
    payload.total_stock = bookForm.total_stock;
  }

  submitting.value = true;
  try {
    if (bookDialog.mode === "add") {
      const res = await bookApi.create(payload as any);
      if (res.data.code === 0) {
        ElMessage.success("新增成功");
        bookDialog.visible = false;
        loadBooks();
      } else {
        ElMessage.error(res.data.message || "新增失败");
      }
    } else if (editingId !== null) {
      const res = await bookApi.update(editingId, payload);
      if (res.data.code === 0) {
        ElMessage.success("保存成功");
        bookDialog.visible = false;
        loadBooks();
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

// ——— 下架 / 上架 ———
async function handleDelete(row: Book) {
  try {
    const res = await bookApi.delete(row.id);
    if (res.data.code === 0) {
      ElMessage.success(`《${row.title}》已下架`);
      loadBooks();
    } else {
      ElMessage.error(res.data.message || "操作失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "操作失败");
  }
}

async function handleRestore(row: Book) {
  try {
    const res = await bookApi.restore(row.id);
    if (res.data.code === 0) {
      ElMessage.success(`《${row.title}》已上架`);
      loadBooks();
    } else {
      ElMessage.error(res.data.message || "操作失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "操作失败");
  }
}

// ——— 调整库存 对话框 ———
const stockDialog = reactive<{ visible: boolean; book: Book | null }>({
  visible: false,
  book: null,
});
const stockDelta = ref(0);

function openStockDialog(row: Book) {
  stockDialog.book = row;
  stockDelta.value = 0;
  stockDialog.visible = true;
}

async function submitStockAdjust() {
  if (!stockDialog.book) return;
  if (stockDelta.value === 0) {
    ElMessage.warning("调整数量不能为 0");
    return;
  }
  submitting.value = true;
  try {
    const res = await bookApi.adjustStock(stockDialog.book.id, stockDelta.value);
    if (res.data.code === 0) {
      ElMessage.success("库存已更新");
      stockDialog.visible = false;
      loadBooks();
    } else {
      ElMessage.error(res.data.message || "操作失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "操作失败");
  } finally {
    submitting.value = false;
  }
}

// ——— 借阅 ———
async function handleBorrow(row: Book) {
  try {
    const res = await borrowApi.create(row.id);
    if (res.data.code === 0) {
      ElMessage.success(`《${row.title}》借阅成功，应还日期：${res.data.data.due_at.slice(0, 10)}`);
      loadBooks();
    } else {
      ElMessage.error(res.data.message || "借阅失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "借阅失败");
  }
}

// ——— 预约 ———
async function handleReserve(row: Book) {
  try {
    const res = await reservationApi.create(row.id);
    if (res.data.code === 0) {
      ElMessage.success(`《${row.title}》预约成功，到期时间：${res.data.data.expired_at?.slice(0, 10)}`);
    } else {
      ElMessage.error(res.data.message || "预约失败");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || "预约失败");
  }
}

onMounted(loadBooks);
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.books-page {
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

.stock-info {
  color: #606266;
  line-height: 2;
}

.stock-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.no-borrow {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
