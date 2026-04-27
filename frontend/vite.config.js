import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['framer-motion'],
  },
  server: {
    proxy: {
      '/api': {
        // 127.0.0.1 avoids Node resolving localhost -> ::1 while uvicorn binds IPv4 (ECONNREFUSED).
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
