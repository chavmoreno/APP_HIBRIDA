// Pestaña "Histórico": lista paginada de las consultas del usuario con su resultado.
import { Fragment, useCallback, useEffect, useState } from 'react'
import { NIVEL_RIESGO, RESIDENCIA, SEXO, TABAQUISMO, TIPO_TRABAJO, etiqueta, porcentaje } from '../constants'
import { listarConsultas } from '../services/api'
import { useManejarErrorApi } from '../services/useManejarErrorApi'

const POR_PAGINA = 10
const fecha = (iso) => new Date(iso).toLocaleString('es', { dateStyle: 'medium', timeStyle: 'short' })
const siNo = (b) => (b ? 'Sí' : 'No')

export default function Historico() {
  const [pagina, setPagina] = useState(0)
  const [datos, setDatos] = useState(null) // {total, items}
  const [abierta, setAbierta] = useState(null) // id de la fila expandida
  const [mensaje, setMensaje] = useState('')
  const manejarError = useManejarErrorApi()

  const cargar = useCallback(async () => {
    setMensaje('')
    try {
      setDatos(await listarConsultas(POR_PAGINA, pagina * POR_PAGINA))
    } catch (err) {
      const texto = manejarError(err)
      if (texto) setMensaje(texto)
    }
  }, [pagina, manejarError])

  useEffect(() => {
    cargar()
  }, [cargar])

  if (mensaje) return <p className="alerta">{mensaje}</p>
  if (!datos) return <p className="cargando">Cargando histórico…</p>
  if (datos.total === 0) {
    return (
      <section className="tarjeta vacio">
        <h2>Histórico</h2>
        <p>Aún no tienes consultas. Ve a la pestaña “Nueva consulta” para hacer la primera.</p>
      </section>
    )
  }

  const paginas = Math.ceil(datos.total / POR_PAGINA)

  return (
    <section className="tarjeta">
      <h2>Histórico ({datos.total})</h2>
      <div className="tabla-scroll">
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Edad</th>
              <th>Sexo</th>
              <th>Probabilidad</th>
              <th>Riesgo</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {datos.items.map((c) => (
              <Fragment key={c.id}>
                <tr>
                  <td>{fecha(c.creado_en)}</td>
                  <td>{c.datos.age}</td>
                  <td>{etiqueta(SEXO, c.datos.gender)}</td>
                  <td>{porcentaje(c.resultado.probabilidad)}</td>
                  <td>
                    <span className={`etiqueta ${NIVEL_RIESGO[c.resultado.nivel_riesgo].clase}`}>
                      {NIVEL_RIESGO[c.resultado.nivel_riesgo].etiqueta}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-enlace" onClick={() => setAbierta(abierta === c.id ? null : c.id)}>
                      {abierta === c.id ? 'Ocultar' : 'Ver datos'}
                    </button>
                  </td>
                </tr>
                {abierta === c.id && (
                  <tr className="detalle">
                    <td colSpan={6}>
                      <dl>
                        <dt>Hipertensión</dt><dd>{siNo(c.datos.hypertension)}</dd>
                        <dt>Enf. cardíaca</dt><dd>{siNo(c.datos.heart_disease)}</dd>
                        <dt>Alguna vez casado/a</dt><dd>{c.datos.ever_married === 'Yes' ? 'Sí' : 'No'}</dd>
                        <dt>Trabajo</dt><dd>{etiqueta(TIPO_TRABAJO, c.datos.work_type)}</dd>
                        <dt>Residencia</dt><dd>{etiqueta(RESIDENCIA, c.datos.residence_type)}</dd>
                        <dt>Tabaquismo</dt><dd>{etiqueta(TABAQUISMO, c.datos.smoking_status)}</dd>
                        <dt>Glucosa</dt><dd>{c.datos.avg_glucose_level ?? 'No informado'}</dd>
                        <dt>IMC</dt><dd>{c.datos.bmi ?? 'No informado'}</dd>
                        <dt>Modelo</dt><dd>{c.resultado.modelo_version}</dd>
                      </dl>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      {paginas > 1 && (
        <div className="paginacion">
          <button className="btn btn-secundario" disabled={pagina === 0} onClick={() => setPagina(pagina - 1)}>
            ← Anterior
          </button>
          <span>
            Página {pagina + 1} de {paginas}
          </span>
          <button className="btn btn-secundario" disabled={pagina + 1 >= paginas} onClick={() => setPagina(pagina + 1)}>
            Siguiente →
          </button>
        </div>
      )}
    </section>
  )
}
