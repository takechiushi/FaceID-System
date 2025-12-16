<template>
  <div class="app-wrapper">
    <router-view />
  </div>
</template>

<script setup>
// Không cần code logic gì ở đây cả, Router sẽ lo hết.
</script>

<style>
/* CSS toàn cục cho cả ứng dụng */
body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f4f6f8;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.app-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  justify-content: center;
}

/* Style chung cho các nút bấm để đẹp hơn */
button {
  cursor: pointer;
  transition: background 0.3s;
  border-radius: 4px;
}

button:disabled {
  background: #ccc !important;
  cursor: not-allowed;
}

a {
  color: #42b983;
  text-decoration: none;
  margin-top: 15px;
  display: inline-block;
}

a:hover {
  text-decoration: underline;
}

input {
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}
</style>