import { defineStore } from "pinia";

type CurrentUser = {
  id: number;
  username: string;
  role: "ADMIN" | "USER";
} | null;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    currentUser: null as CurrentUser
  }),
  actions: {
    setUser(user: CurrentUser) {
      this.currentUser = user;
    },
    clearUser() {
      this.currentUser = null;
    }
  }
});
