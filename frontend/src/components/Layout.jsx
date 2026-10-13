// Estructura común de las páginas privadas: cabecera, pestañas y aviso médico.
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { usuario, salir } = useAuth()
  const navegar = useNavigate()

  const cerrarSesion = async () => {
    await salir()
    navegar('/login')
  }

  return (
    <div className="app">
      <header className="cabecera">
        <span className="marca">🧠 Riesgo de Stroke</span>
        <div className="usuario">
          <span title={usuario?.email}>{usuario?.displayName || usuario?.email}</span>
          <button className="btn btn-secundario" onClick={cerrarSesion}>
            Salir
          </button>
        </div>
      </header>

      {/* Pestañas principales */}
      <nav className="pestanas" aria-label="Secciones">
        <NavLink to="/nueva-consulta" className={({ isActive }) => (isActive ? 'pestana activa' : 'pestana')}>
          Nueva consulta
        </NavLink>
        <NavLink to="/historico" className={({ isActive }) => (isActive ? 'pestana activa' : 'pestana')}>
          Histórico
        </NavLink>
      </nav>

      <main className="contenido">
        <Outlet />
      </main>

      <footer className="pie">
        Resultado orientativo generado por un modelo estadístico. No sustituye la valoración de un profesional de la
        salud. Ante síntomas de alarma (debilidad súbita, dificultad para hablar, desviación de la boca) llama a
        emergencias.
      </footer>
    </div>
  )
}
