// FILE: src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Gate from '../views/Gate.vue'           // File mới (Thay cho Login cũ)
import AdminLogin from '../views/AdminLogin.vue' // File mới
import AdminDashboard from '../views/AdminDashboard.vue' // File Dashboard cũ sửa lại

const routes = [
  { path: '/', component: Gate },
  { path: '/admin-login', component: AdminLogin },
  { path: '/admin-dashboard', component: AdminDashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Guard: Kiểm tra nếu chưa đăng nhập Admin thì không cho vào Dashboard
router.beforeEach((to, from, next) => {
  const adminUser = localStorage.getItem('adminUser');
  if (to.path === '/admin-dashboard' && !adminUser) {
    next('/admin-login');
  } else {
    next();
  }
});

export default router