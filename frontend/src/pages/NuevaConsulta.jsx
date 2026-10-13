// Pestaña "Nueva consulta": formulario de datos clínicos y resultado de la predicción.
import { useState } from 'react'
import ResultadoCard from '../components/ResultadoCard'
import { RESIDENCIA, SEXO, SI_NO, TABAQUISMO, TIPO_TRABAJO } from '../constants'
import { crearConsulta } from '../services/api'
import { useManejarErrorApi } from '../services/useManejarErrorApi'

// Valores iniciales del formulario (cadenas vacías = sin responder)
const INICIAL = {
  gender: '',
  age: '',
  hypertension: '',
  heart_disease: '',
  ever_married: '',
  work_type: '',
  residence_type: '',
  avg_glucose_level: '',
  bmi: '',
  smoking_status: '',
}

/** Valida en el navegador (el backend vuelve a validar todo). Devuelve {campo: mensaje}. */
function validar(f) {
  const e = {}
  for (const campo of ['gender', 'age', 'hypertension', 'heart_disease', 'ever_married', 'work_type', 'residence_type']) {
    if (f[campo] === '') e[campo] = 'Obligatorio'
  }
  if (f.age !== '' && (Number(f.age) < 0 || Number(f.age) > 120)) e.age = 'Entre 0 y 120'
  if (f.avg_glucose_level !== '' && (Number(f.avg_glucose_level) < 40 || Number(f.avg_glucose_level) > 400))
    e.avg_glucose_level = 'Entre 40 y 400 mg/dL'
  if (f.bmi !== '' && (Number(f.bmi) < 10 || Number(f.bmi) > 100)) e.bmi = 'Entre 10 y 100'
  return e
}

/** Convierte el estado del formulario al JSON que espera la API (vacíos opcionales → null). */
function aPayload(f) {
  return {
    gender: f.gender,
    age: Number(f.age),
    hypertension: f.hypertension === 'Yes',
    heart_disease: f.heart_disease === 'Yes',
    ever_married: f.ever_married,
    work_type: f.work_type,
    residence_type: f.residence_type,
    avg_glucose_level: f.avg_glucose_level === '' ? null : Number(f.avg_glucose_level),
    bmi: f.bmi === '' ? null : Number(f.bmi),
    smoking_status: f.smoking_status === '' ? null : f.smoking_status,
  }
}

// Campo <select> reutilizable
function Selector({ nombre, texto, opciones, valor, onChange, error, opcional }) {
  return (
    <label className={error ? 'con-error' : ''}>
      {texto} {opcional && <span className="opcional">(opcional)</span>}
      <select name={nombre} value={valor} onChange={onChange}>
        <option value="">Selecciona…</option>
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.etiqueta}
          </option>
        ))}
      </select>
      {error && <small>{error}</small>}
    </label>
  )
}

// Campo numérico reutilizable
function Numero({ nombre, texto, valor, onChange, error, opcional, ...resto }) {
  return (
    <label className={error ? 'con-error' : ''}>
      {texto} {opcional && <span className="opcional">(opcional)</span>}
      <input type="number" inputMode="decimal" name={nombre} value={valor} onChange={onChange} {...resto} />
      {error && <small>{error}</small>}
    </label>
  )
}

export default function NuevaConsulta() {
  const [form, setForm] = useState(INICIAL)
  const [errores, setErrores] = useState({})
  const [mensaje, setMensaje] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [consulta, setConsulta] = useState(null) // Última consulta realizada
  const manejarError = useManejarErrorApi()

  const cambiar = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const enviar = async (e) => {
    e.preventDefault()
    const errs = validar(form)
    setErrores(errs)
    if (Object.keys(errs).length) return
    setEnviando(true)
    setMensaje('')
    try {
      setConsulta(await crearConsulta(aPayload(form)))
    } catch (err) {
      const texto = manejarError(err)
      if (texto) setMensaje(err.requestId ? `${texto} (Ref.: ${err.requestId})` : texto)
    } finally {
      setEnviando(false)
    }
  }

  const props = (nombre) => ({ nombre, valor: form[nombre], onChange: cambiar, error: errores[nombre] })

  return (
    <div className="dos-columnas">
      <form className="tarjeta formulario" onSubmit={enviar} noValidate>
        <h2>Tus datos</h2>
        <div className="rejilla">
          <Selector texto="Sexo" opciones={SEXO} {...props('gender')} />
          <Numero texto="Edad (años)" min="0" max="120" step="1" {...props('age')} />
          <Selector texto="¿Hipertensión?" opciones={SI_NO} {...props('hypertension')} />
          <Selector texto="¿Enfermedad cardíaca?" opciones={SI_NO} {...props('heart_disease')} />
          <Selector texto="¿Alguna vez casado/a?" opciones={SI_NO} {...props('ever_married')} />
          <Selector texto="Tipo de trabajo" opciones={TIPO_TRABAJO} {...props('work_type')} />
          <Selector texto="Residencia" opciones={RESIDENCIA} {...props('residence_type')} />
          <Selector texto="Tabaquismo" opciones={TABAQUISMO} opcional {...props('smoking_status')} />
          <Numero texto="Glucosa promedio (mg/dL)" min="40" max="400" step="0.1" opcional {...props('avg_glucose_level')} />
          <Numero texto="Índice de masa corporal" min="10" max="100" step="0.1" opcional {...props('bmi')} />
        </div>
        <p className="nota">
          Si no conoces un dato opcional déjalo vacío: el modelo usará el valor típico de la población (mediana o moda).
        </p>
        {mensaje && <p className="alerta">{mensaje}</p>}
        <div className="acciones">
          <button className="btn" type="submit" disabled={enviando}>
            {enviando ? 'Calculando…' : 'Calcular riesgo'}
          </button>
          <button className="btn btn-secundario" type="button" onClick={() => { setForm(INICIAL); setErrores({}); setConsulta(null) }}>
            Limpiar
          </button>
        </div>
      </form>

      {consulta ? (
        <ResultadoCard consulta={consulta} />
      ) : (
        <section className="tarjeta vacio">
          <h2>Resultado</h2>
          <p>Completa el formulario y pulsa “Calcular riesgo” para ver tu probabilidad estimada.</p>
        </section>
      )}
    </div>
  )
}
