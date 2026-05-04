<!-- ===================== Template 区块 ===================== -->
<!-- 说明：应用外壳，包含左侧导航菜单、顶部工具栏和主内容区域 -->
<template>
  <el-container class="app-shell">
    <!-- 左侧导航栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">bookMS</div>
      <el-menu
        :default-active="route.path"
        router
        class="sidebar-menu"
        text-color="#a6adb4"
        active-text-color="#ffffff"
        background-color="#001529"
      >
        <el-menu-item index="/books">图书管理</el-menu-item>
        <el-menu-item v-if="isAdmin" index="/users">用户管理</el-menu-item>
        <el-menu-item index="/borrows">借阅记录</el-menu-item>
        <el-menu-item index="/reservations">预约管理</el-menu-item>
        <el-menu-item v-if="isAdmin" index="/reports">报表统计</el-menu-item>
        <el-menu-item index="/profile">个人资料</el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主体 -->
    <el-container direction="vertical">
      <el-header class="app-header">
        <span class="app-title">图书管理系统</span>
        <div class="header-actions">
          <span class="username">{{ authStore.currentUser?.username }}</span>
          <el-divider direction="vertical" />
          <el-button link type="primary" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<!-- ===================== Script 区块 ===================== -->
<!-- 说明：组合式 API，含登出逻辑和当前用户状态读取 -->
<script setup lang="ts">
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import http from "../api/http";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// 管理员标识，控制"用户管理"菜单项的显示
const isAdmin = computed(() => authStore.currentUser?.role === "ADMIN");

// 退出：清理后端 Session 后清空 store 并跳转登录页
async function handleLogout() {
  try {
    await http.post("/auth/logout");
  } catch {
    // 忽略退出接口错误，仍清理本地状态
  }
  authStore.clearUser();
  ElMessage.success("已退出登录");
  router.push("/login");
}
</script>

<!-- ===================== Style 区块 ===================== -->
<!-- 说明：局部样式（scoped） -->
<style scoped>
.app-shell {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background-color: #001529;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 3px;
  background-color: #001529;
  border-bottom: 1px solid #0d2137;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
  height: 60px;
  flex-shrink: 0;
}

.app-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  color: #606266;
  font-size: 14px;
}

.main-content {
  background-color: #f5f7fa;
  overflow-y: auto;
  padding: 20px;
}
</style>
