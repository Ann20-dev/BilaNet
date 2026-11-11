import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow access through ngrok tunnels when sharing for testing
    allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.app'],
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
