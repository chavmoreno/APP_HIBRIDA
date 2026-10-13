// ErrorBoundary: atrapa errores de renderizado de React, los reporta y muestra una pantalla amable.
import { Component } from 'react'
import { reportarError } from '../services/errorReporter'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hayError: false }
  }

  // Cambia el estado para mostrar la interfaz de respaldo en el siguiente render
  static getDerivedStateFromError() {
    return { hayError: true }
  }

  // Envía el error y la pila de componentes a POST /api/errores
  componentDidCatch(error, info) {
    reportarError(error, {
      severidad: 'ERROR',
      contexto: { origen: 'ErrorBoundary', componentStack: info?.componentStack?.slice(0, 2000) },
    })
  }

  render() {
    if (this.state.hayError) {
      return (
        <main className="pagina-estado">
          <h1>Algo salió mal</h1>
          <p>Ocurrió un error inesperado en la aplicación. Ya lo registramos para revisarlo.</p>
          <button className="btn" onClick={() => window.location.assign('/')}>
            Volver al inicio
          </button>
        </main>
      )
    }
    return this.props.children
  }
}
