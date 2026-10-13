// Tarjeta que muestra el resultado de una consulta: probabilidad, nivel de riesgo y explicación.
import { NIVEL_RIESGO, porcentaje } from '../constants'

export default function ResultadoCard({ consulta }) {
  const { resultado } = consulta
  const nivel = NIVEL_RIESGO[resultado.nivel_riesgo]

  return (
    <section className={`tarjeta resultado ${nivel.clase}`} aria-live="polite">
      <h2>Resultado</h2>
      <p className="probabilidad">{porcentaje(resultado.probabilidad)}</p>
      <p>
        Probabilidad estimada de derrame cerebral · Riesgo <strong>{nivel.etiqueta}</strong>
      </p>
      {/* Barra visual de la probabilidad */}
      <div className="barra" role="img" aria-label={`Probabilidad ${porcentaje(resultado.probabilidad)}`}>
        <div className="barra-relleno" style={{ width: `${Math.max(2, resultado.probabilidad * 100)}%` }} />
      </div>
      <p className="nota">
        Las bandas comparan tu estimación con la prevalencia del conjunto de entrenamiento (~5 %): bajo &lt; 5 %,
        moderado 5–15 %, alto ≥ 15 %. Modelo {resultado.modelo_version}.
      </p>
      {!consulta.guardada && (
        <p className="alerta">No pudimos guardar esta consulta en tu histórico. Ref.: {consulta.request_id}</p>
      )}
    </section>
  )
}
