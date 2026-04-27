import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.js',
    alias: {
      'framer-motion': path.resolve(__dirname, './src/__mocks__/framer-motion.jsx'),
    },
  },
})
