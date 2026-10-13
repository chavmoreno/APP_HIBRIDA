// Panel de administración: resumen y listado del log de errores (sólo correos en ADMIN_EMAILS del backend).
import { useEffect, useState } from 'react'
import { listarErroresAdmin, resumenErroresAdmin } from '../services/api'
import { useManejarErrorApi } from '../services/useManejarErrorApi'

export default function Admin() {
  const [resumen, setResumen] = useState([])
  const [errores, setErrores] = useState(null)
  const [severidad, setSeveridad] = useState('')
  const [mensaje, setMensaje] = useState('')
  const manejarError = useManejarErrorApi()

  useEffect(() => {
    const filtro = severidad ? `?severidad=${severidad}&limit=50` : '?limit=50'
    Promise.all([resumenErroresAdmin(), listarErroresAdmin(filtro)])
      .then(([r, e]) => {
        setResumen(r)
        setErrores(e)
      })
      .catch((err) => setMensaje(err.status === 403 ? 'No tienes permisos de administrador.' : manejarError(err)))
  }, [severidad, manejarError])

  if (mensaje) return <p className="alerta">{mensaje}</p>
  if (!errores) return <p className="cargando">Cargando…</p>

  return (
    <section className="tarjeta">
      <h2>Errores (últimas 24 h)</h2>
      <div className="resumen">
        {resumen.length === 0 && <p>Sin errores en las últimas 24 horas. 🎉</p>}
        {resumen.map((r) => (
          <span key={`${r.origen}-${r.severidad}`} className={`etiqueta sev-${r.severidad}`}>
            {r.origen} · {r.severidad}: {r.total}
          </span>
        ))}
      </div>
      <label className="filtro">
        Severidad
        <select value={severidad} onChange={(e) => setSeveridad(e.target.value)}>
          <option value="">Todas</option>
          {['CRITICAL', 'ERROR', 'WARNING', 'INFO'].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>
      <div className="tabla-scroll">
        <table>
          <thead>
            <tr>
              <th>Fecha</th><th>Origen</th><th>Severidad</th><th>HTTP</th><th>Tipo</th><th>Mensaje</th><th>Request-ID</th>
            </tr>
          </thead>
          <tbody>
            {errores.items.map((e) => (
              <tr key={e.id}>
                <td>{new Date(e.creado_en).toLocaleString('es')}</td>
                <td>{e.origen}</td>
                <td><span className={`etiqueta sev-${e.severidad}`}>{e.severidad}</span></td>
                <td>{e.codigo_http ?? '-'}</td>
                <td>{e.tipo}</td>
                <td className="mensaje">{e.mensaje}</td>
                <td><code>{e.request_id}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
