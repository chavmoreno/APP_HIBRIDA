// Configuración de Vite. Si existen certificados en infra/certs (los genera la VM), `npm run dev` también usa HTTPS.
import fs from 'node:fs'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const CERT = '../infra/certs/localhost.pem'
const KEY = '../infra/certs/localhost-key.pem'
// Si existen los certificados locales, el servidor de desarrollo arranca en https://localhost:5173
const https = fs.existsSync(CERT) && fs.existsSync(KEY) ? { cert: fs.readFileSync(CERT), key: fs.readFileSync(KEY) } : undefined

export default defineConfig({
  plugins: [react()],
  server: { https, port: 5173, strictPort: true },
  build: { sourcemap: false }, // No se publican los fuentes en producción
})
