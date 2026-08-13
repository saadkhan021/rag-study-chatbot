import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  preview: {
    // Railway sets $PORT and expects the app to bind 0.0.0.0 there.
    // allowedHosts: true lets vite preview accept Railway's public
    // *.up.railway.app hostname (it validates the Host header by default).
    allowedHosts: true,
  },
})
