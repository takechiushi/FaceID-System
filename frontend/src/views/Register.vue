<template>
  <div class="card register-card">
    <h2>📝 Đăng ký Hồ sơ</h2>
    <p class="subtitle">Cung cấp dữ liệu khuôn mặt đa góc độ</p>

    <form @submit.prevent="handleRegister" class="form-grid">
      <div class="input-group full-width">
        <input v-model="form.name" type="text" placeholder="Họ và Tên" required />
      </div>
      <div class="input-group full-width">
        <input v-model="form.age" type="number" placeholder="Tuổi" required />
      </div>

      <div class="photo-grid">
        <div v-for="angle in angles" :key="angle" class="photo-item">
          <label :class="{ 'has-file': files[angle] }">
            <span class="icon">📷</span>
            <span>{{ angleLabels[angle] }}</span>
            <input type="file" @change="e => handleFileChange(e, angle)" accept="image/*" required />
          </label>
          <div class="file-name" v-if="files[angle]">✅ Đã chọn</div>
        </div>
      </div>

      <button type="submit" :disabled="loading" class="btn-submit" color="blue">
        {{ loading ? 'Đang xử lý dữ liệu...' : 'Hoàn tất Đăng ký' }}
      </button>
    </form>
    
    <div class="footer">
      <router-link to="/">← Quay lại Đăng nhập</router-link>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();
const loading = ref(false);
const angles = ['straight', 'up', 'left', 'right', 'down'];
const angleLabels = {
  straight: 'Nhìn Thẳng', up: 'Nhìn Lên', left: 'Nhìn Trái', right: 'Nhìn Phải', down: 'Cúi Xuống'
};
const form = reactive({ name: '', age: '' });
const files = reactive({});

const handleFileChange = (e, angle) => {
  files[angle] = e.target.files[0];
};

const handleRegister = async () => {
  loading.value = true;
  const formData = new FormData();
  formData.append('name', form.name);
  formData.append('age', form.age);
  angles.forEach(angle => { if (files[angle]) formData.append(angle, files[angle]); });

  try {
    await axios.post('http://localhost:5000/api/register', formData);
    alert('🎉 Đăng ký thành công!');
    router.push('/');
  } catch (error) {
    alert('Lỗi: ' + (error.response?.data?.message || 'Server Error'));
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.card {
  background: var(--card-bg);
  padding: 40px;
  border-radius: 20px;
  width: 600px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
h2 { color: var(--primary-color); margin-bottom: 5px; text-align: center; }
.subtitle { text-align: center; color: #666; margin-bottom: 30px; }

.form-grid { display: flex; flex-direction: column; gap: 15px; }

input[type="text"], input[type="number"] {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  transition: 0.3s;
}
input:focus { border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }

/* Photo Grid */
.photo-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 20px 0;
}
.photo-item label {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  border: 2px dashed #ccc; padding: 15px; border-radius: 10px;
  cursor: pointer; transition: 0.3s; height: 80px;
  color: #666; font-size: 13px; font-weight: bold;
}
.photo-item label:hover { border-color: var(--primary-color); background: #f5f3ff; }
.photo-item label.has-file { border-color: #10b981; background: #ecfdf5; color: #059669; }
.photo-item input { display: none; }
.icon { font-size: 20px; margin-bottom: 5px; }
.file-name { font-size: 11px; color: #10b981; text-align: center; margin-top: 3px; }

/* Nút Submit */
.btn-submit {
  background: var(--bg-gradient);
  color: blue;
  padding: 15px;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
}
.footer { text-align: center; margin-top: 20px; }
</style>