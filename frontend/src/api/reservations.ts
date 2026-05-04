import http from "./http";

export interface Reservation {
  id: number;
  user_id: number;
  username: string | null;
  book_id: number;
  book_title: string | null;
  book_author: string | null;
  status: "ACTIVE" | "CANCELLED" | "FULFILLED" | "EXPIRED";
  reserved_at: string;
  expired_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReservationListQuery {
  page?: number;
  per_page?: number;
  status?: string;
  keyword?: string;
  user_id?: number;
}

export interface ReservationListResult {
  items: Reservation[];
  total: number;
  page: number;
  per_page: number;
}

export const reservationApi = {
  create: (book_id: number) =>
    http.post<{ code: number; message: string; data: Reservation }>(
      "/reservations",
      { book_id }
    ),

  cancel: (reservation_id: number) =>
    http.post<{ code: number; message: string; data: Reservation }>(
      `/reservations/${reservation_id}/cancel`,
      {}
    ),

  list: (params: ReservationListQuery) =>
    http.get<{ code: number; data: ReservationListResult }>("/reservations", {
      params,
    }),

  get: (reservation_id: number) =>
    http.get<{ code: number; data: Reservation }>(
      `/reservations/${reservation_id}`
    ),
};
