import http from "./http";

export interface User {
  id: number;
  username: string;
  role: "ADMIN" | "USER";
  real_name: string | null;
  phone: string | null;
  email: string | null;
  status: number;
  created_at: string;
  updated_at: string;
}

export interface UserListQuery {
  page?: number;
  per_page?: number;
  keyword?: string;
  role?: string;
  status?: number | string;
}

export interface UserListResult {
  items: User[];
  total: number;
  page: number;
  per_page: number;
}

export interface CreateUserForm {
  username: string;
  password: string;
  role?: "ADMIN" | "USER";
  real_name?: string;
  phone?: string;
  email?: string;
}

export interface UpdateUserForm {
  real_name?: string;
  phone?: string;
  email?: string;
  role?: "ADMIN" | "USER";
  password?: string;
}

export interface ProfileForm {
  real_name?: string;
  phone?: string;
  email?: string;
}

export const userApi = {
  list: (params: UserListQuery) =>
    http.get<{ code: number; data: UserListResult }>("/users", { params }),

  get: (id: number) =>
    http.get<{ code: number; data: User }>(`/users/${id}`),

  create: (data: CreateUserForm) =>
    http.post<{ code: number; data: User }>("/users", data),

  update: (id: number, data: UpdateUserForm) =>
    http.put<{ code: number; data: User }>(`/users/${id}`, data),

  toggleStatus: (id: number, status: 0 | 1) =>
    http.patch<{ code: number }>(`/users/${id}/status`, { status }),

  // 普通用户自助接口
  updateProfile: (data: ProfileForm) =>
    http.put<{ code: number; data: User }>("/users/me", data),

  changePassword: (old_password: string, new_password: string) =>
    http.patch<{ code: number }>("/users/me/password", {
      old_password,
      new_password,
    }),
};
