import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/dashboard/',
  server: {
    proxy: {
      '/control': 'http://localhost:8000',
      '/runs': 'http://localhost:8000',
      '/artifacts': 'http://localhost:8000',
      '/graphdash': 'http://localhost:8000',
      '/execution': 'http://localhost:8000',
      '/telemetry': 'http://localhost:8000',
    }
  },
  build: {
    minify: 'terser'
  }
})
