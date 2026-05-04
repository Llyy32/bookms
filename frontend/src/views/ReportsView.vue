<!-- ===================== Template 区块 ===================== -->
<!-- 说明：报表统计页，含借阅排行、逾期统计、库存统计、用户活跃度四个 Tab，管理员专用 -->
<template>
  <div class="reports-page">
    <div class="page-header">
      <span class="page-title">报表统计</span>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">

      <!-- ── 借阅排行榜 ── -->
      <el-tab-pane label="借阅排行" name="borrow-ranking">
        <div class="tab-toolbar">
          <el-date-picker
            v-model="borrowRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
          <el-input-number v-model="borrowLimit" :min="5" :max="50" :step="5" style="width: 120px" />
          <el-button type="primary" @click="loadBorrowRanking">查询</el-button>
        </div>
        <div v-loading="borrowLoading">
          <div ref="borrowChartRef" class="chart-area" />
          <el-table :data="borrowData" stripe size="small" style="margin-top:16px">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="title" label="书名" min-width="160" show-overflow-tooltip />
            <el-table-column prop="author" label="作者" width="120" />
            <el-table-column prop="category" label="分类" width="100">
              <template #default="{ row }">{{ row.category || "-" }}</template>
            </el-table-column>
            <el-table-column prop="borrow_count" label="借阅次数" width="100" align="center" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ── 逾期统计 ── -->
      <el-tab-pane label="逾期统计" name="overdue-summary">
        <div class="tab-toolbar">
          <el-date-picker
            v-model="overdueRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
          <el-button type="primary" @click="loadOverdueSummary">查询</el-button>
        </div>
        <div v-loading="overdueLoading">
          <el-row :gutter="16" class="stat-cards">
            <el-col :span="8">
              <el-card shadow="never" class="stat-card">
                <div class="stat-num">{{ overdueData.total_overdue }}</div>
                <div class="stat-label">累计逾期记录</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never" class="stat-card danger">
                <div class="stat-num">{{ overdueData.currently_overdue }}</div>
                <div class="stat-label">当前仍逾期</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never" class="stat-card success">
                <div class="stat-num">{{ overdueData.returned_overdue }}</div>
                <div class="stat-label">逾期后已归还</div>
              </el-card>
            </el-col>
          </el-row>
          <div class="section-title">逾期次数最多图书 Top 10</div>
          <el-table :data="overdueData.top_books" stripe size="small">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="title" label="书名" min-width="200" show-overflow-tooltip />
            <el-table-column prop="overdue_count" label="逾期次数" width="100" align="center" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ── 库存统计 ── -->
      <el-tab-pane label="库存统计" name="stock-summary">
        <div v-loading="stockLoading">
          <el-row :gutter="16" class="stat-cards">
            <el-col :span="8">
              <el-card shadow="never" class="stat-card">
                <div class="stat-num">{{ stockData.total_stock }}</div>
                <div class="stat-label">总册数</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never" class="stat-card success">
                <div class="stat-num">{{ stockData.available_stock }}</div>
                <div class="stat-label">可借册数</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="never" class="stat-card warning">
                <div class="stat-num">{{ stockData.borrowed_stock }}</div>
                <div class="stat-label">在借册数</div>
              </el-card>
            </el-col>
          </el-row>
          <div ref="stockChartRef" class="chart-area" />
          <div class="section-title">分类明细</div>
          <el-table :data="stockData.by_category" stripe size="small">
            <el-table-column prop="category" label="分类" min-width="120" />
            <el-table-column prop="total_stock" label="总册数" width="100" align="center" />
            <el-table-column prop="available_stock" label="可借" width="100" align="center" />
            <el-table-column prop="borrowed_stock" label="在借" width="100" align="center" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ── 用户活跃度 ── -->
      <el-tab-pane label="用户活跃度" name="user-activity">
        <div class="tab-toolbar">
          <el-date-picker
            v-model="activityRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
          <el-input-number v-model="activityLimit" :min="5" :max="50" :step="5" style="width: 120px" />
          <el-button type="primary" @click="loadUserActivity">查询</el-button>
        </div>
        <div v-loading="activityLoading">
          <div ref="activityChartRef" class="chart-area" />
          <el-table :data="activityData" stripe size="small" style="margin-top:16px">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="real_name" label="姓名" width="110">
              <template #default="{ row }">{{ row.real_name || "-" }}</template>
            </el-table-column>
            <el-table-column prop="borrow_count" label="借阅次数" width="100" align="center" />
          </el-table>
        </div>
      </el-tab-pane>

    </el-tabs>
  </div>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含四个报表的数据加载和 ECharts 图表初始化/更新逻辑 -->
<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import * as echarts from "echarts";
import http from "../api/http";

const activeTab = ref("borrow-ranking");

// ── 借阅排行榜 ──────────────────────────────────────────────
const borrowChartRef = ref<HTMLElement>();
const borrowLoading = ref(false);
const borrowRange = ref<[string, string] | null>(null);
const borrowLimit = ref(20);
const borrowData = ref<any[]>([]);
let borrowChart: echarts.ECharts | null = null;

async function loadBorrowRanking() {
  borrowLoading.value = true;
  try {
    const params: Record<string, any> = { limit: borrowLimit.value };
    if (borrowRange.value) {
      params.start = borrowRange.value[0];
      params.end = borrowRange.value[1];
    }
    const res = await http.get<{ code: number; data: any[] }>("/reports/borrow-ranking", { params });
    if (res.data.code === 0) {
      borrowData.value = res.data.data;
      await nextTick();
      renderBorrowChart();
    }
  } catch {
    ElMessage.error("加载借阅排行失败");
  } finally {
    borrowLoading.value = false;
  }
}

function renderBorrowChart() {
  if (!borrowChartRef.value) return;
  if (!borrowChart) borrowChart = echarts.init(borrowChartRef.value);
  const data = [...borrowData.value].reverse();
  borrowChart.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 160, right: 40, top: 20, bottom: 20 },
    xAxis: { type: "value", name: "借阅次数" },
    yAxis: {
      type: "category",
      data: data.map((d) => d.title),
      axisLabel: { width: 150, overflow: "truncate" },
    },
    series: [{ type: "bar", data: data.map((d) => d.borrow_count), itemStyle: { color: "#409eff" } }],
  });
}

// ── 逾期统计 ──────────────────────────────────────────────
const overdueLoading = ref(false);
const overdueRange = ref<[string, string] | null>(null);
const overdueData = reactive({ total_overdue: 0, currently_overdue: 0, returned_overdue: 0, top_books: [] as any[] });

async function loadOverdueSummary() {
  overdueLoading.value = true;
  try {
    const params: Record<string, any> = {};
    if (overdueRange.value) {
      params.start = overdueRange.value[0];
      params.end = overdueRange.value[1];
    }
    const res = await http.get<{ code: number; data: any }>("/reports/overdue-summary", { params });
    if (res.data.code === 0) {
      Object.assign(overdueData, res.data.data);
    }
  } catch {
    ElMessage.error("加载逾期统计失败");
  } finally {
    overdueLoading.value = false;
  }
}

// ── 库存统计 ──────────────────────────────────────────────
const stockChartRef = ref<HTMLElement>();
const stockLoading = ref(false);
const stockData = reactive({ total_stock: 0, available_stock: 0, borrowed_stock: 0, by_category: [] as any[] });
let stockChart: echarts.ECharts | null = null;

async function loadStockSummary() {
  stockLoading.value = true;
  try {
    const res = await http.get<{ code: number; data: any }>("/reports/stock-summary");
    if (res.data.code === 0) {
      Object.assign(stockData, res.data.data);
      await nextTick();
      renderStockChart();
    }
  } catch {
    ElMessage.error("加载库存统计失败");
  } finally {
    stockLoading.value = false;
  }
}

function renderStockChart() {
  if (!stockChartRef.value || stockData.by_category.length === 0) return;
  if (!stockChart) stockChart = echarts.init(stockChartRef.value);
  const cats = stockData.by_category.map((d: any) => d.category);
  stockChart.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { data: ["可借", "在借"], top: 0 },
    grid: { left: 100, right: 40, top: 40, bottom: 20 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: [...cats].reverse(), axisLabel: { width: 90, overflow: "truncate" } },
    series: [
      {
        name: "可借", type: "bar", stack: "total",
        data: [...stockData.by_category].reverse().map((d: any) => d.available_stock),
        itemStyle: { color: "#67c23a" },
      },
      {
        name: "在借", type: "bar", stack: "total",
        data: [...stockData.by_category].reverse().map((d: any) => d.borrowed_stock),
        itemStyle: { color: "#e6a23c" },
      },
    ],
  });
}

// ── 用户活跃度 ──────────────────────────────────────────────
const activityChartRef = ref<HTMLElement>();
const activityLoading = ref(false);
const activityRange = ref<[string, string] | null>(null);
const activityLimit = ref(20);
const activityData = ref<any[]>([]);
let activityChart: echarts.ECharts | null = null;

async function loadUserActivity() {
  activityLoading.value = true;
  try {
    const params: Record<string, any> = { limit: activityLimit.value };
    if (activityRange.value) {
      params.start = activityRange.value[0];
      params.end = activityRange.value[1];
    }
    const res = await http.get<{ code: number; data: any[] }>("/reports/user-activity", { params });
    if (res.data.code === 0) {
      activityData.value = res.data.data;
      await nextTick();
      renderActivityChart();
    }
  } catch {
    ElMessage.error("加载用户活跃度失败");
  } finally {
    activityLoading.value = false;
  }
}

function renderActivityChart() {
  if (!activityChartRef.value) return;
  if (!activityChart) activityChart = echarts.init(activityChartRef.value);
  const data = [...activityData.value].reverse();
  activityChart.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 120, right: 40, top: 20, bottom: 20 },
    xAxis: { type: "value", name: "借阅次数" },
    yAxis: {
      type: "category",
      data: data.map((d) => d.username),
      axisLabel: { width: 110, overflow: "truncate" },
    },
    series: [{ type: "bar", data: data.map((d) => d.borrow_count), itemStyle: { color: "#9b59b6" } }],
  });
}

// Tab 切换时按需加载数据
function handleTabChange(name: string) {
  if (name === "borrow-ranking" && borrowData.value.length === 0) loadBorrowRanking();
  if (name === "overdue-summary" && overdueData.total_overdue === 0) loadOverdueSummary();
  if (name === "stock-summary" && stockData.total_stock === 0) loadStockSummary();
  if (name === "user-activity" && activityData.value.length === 0) loadUserActivity();
}

// 窗口 resize 时重绘图表
function handleResize() {
  borrowChart?.resize();
  stockChart?.resize();
  activityChart?.resize();
}

onMounted(() => {
  loadBorrowRanking();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  borrowChart?.dispose();
  stockChart?.dispose();
  activityChart?.dispose();
});
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.reports-page {
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

.tab-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.chart-area {
  width: 100%;
  height: 360px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 8px 0;
}

.stat-card.danger :deep(.el-card__body) {
  background-color: #fef0f0;
}

.stat-card.success :deep(.el-card__body) {
  background-color: #f0f9eb;
}

.stat-card.warning :deep(.el-card__body) {
  background-color: #fdf6ec;
}

.stat-num {
  font-size: 36px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-card.danger .stat-num { color: #f56c6c; }
.stat-card.success .stat-num { color: #67c23a; }
.stat-card.warning .stat-num { color: #e6a23c; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}

.section-title {
  font-size: 14px;
  font-weight: bold;
  color: #606266;
  margin: 16px 0 8px;
}
</style>
