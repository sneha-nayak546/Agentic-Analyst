import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    port: 3000,
    strictPort: true,
    proxy: {
      '/query': 'http://127.0.0.1:8000',
      '/schema': 'http://127.0.0.1:8000',
      '/history': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/export': 'http://127.0.0.1:8000',
      '/api': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000'
    }
  },
  build: {
    outDir: '../app/static',
    emptyOutDir: true,
  }
})

