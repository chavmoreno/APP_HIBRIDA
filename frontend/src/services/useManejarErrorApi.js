// Hook que decide qué hacer con un ApiError: redirigir a 401/500 o devolver un mensaje para mostrar.
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

export function useManejarErrorApi() {
  const navegar = useNavigate()

  return useCallback(
    (error) => {
      if (error?.status === 401) {
        navegar('/401', { replace: true }) // Sesión inválida o expirada
        return null
      }
      if (error?.status >= 500 && error?.status !== 503) {
        navegar('/500', { replace: true, state: { requestId: error.requestId } })
        return null
      }
      // 403, 422, 503 o sin conexión: se muestra en la propia página
      return error?.message || 'Ocurrió un error inesperado'
    },
    [navegar],
  )
}
