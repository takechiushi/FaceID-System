<template>
  <div class="login-box">
    <h2>🔐 Đăng nhập Quản trị</h2>
    <form @submit.prevent="login">
      <div class="input-group">
        <label>Tài khoản</label>
        <input v-model="username" type="text" placeholder="admin" required>
      </div>
      <div class="input-group">
        <label>Mật khẩu</label>
        <input v-model="password" type="password" placeholder="***" required>
      </div>
      <button type="submit" class="btn-login">Đăng nhập</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
    <router-link to="/" class="back-link">← Quay lại Cổng</router-link>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const error = ref('');
const router = useRouter();

const login = async () => {
  try {
    const res = await axios.post('http://localhost:5000/api/admin/login', {
      username: username.value,
      password: password.value
    });
    if (res.data.success) {
      // Lưu thông tin admin vào LocalStorage
      localStorage.setItem('adminUser', JSON.stringify(res.data.user));
      router.push('/admin-dashboard');
    }
  } catch (err) {
    error.value = "Sai tài khoản hoặc mật khẩu!";
  }
};
</script>

<style scoped>
.login-box {
  background: white; padding: 40px; border-radius: 10px;
  width: 350px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}
h2 { color: var(--primary-color); margin-bottom: 20px; }
.input-group { margin-bottom: 15px; text-align: left; }
.input-group label { display: block; font-size: 14px; font-weight: bold; color: #555; margin-bottom: 5px; }
.input-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
.btn-login { width: 100%; padding: 12px; background: var(--primary-color); color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 16px; margin-top: 10px; }
.btn-login:hover { background: #4f46e5; }
.error { color: red; margin-top: 10px; font-size: 14px; }
.back-link { display: block; margin-top: 20px; font-size: 14px; color: #666; }
</style>