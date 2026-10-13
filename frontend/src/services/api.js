// Cliente HTTP del API Gateway: añade el token de Firebase, el X-Request-ID y normaliza los errores.
import { auth } from '../firebase'

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

// Política HTTPS exclusiva: nunca se envían datos a una URL http://
if (!API_URL.startsWith('https://')) {
  console.error('VITE_API_URL debe empezar por https://')
}

/** Error de la API con código HTTP y request-id para soporte. */
export class ApiError extends Error {
  constructor(status, mensaje, requestId, detalles) {
    super(mensaje)
    this.name = 'ApiError'
    this.status = status
    this.requestId = requestId
    this.detalles = detalles
  }
}

/** Genera un identificador único por petición (se correlaciona con los logs del backend). */
export function nuevoRequestId() {
  return crypto.randomUUID()
}

/**
 * Llama al API Gateway.
 * @param {string} ruta - p. ej. '/api/consultas'
 * @param {{method?: string, body?: any, autenticado?: boolean}} opciones
 */
export async function apiFetch(ruta, { method = 'GET', body, autenticado = true } = {}) {
  if (!API_URL.startsWith('https://')) {
    throw new ApiError(0, 'Configuración insegura: la API debe usar HTTPS')
  }
  const requestId = nuevoRequestId()
  const headers = { 'X-Request-ID': requestId }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  if (autenticado) {
    const usuario = auth.currentUser
    if (!usuario) throw new ApiError(401, 'No hay sesión iniciada', requestId)
    // getIdToken() renueva el token automáticamente si está por expirar
    headers.Authorization = `Bearer ${await usuario.getIdToken()}`
  }

  let respuesta
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: 'omit', // No se usan cookies
      cache: 'no-store', // Datos de salud: sin caché
    })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor. Revisa tu conexión.', requestId)
  }

  if (respuesta.status === 204) return null
  const datos = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    const err = datos?.error || {}
    throw new ApiError(
      respuesta.status,
      err.mensaje || `Error ${respuesta.status}`,
      err.request_id || respuesta.headers.get('X-Request-ID') || requestId,
      err.detalles,
    )
  }
  return datos
}

// ---- Endpoints de la aplicación ----
export const crearConsulta = (datos) => apiFetch('/api/consultas', { method: 'POST', body: datos })
export const listarConsultas = (limit = 10, offset = 0) => apiFetch(`/api/consultas?limit=${limit}&offset=${offset}`)
export const listarErroresAdmin = (params = '') => apiFetch(`/api/admin/errores${params}`)
export const resumenErroresAdmin = () => apiFetch('/api/admin/errores/resumen')
