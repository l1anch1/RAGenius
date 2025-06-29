import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    open: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // 确保这个 URL 是正确的
        changeOrigin: true,
        secure: false,
      },
    },

  }
})