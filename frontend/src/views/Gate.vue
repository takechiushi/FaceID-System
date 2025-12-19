<template>
  <div class="gate-container">
    
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>

    <div class="gate-header">
      <div class="brand">
        <div class="logo-circle">AI</div>
        <div class="brand-text">
          <h2>FACE ID SYSTEM</h2>
          <small>Cổng kiểm soát an ninh</small>
        </div>
      </div>
      <router-link to="/admin-login" class="btn-admin">
        ⚙️ Quản trị
      </router-link>
    </div>

    <div class="content-wrapper">
      <div class="camera-frame" :class="{ 'inactive': recognizedUser }">
        <video ref="video" autoplay playsinline muted></video>
        
        <div class="viewfinder">
          <div class="corner tl"></div>
          <div class="corner tr"></div>
          <div class="corner bl"></div>
          <div class="corner br"></div>
        </div>

        <div v-if="!recognizedUser && !isUploading" class="scanner-laser"></div>

        <div class="camera-status">
          <span class="dot" :class="{ 'red': isUploading, 'green': !isUploading }"></span>
          {{ isUploading ? 'Đang xử lý ảnh...' : 'Đang hoạt động' }}
        </div>
      </div>
      <canvas ref="canvas" style="display: none;"></canvas>

      <div class="manual-action" v-if="!recognizedUser">
        <label for="file-upload" class="link-upload" :class="{ 'disabled': isUploading }">
          📂 Gặp sự cố? Tải ảnh lên
        </label>
        <input id="file-upload" type="file" @change="handleFileUpload" accept="image/*" :disabled="isUploading">
      </div>
    </div>

    <transition name="pop-in">
      <div v-if="recognizedUser" class="modal-overlay">
        <div class="modal-card">
          
          <div class="modal-header success">
            <div class="icon-circle">✓</div>
            <h3>XÁC THỰC THÀNH CÔNG</h3>
          </div>

          <div class="modal-body">
            <div class="user-avatar">
              <img :src="getAvatarUrl(recognizedUser.avatar)" alt="Avatar" @error="handleImgError">
            </div>

            <div class="user-details">
              <h2 class="name">{{ recognizedUser.name }}</h2>
              <p class="role-badge" :class="recognizedUser.role">
                {{ recognizedUser.role === 'admin' ? 'Quản Trị Viên' : 'Nhân Viên' }}
              </p>
              
              <div class="detail-row">
                <span>Mã nhân viên:</span>
                <strong>{{ recognizedUser._id.substring(0, 6).toUpperCase() }}</strong>
              </div>
              <div class="detail-row">
                <span>Thời gian:</span>
                <strong class="time">{{ currentTime }}</strong>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="resetState" class="btn-confirm">
              XÁC NHẬN (OK)
            </button>
          </div>

        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';

const video = ref(null);
const canvas = ref(null);
const recognizedUser = ref(null);
const currentTime = ref('');
const isUploading = ref(false);
let intervalId = null;

// --- HÀM XỬ LÝ URL ẢNH (FIX LỖI ẢNH) ---
const getAvatarUrl = (path) => {
  if (!path) return 'https://via.placeholder.com/150';
  // 1. Thay thế dấu backslash '\' của Windows thành '/'
  // 2. Nếu path chưa có http, nối thêm localhost vào
  const cleanPath = path.replace(/\\/g, '/'); 
  return `http://localhost:5000/${cleanPath}`;
};

// Hàm xử lý khi ảnh bị lỗi (load ảnh mặc định)
const handleImgError = (e) => {
  e.target.src = "https://cdn-icons-png.flaticon.com/512/149/149071.png";
};

// --- LOGIC CHÍNH ---

const handleSuccess = (user) => {
    recognizedUser.value = user;
    currentTime.value = dayjs().format('HH:mm:ss - DD/MM/YYYY');
    // KHÔNG CÒN setTimeout tự đóng nữa
};

// Hàm đóng Modal và Reset trạng thái để quét tiếp
const resetState = () => {
  recognizedUser.value = null;
  // Reset input file để có thể chọn lại file cũ nếu muốn
  const input = document.getElementById('file-upload');
  if (input) input.value = '';
};

// 1. Camera Logic
const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    if(video.value) video.value.srcObject = stream;
  } catch(err) { 
    console.error(err);
    alert("Không tìm thấy camera!");
  }
};

const captureAndCheck = async () => {
  if (!video.value || !canvas.value) return;
  // Dừng quét nếu đang hiện kết quả hoặc đang upload
  if (recognizedUser.value || isUploading.value) return; 

  const ctx = canvas.value.getContext('2d');
  if (video.value.videoWidth === 0) return;

  canvas.value.width = video.value.videoWidth;
  canvas.value.height = video.value.videoHeight;
  ctx.drawImage(video.value, 0, 0);
  
  const blob = await new Promise(r => canvas.value.toBlob(r, 'image/jpeg'));
  const formData = new FormData();
  formData.append('file', blob);

  try {
    const res = await axios.post('http://localhost:5000/api/recognize', formData);
    if (res.data.found) handleSuccess(res.data.user);
  } catch (e) { }
};

// 2. Upload Logic
const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    isUploading.value = true;
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await axios.post('http://localhost:5000/api/recognize', formData);
        if (res.data.found) handleSuccess(res.data.user);
        else alert("❌ Không nhận diện được khuôn mặt!");
    } catch (err) {
        alert("Lỗi kết nối Server.");
    } finally {
        isUploading.value = false;
    }
};

onMounted(() => {
  startCamera();
  intervalId = setInterval(captureAndCheck, 1000);
});

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
  if (video.value && video.value.srcObject) {
      video.value.srcObject.getTracks().forEach(t => t.stop());
  }
});
</script>

<style scoped>
/* --- 1. NỀN & LAYOUT (GIAO DIỆN SÁNG ĐẸP) --- */
.gate-container {
  display: flex; flex-direction: column; align-items: center;
  width: 100%; min-height: 100vh;
  background: #f3f4f6; /* Nền xám sáng chuyên nghiệp */
  position: relative; overflow: hidden;
  font-family: 'Segoe UI', sans-serif;
}

/* Các hình khối trang trí nền */
.bg-shape { position: absolute; border-radius: 50%; filter: blur(80px); z-index: 0; }
.shape-1 { width: 400px; height: 400px; background: rgba(99, 102, 241, 0.2); top: -100px; left: -100px; }
.shape-2 { width: 300px; height: 300px; background: rgba(16, 185, 129, 0.15); bottom: 0; right: 0; }

/* --- 2. HEADER --- */
.gate-header {
  width: 100%; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center;
  z-index: 10; background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.brand { display: flex; align-items: center; gap: 15px; }
.logo-circle {
  width: 45px; height: 45px; background: var(--primary-color); color: white;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 18px; box-shadow: 0 4px 10px rgba(99, 102, 241, 0.4);
}
.brand-text h2 { margin: 0; font-size: 18px; color: #1f2937; letter-spacing: 0.5px; }
.brand-text small { color: #6b7280; font-size: 12px; }

.btn-admin {
  text-decoration: none; color: #4b5563; font-weight: 600; font-size: 14px;
  padding: 8px 16px; border-radius: 8px; transition: 0.2s; border: 1px solid transparent;
}
.btn-admin:hover { background: white; border-color: #e5e7eb; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }

/* --- 3. CAMERA FRAME --- */
.content-wrapper { z-index: 1; margin-top: 40px; display: flex; flex-direction: column; align-items: center; }

.camera-frame {
  position: relative; width: 680px; height: 480px;
  background: black; border-radius: 24px; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  border: 8px solid white; /* Viền trắng dày tạo cảm giác khung hình */
  transition: all 0.3s;
}
.camera-frame.inactive { filter: blur(10px) grayscale(80%); }

video { width: 100%; height: 100%; object-fit: cover; }

/* Viewfinder (4 góc) */
.viewfinder { position: absolute; inset: 40px; pointer-events: none; }
.corner { position: absolute; width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.6); }
.tl { top: 0; left: 0; border-right: none; border-bottom: none; border-radius: 12px 0 0 0; }
.tr { top: 0; right: 0; border-left: none; border-bottom: none; border-radius: 0 12px 0 0; }
.bl { bottom: 0; left: 0; border-right: none; border-top: none; border-radius: 0 0 0 12px; }
.br { bottom: 0; right: 0; border-left: none; border-top: none; border-radius: 0 0 12px 0; }

/* Scanner Laser */
.scanner-laser {
  position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: #10b981; box-shadow: 0 0 20px 2px #10b981;
  animation: scan 2s infinite ease-in-out;
}
@keyframes scan { 0% {top: 10%} 50% {top: 90%} 100% {top: 10%} }

.camera-status {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: rgba(0,0,0,0.6); color: white; padding: 6px 15px; border-radius: 20px;
  font-size: 13px; display: flex; align-items: center; gap: 8px; backdrop-filter: blur(4px);
}
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.green { background: #10b981; box-shadow: 0 0 5px #10b981; }
.dot.red { background: #ef4444; box-shadow: 0 0 5px #ef4444; }

/* Manual Upload Link */
.manual-action { margin-top: 20px; }
.link-upload {
  color: #6b7280; font-size: 14px; cursor: pointer; text-decoration: underline; transition: 0.2s;
}
.link-upload:hover { color: var(--primary-color); }
.link-upload.disabled { cursor: wait; opacity: 0.5; }
input[type="file"] { display: none; }

/* --- 4. MODAL KẾT QUẢ (POPUP) --- */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.4); z-index: 100;
  display: flex; justify-content: center; align-items: center;
  backdrop-filter: blur(5px);
}

.modal-card {
  background: white; width: 450px; border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0,0,0,0.25);
  overflow: hidden;
  animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-header {
  background: #10b981; color: white; padding: 25px; text-align: center;
}
.icon-circle {
  width: 50px; height: 50px; background: white; color: #10b981;
  border-radius: 50%; font-size: 30px; font-weight: bold;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 10px;
}
.modal-header h3 { margin: 0; font-size: 18px; letter-spacing: 1px; }

.modal-body { padding: 30px 20px; text-align: center; }

.user-avatar img {
  width: 120px; height: 120px; border-radius: 50%; object-fit: cover;
  border: 4px solid #f3f4f6; margin-bottom: 15px;
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.name { margin: 0; color: #1f2937; font-size: 24px; }
.role-badge {
  display: inline-block; padding: 4px 12px; border-radius: 12px;
  font-size: 12px; font-weight: bold; color: white; margin: 8px 0 20px;
}
.role-badge.admin { background: #8b5cf6; }
.role-badge.user { background: #3b82f6; }

.detail-row {
  display: flex; justify-content: space-between; padding: 8px 20px;
  border-bottom: 1px solid #f3f4f6; color: #4b5563; font-size: 14px;
}
.detail-row:last-child { border-bottom: none; }
.time { color: #10b981; }

.modal-footer {
  padding: 0 20px 20px;
}
.btn-confirm {
  width: 100%; background: #1f2937; color: white;
  padding: 15px; border: none; border-radius: 12px;
  font-size: 16px; font-weight: bold; cursor: pointer;
  transition: 0.2s;
}
.btn-confirm:hover { background: #374151; transform: translateY(-2px); }

@keyframes popIn { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>