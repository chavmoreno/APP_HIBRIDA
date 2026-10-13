// Punto de entrada: monta la app con el ErrorBoundary, el router y el contexto de autenticación.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import { AuthProvider } from './context/AuthContext'
import { instalarCapturaGlobal } from './services/errorReporter'
import './styles.css'

// Defensa extra: si alguien abre la app por http:// fuera de localhost, se fuerza https://
if (window.location.protocol === 'http:' && window.location.hostname !== 'localhost') {
  window.location.replace(window.location.href.replace(/^http:/, 'https:'))
}

// Errores JS fuera de React (window.onerror, promesas sin catch) → POST /api/errores
instalarCapturaGlobal()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
)
