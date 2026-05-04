import http from "./http";

export interface Book {
  id: number;
  isbn: string | null;
  title: string;
  author: string;
  category: string | null;
  publisher: string | null;
  publish_date: string | null;
  total_stock: number;
  available_stock: number;
  status: number;
  created_at: string;
  updated_at: string;
}

export interface BookListQuery {
  page?: number;
  per_page?: number;
  keyword?: string;
  category?: string;
}

export interface BookListResult {
  items: Book[];
  total: number;
  page: number;
  per_page: number;
}

export interface BookForm {
  isbn?: string;
  title: string;
  author: string;
  category?: string;
  publisher?: string;
  publish_date?: string;
  total_stock?: number;
}

export const bookApi = {
  list: (params: BookListQuery) =>
    http.get<{ code: number; data: BookListResult }>("/books", { params }),

  get: (id: number) =>
    http.get<{ code: number; data: Book }>(`/books/${id}`),

  create: (data: BookForm) =>
    http.post<{ code: number; data: Book }>("/books", data),

  update: (id: number, data: Partial<BookForm>) =>
    http.put<{ code: number; data: Book }>(`/books/${id}`, data),

  delete: (id: number) =>
    http.delete<{ code: number }>(`/books/${id}`),

  restore: (id: number) =>
    http.patch<{ code: number; data: Book }>(`/books/${id}/restore`, {}),

  adjustStock: (id: number, delta: number) =>
    http.patch<{ code: number; data: Book }>(`/books/${id}/stock`, { delta }),
};
