<template>
  <div class="dashboard-container" v-if="user">
    <div class="id-card">
      <div class="card-header">
        <h3>THẺ NHÂN VIÊN</h3>
        <div class="chip">VERIFIED</div>
      </div>
      
      <div class="avatar-wrapper">
        <img :src="user.avatar_url" alt="Avatar" />
      </div>

      <div class="info-body">
        <h2 class="name">{{ user.name }}</h2>
        <p class="role">Thành viên chính thức</p>
        
        <div class="stats">
          <div class="stat-item">
            <span class="label">TUỔI</span>
            <span class="value">{{ user.age }}</span>
          </div>
          <div class="stat-item">
            <span class="label">ID HỆ THỐNG</span>
            <span class="value code">{{ user._id.substring(0, 8) }}...</span>
          </div>
        </div>
      </div>

      <button @click="logout" class="btn-logout">Đăng xuất</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = ref(null);

onMounted(() => {
  const storedUser = localStorage.getItem('user');
  if (storedUser) user.value = JSON.parse(storedUser);
  else router.push('/');
});

const logout = () => {
  localStorage.removeItem('user');
  router.push('/');
};
</script>

<style scoped>
.dashboard-container {
  animation: fadeIn 0.5s ease;
}

.id-card {
  background: white;
  width: 350px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0,0,0,0.2);
  text-align: center;
  position: relative;
}

.card-header {
  background: var(--bg-gradient);
  padding: 20px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h3 { margin: 0; font-size: 14px; letter-spacing: 1px; opacity: 0.9; }

.chip {
  background: rgba(255,255,255,0.2);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
}

.avatar-wrapper {
  margin-top: -50px;
  position: relative;
  display: inline-block;
}
.avatar-wrapper img {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 5px solid white;
  object-fit: cover;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.info-body { padding: 20px 30px; }
.name { margin: 10px 0 5px; color: #333; font-size: 24px; }
.role { color: #888; font-size: 14px; margin-bottom: 25px; }

.stats {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid #eee;
  padding-top: 20px;
}
.stat-item { display: flex; flex-direction: column; text-align: left; }
.stat-item .label { font-size: 10px; color: #999; font-weight: bold; margin-bottom: 3px; }
.stat-item .value { font-size: 16px; font-weight: bold; color: #333; }
.code { font-family: monospace; color: var(--primary-color); }

.btn-logout {
  width: 100%;
  padding: 15px;
  border: none;
  background: #f3f4f6;
  color: #666;
  font-weight: bold;
  cursor: pointer;
  border-top: 1px solid #eee;
}
.btn-logout:hover { background: #fee2e2; color: #ef4444; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>