// Ruta protegida: sólo deja pasar a usuarios con sesión y correo verificado.
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute() {
  const { usuario, cargando, verificado } = useAuth()
  const ubicacion = useLocation()

  if (cargando) return <p className="cargando">Cargando…</p> // Aún no sabemos si hay sesión
  if (!usuario || !verificado) {
    // Sin sesión (o correo sin verificar) → login, recordando a dónde quería ir
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  }
  return <Outlet />
}
