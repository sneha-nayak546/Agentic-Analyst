import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/',
  server: {
    port: 3000,
    strictPort: true,
  },
  build: {
    outDir: '../app/static',
    emptyOutDir: true,
  }
})
