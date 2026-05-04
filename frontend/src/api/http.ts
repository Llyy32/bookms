import axios from "axios";

const http = axios.create({
  // 后端统一 API 前缀
  baseURL: "/api/v1",
  // Session/Cookie 鉴权依赖浏览器携带凭证
  withCredentials: true,
  timeout: 10000
});

export default http;
