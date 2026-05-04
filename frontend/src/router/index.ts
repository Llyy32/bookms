import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import http from "../api/http";
import AppLayout from "../layouts/AppLayout.vue";
import LoginView from "../views/LoginView.vue";
import BooksView from "../views/BooksView.vue";
import UsersView from "../views/UsersView.vue";
import ProfileView from "../views/ProfileView.vue";
import BorrowView from "../views/BorrowView.vue";
import ReservationsView from "../views/ReservationsView.vue";
import ReportsView from "../views/ReportsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView },
    {
      path: "/",
      component: AppLayout,
      children: [
        { path: "", redirect: "/books" },
        { path: "books", component: BooksView },
        { path: "users", component: UsersView },
        { path: "borrows", component: BorrowView },
        { path: "reservations", component: ReservationsView },
        { path: "reports", component: ReportsView },
        { path: "profile", component: ProfileView },
      ],
    },
  ],
});

// 路由守卫：未登录时尝试从后端恢复 Session，失败则跳转登录页
router.beforeEach(async (to) => {
  if (to.path === "/login") return true;

  const authStore = useAuthStore();
  if (authStore.currentUser) return true;

  try {
    const res = await http.get<{ code: number; data: any }>("/auth/me");
    if (res.data.code === 0) {
      authStore.setUser({
        id: res.data.data.id,
        username: res.data.data.username,
        role: res.data.data.role,
      });
      return true;
    }
  } catch {
    // 会话无效，跳转登录
  }
  return "/login";
});

export default router;
