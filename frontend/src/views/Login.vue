<template>
  <div class="card login-card">
    <div class="header">
      <h2>🔐 Face Security</h2>
      <p>Vui lòng xác thực danh tính để truy cập</p>
    </div>

    <div class="content-wrapper">
      <div class="webcam-section">
        <div class="video-container">
          <video ref="video" autoplay playsinline muted></video>
          <div class="scan-line"></div>
          <div class="face-frame"></div>
        </div>
        <canvas ref="canvas" style="display: none;"></canvas>
        
        <button @click="captureAndLogin" :disabled="loading" class="btn-primary">
          <span v-if="!loading">📸 Quét khuôn mặt</span>
          <span v-else>Thinking...</span>
        </button>
      </div>

      <div class="divider">
        <span>HOẶC</span>
      </div>

      <div class="upload-section">
        <div class="upload-box">
          <label for="file-upload" class="custom-file-upload">
            📂 Tải ảnh có sẵn
          </label>
          <input id="file-upload" type="file" @change="uploadAndLogin" accept="image/*" />
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
      </div>
    </div>

    <div class="footer">
      Chưa có tài khoản? <router-link to="/register">Đăng ký ngay</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();
const video = ref(null);
const canvas = ref(null);
const loading = ref(false);
const error = ref('');
let stream = null;

onMounted(async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.value.srcObject = stream;
  } catch (err) {
    error.value = "⚠️ Không tìm thấy Camera!";
  }
});

onUnmounted(() => {
  if (stream) stream.getTracks().forEach(track => track.stop());
});

const sendToApi = async (base64Image) => {
  loading.value = true;
  error.value = '';
  try {
    const res = await axios.post('http://localhost:5000/api/login', { image: base64Image });
    if (res.data.success) {
      localStorage.setItem('user', JSON.stringify(res.data.user));
      router.push('/dashboard');
    }
  } catch (err) {
    error.value = err.response?.data?.message || "Không nhận diện được!";
  } finally {
    loading.value = false;
  }
};

const captureAndLogin = () => {
  if (!video.value) return;
  const ctx = canvas.value.getContext('2d');
  canvas.value.width = video.value.videoWidth;
  canvas.value.height = video.value.videoHeight;
  ctx.drawImage(video.value, 0, 0);
  sendToApi(canvas.value.toDataURL('image/jpeg'));
};

const uploadAndLogin = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => sendToApi(e.target.result);
  reader.readAsDataURL(file);
};
</script>

<style scoped>
.card {
  background: var(--card-bg);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  padding: 40px;
  width: 800px;
  max-width: 95%;
  text-align: center;
}

.header h2 { margin: 0; color: var(--primary-color); }
.header p { color: #666; margin-top: 5px; }

.content-wrapper {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin: 30px 0;
  gap: 20px;
}

/* Webcam Style */
.video-container {
  position: relative;
  width: 320px;
  height: 240px;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  background: #000;
}
video { width: 100%; height: 100%; object-fit: cover; }

/* Hiệu ứng Scan */
.scan-line {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 2px;
  background: #00ff00;
  box-shadow: 0 0 10px #00ff00;
  animation: scan 2s infinite linear;
}
@keyframes scan { 
  0% { top: 0%; } 50% { top: 100%; } 100% { top: 0%; } 
}

/* Nút bấm */
.btn-primary {
  margin-top: 15px;
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 50px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);
}
.btn-primary:disabled { background: #ccc; }

/* Divider */
.divider { display: flex; align-items: center; color: #999; font-size: 12px; font-weight: bold; }
.divider::before, .divider::after { content: ""; height: 1px; background: #ddd; width: 1px; flex-grow: 1; height: 50px; } /* Sửa thành dọc */

/* Upload */
input[type="file"] { display: none; }
.custom-file-upload {
  border: 2px dashed #ccc;
  display: inline-block;
  padding: 20px 40px;
  cursor: pointer;
  border-radius: 10px;
  color: #666;
  transition: 0.3s;
}
.custom-file-upload:hover { border-color: var(--primary-color); color: var(--primary-color); background: #f0fdf4; }

.error-msg { color: #e11d48; margin-top: 10px; font-weight: bold; }
.footer { margin-top: 20px; color: #666; font-size: 14px; }

/* Responsive Mobile */
@media (max-width: 768px) {
  .content-wrapper { flex-direction: column; }
  .video-container { width: 100%; }
}
</style>