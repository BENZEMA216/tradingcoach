import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // 拆 vendor chunk：图表库 + i18n + 数据层独立，
    // 避免单文件 >500KB 的 chunkSizeWarning，并改善冷加载缓存命中率。
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts', 'lightweight-charts'],
          'vendor-i18n': ['i18next', 'react-i18next'],
          'vendor-query': ['@tanstack/react-query', 'axios'],
          'vendor-sentry': ['@sentry/react'],
        },
      },
    },
    chunkSizeWarningLimit: 700,
  },
})
