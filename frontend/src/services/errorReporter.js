// Envía errores de JavaScript a POST /api/errores para que queden en errores_db.
import { apiFetch } from './api'
import { auth } from '../firebase'

let enviadosEnSesion = 0
const MAX_POR_SESION = 20 // Evita bucles que inunden el log

/**
 * Reporta un error al backend. Nunca lanza excepciones (reportar no debe romper la app).
 * @param {Error|any} error
 * @param {{severidad?: string, contexto?: object}} extra
 */
export async function reportarError(error, { severidad = 'ERROR', contexto } = {}) {
  if (enviadosEnSesion >= MAX_POR_SESION) return
  enviadosEnSesion += 1
  try {
    await apiFetch('/api/errores', {
      method: 'POST',
      autenticado: Boolean(auth.currentUser), // Con sesión se asocia el uid; sin sesión también se acepta
      body: {
        mensaje: String(error?.message || error || 'Error desconocido').slice(0, 2000),
        tipo: String(error?.name || 'Error').slice(0, 120),
        stack: error?.stack ? String(error.stack).slice(0, 8000) : null,
        ruta: window.location.pathname.slice(0, 255),
        severidad,
        contexto: { userAgent: navigator.userAgent.slice(0, 200), ...contexto },
      },
    })
  } catch {
    // Si el backend no responde, no hay nada más que hacer
  }
}

/** Captura errores globales no controlados y promesas rechazadas sin catch. */
export function instalarCapturaGlobal() {
  window.addEventListener('error', (evento) => {
    reportarError(evento.error || evento.message, { contexto: { origen: 'window.onerror' } })
  })
  window.addEventListener('unhandledrejection', (evento) => {
    reportarError(evento.reason, { contexto: { origen: 'unhandledrejection' } })
  })
}
