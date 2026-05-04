import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import App from "./App.vue";
import router from "./router";

// 挂载全局插件：状态管理、路由与 Element Plus 组件库
createApp(App).
use(createPinia()).
use(router).
use(ElementPlus).
mount("#app");
