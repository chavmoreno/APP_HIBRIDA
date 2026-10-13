// Definición de rutas de la SPA.
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Admin from './pages/Admin'
import Historico from './pages/Historico'
import Login from './pages/Login'
import NuevaConsulta from './pages/NuevaConsulta'
import { ErrorServidor, NoAutorizado, NoEncontrada } from './pages/PaginasEstado'

export default function App() {
  return (
    <Routes>
      {/* Públicas */}
      <Route path="/login" element={<Login />} />
      <Route path="/401" element={<NoAutorizado />} />
      <Route path="/500" element={<ErrorServidor />} />

      {/* Privadas: requieren sesión y correo verificado */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/nueva-consulta" replace />} />
          <Route path="/nueva-consulta" element={<NuevaConsulta />} />
          <Route path="/historico" element={<Historico />} />
          <Route path="/admin" element={<Admin />} />
        </Route>
      </Route>

      {/* Cualquier otra ruta → 404 */}
      <Route path="*" element={<NoEncontrada />} />
    </Routes>
  )
}
