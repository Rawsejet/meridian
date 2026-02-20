import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'

export default defineConfig({
  css: {
    postcss: {
      plugins: [tailwindcss()],
    },
  },
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})