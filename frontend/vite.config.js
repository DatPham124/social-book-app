import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(),  tailwindcss()],
  server: {
    host: true, // Hoặc gõ '0.0.0.0'
    port: 5173, // (Tùy chọn) Giữ cố định port
  }
})