<template>
  <div class="dashboard-wrapper">
    <div class="dash-header">
      <h1>🛠️ Quản lý Hệ thống</h1>
      <button @click="logout" class="btn-logout">Đăng xuất</button>
    </div>

    <div class="content-grid">
      
      <div class="panel list-panel">
        <div class="panel-head">
          <h3>Danh sách nhân sự ({{ users.length }})</h3>
          <button @click="fetchUsers" class="btn-refresh">🔄</button>
        </div>
        
        <div class="user-list">
          <div v-for="user in users" :key="user._id" class="user-row">
            <img :src="'http://localhost:5000/' + user.avatar" class="avatar-small">
            <div class="u-info">
              <div class="u-name">{{ user.name }}</div>
              <div class="u-sub">Tuổi: {{ user.age }} | <span :class="'tag ' + user.role">{{ user.role }}</span></div>
            </div>
            <button @click="deleteUser(user._id)" class="btn-del">🗑️</button>
          </div>
        </div>
      </div>

      <div class="panel form-panel">
        <h3>📝 Thêm mới nhân sự</h3>
        <form @submit.prevent="registerUser">
          
          <div class="form-row">
            <div class="field">
              <label>Họ và Tên</label>
              <input v-model="form.name" type="text" required>
            </div>
            <div class="field sm">
              <label>Tuổi</label>
              <input v-model="form.age" type="number" required>
            </div>
          </div>

          <div class="field">
            <label>Chức vụ (Role)</label>
            <select v-model="form.role">
              <option value="user">Nhân viên thường</option>
              <option value="admin">Quản trị viên (Admin)</option>
            </select>
          </div>

          <div v-if="form.role === 'admin'" class="admin-auth-box">
            <div class="field">
              <label>Tên đăng nhập</label>
              <input v-model="form.username" type="text">
            </div>
            <div class="field">
              <label>Mật khẩu</label>
              <input v-model="form.password" type="text">
            </div>
          </div>

          <div class="field">
            <label>Chọn 5 ảnh khuôn mặt (Đa góc độ)</label>
            <input type="file" multiple @change="handleFiles" accept="image/*" required>
            <small>{{ form.files.length }} ảnh đã chọn</small>
          </div>

          <button type="submit" :disabled="loading" class="btn-save">
            {{ loading ? 'Đang xử lý...' : '➕ Thêm nhân sự' }}
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();
const users = ref([]);
const loading = ref(false);

const form = ref({
  name: '', age: '', role: 'user', username: '', password: '', files: []
});

// 1. Lấy danh sách user
const fetchUsers = async () => {
  try {
    const res = await axios.get('http://localhost:5000/api/users');
    users.value = res.data;
  } catch (err) { console.error(err); }
};

// 2. Xử lý xóa user
const deleteUser = async (id) => {
  if (!confirm("Bạn có chắc chắn muốn xóa người này?")) return;
  try {
    await axios.delete(`http://localhost:5000/api/users/${id}`);
    
    // Thay vì gọi fetchUsers(), ta lọc bỏ người vừa xóa khỏi danh sách hiện tại
    users.value = users.value.filter(user => user._id !== id);
    
    // Thông báo nhỏ (nếu cần)
    // alert("Đã xóa xong!"); 
  } catch (err) { 
    alert("Lỗi khi xóa!"); 
  }
};

// 3. Xử lý file input
const handleFiles = (e) => {
  form.value.files = e.target.files;
};

// 4. Đăng ký user mới
const registerUser = async () => {
  if (form.value.files.length < 1) return alert("Vui lòng chọn ảnh!");
  loading.value = true;
  
  const formData = new FormData();
  formData.append('name', form.value.name);
  formData.append('age', form.value.age);
  formData.append('role', form.value.role);
  
  if (form.value.role === 'admin') {
    formData.append('username', form.value.username);
    formData.append('password', form.value.password);
  }

  // Append từng file
  for (let i = 0; i < form.value.files.length; i++) {
    formData.append('files', form.value.files[i]);
  }

  try {
    await axios.post('http://localhost:5000/api/register', formData);
    alert("Thêm thành công!");
    fetchUsers(); // Refresh danh sách
    // Reset form
    form.value = { name: '', age: '', role: 'user', username: '', password: '', files: [] };
  } catch (err) {
    alert("Lỗi: " + (err.response?.data?.error || "Server Error"));
  } finally {
    loading.value = false;
  }
};

const logout = () => {
  localStorage.removeItem('adminUser');
  router.push('/');
};

onMounted(fetchUsers);
</script>

<style scoped>
.dashboard-wrapper { width: 100%; max-width: 1000px; }
.dash-header { display: flex; justify-content: space-between; align-items: center; color: white; margin-bottom: 20px; }
.btn-logout { background: rgba(255,255,255,0.2); border: none; color: white; padding: 8px 15px; border-radius: 5px; cursor: pointer; }

.content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); height: 500px; overflow-y: auto; }

/* List Style */
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
.user-row { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #f0f0f0; transition: 0.2s; }
.user-row:hover { background: #f9fafb; }
.avatar-small { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #ddd; }
.u-info { flex: 1; margin-left: 10px; }
.u-name { font-weight: bold; color: #333; }
.u-sub { font-size: 12px; color: #666; }
.tag.admin { color: #8b5cf6; font-weight: bold; }
.tag.user { color: #10b981; }
.btn-del { background: #fee2e2; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }

/* Form Style */
.form-row { display: grid; grid-template-columns: 2fr 1fr; gap: 10px; }
.field { margin-bottom: 15px; }
.field label { display: block; font-size: 12px; font-weight: bold; margin-bottom: 5px; color: #555; }
.field input, .field select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
.admin-auth-box { background: #fff7ed; padding: 10px; border: 1px dashed #f97316; border-radius: 5px; margin-bottom: 15px; }
.btn-save { width: 100%; background: var(--primary-color); color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
.btn-save:disabled { background: #ccc; }
</style>