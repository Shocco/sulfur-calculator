import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'production' ? '/sulfur-calculator/' : '/',
  build: {
    outDir: 'docs'
  },
  server: {
    port: 5173,
    open: false
  }
}))
