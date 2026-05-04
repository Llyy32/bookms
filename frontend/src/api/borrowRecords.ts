import http from "./http";

export interface BorrowRecord {
  id: number;
  user_id: number;
  username: string | null;
  book_id: number;
  book_title: string | null;
  book_author: string | null;
  borrowed_at: string;
  due_at: string;
  returned_at: string | null;
  status: "BORROWED" | "OVERDUE" | "RETURNED";
  created_at: string;
  updated_at: string;
}

export interface BorrowListQuery {
  page?: number;
  per_page?: number;
  status?: string;
  keyword?: string;
  user_id?: number;
}

export interface BorrowListResult {
  items: BorrowRecord[];
  total: number;
  page: number;
  per_page: number;
}

export const borrowApi = {
  create: (book_id: number) =>
    http.post<{ code: number; message: string; data: BorrowRecord }>(
      "/borrow-records",
      { book_id }
    ),

  return: (record_id: number) =>
    http.post<{ code: number; message: string; data: BorrowRecord }>(
      `/borrow-records/${record_id}/return`,
      {}
    ),

  list: (params: BorrowListQuery) =>
    http.get<{ code: number; data: BorrowListResult }>("/borrow-records", {
      params,
    }),

  get: (record_id: number) =>
    http.get<{ code: number; data: BorrowRecord }>(
      `/borrow-records/${record_id}`
    ),
};
