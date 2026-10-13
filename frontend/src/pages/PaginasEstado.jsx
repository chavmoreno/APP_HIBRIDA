// Páginas de estado: 404 (no existe), 401 (sesión inválida) y 500 (error del servidor).
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Plantilla común para las páginas de estado. */
function PaginaEstado({ codigo, titulo, children }) {
  return (
    <main className="pagina-estado">
      <p className="codigo">{codigo}</p>
      <h1>{titulo}</h1>
      {children}
    </main>
  )
}

export function NoEncontrada() {
  return (
    <PaginaEstado codigo="404" titulo="Página no encontrada">
      <p>La dirección que buscas no existe.</p>
      <Link className="btn" to="/">
        Ir al inicio
      </Link>
    </PaginaEstado>
  )
}

export function NoAutorizado() {
  const { salir } = useAuth()
  return (
    <PaginaEstado codigo="401" titulo="Tu sesión no es válida">
      <p>La sesión expiró o fue revocada. Vuelve a iniciar sesión.</p>
      <Link className="btn" to="/login" onClick={salir}>
        Iniciar sesión
      </Link>
    </PaginaEstado>
  )
}

export function ErrorServidor() {
  const { state } = useLocation()
  return (
    <PaginaEstado codigo="500" titulo="Error del servidor">
      <p>Algo falló de nuestro lado. El incidente quedó registrado.</p>
      {state?.requestId && (
        <p className="nota">
          Referencia para soporte: <code>{state.requestId}</code>
        </p>
      )}
      <Link className="btn" to="/">
        Volver al inicio
      </Link>
    </PaginaEstado>
  )
}
