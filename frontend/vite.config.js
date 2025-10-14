
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { 
    host: '0.0.0.0', 
    port: 3000, 
    allowedHosts: ['browserautomation.duckdns.org', 'localhost', '127.0.0.1'],
    proxy: { '/api': 'http://backend:8000' } 
  }
})
