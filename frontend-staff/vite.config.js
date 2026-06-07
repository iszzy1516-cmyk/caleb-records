import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/staff/',
  server: {
    port: 5174,
    strictPort: true,
  },
})
