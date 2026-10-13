// Opciones del formulario: el valor es el que espera el modelo (dataset de Kaggle), la etiqueta va en español.

export const SEXO = [
  { valor: 'Female', etiqueta: 'Mujer' },
  { valor: 'Male', etiqueta: 'Hombre' },
]

export const SI_NO = [
  { valor: 'Yes', etiqueta: 'Sí' },
  { valor: 'No', etiqueta: 'No' },
]

export const TIPO_TRABAJO = [
  { valor: 'Private', etiqueta: 'Sector privado' },
  { valor: 'Self-employed', etiqueta: 'Independiente' },
  { valor: 'Govt_job', etiqueta: 'Sector público' },
  { valor: 'children', etiqueta: 'Menor de edad (niño/a)' },
  { valor: 'Never_worked', etiqueta: 'Nunca ha trabajado' },
]

export const RESIDENCIA = [
  { valor: 'Urban', etiqueta: 'Urbana' },
  { valor: 'Rural', etiqueta: 'Rural' },
]

export const TABAQUISMO = [
  { valor: 'never smoked', etiqueta: 'Nunca ha fumado' },
  { valor: 'formerly smoked', etiqueta: 'Exfumador/a' },
  { valor: 'smokes', etiqueta: 'Fuma actualmente' },
  { valor: 'Unknown', etiqueta: 'Prefiero no decirlo / no sé' },
]

export const NIVEL_RIESGO = {
  bajo: { etiqueta: 'Bajo', clase: 'riesgo-bajo' },
  moderado: { etiqueta: 'Moderado', clase: 'riesgo-moderado' },
  alto: { etiqueta: 'Alto', clase: 'riesgo-alto' },
}

/** Devuelve la etiqueta en español de un valor del dataset. */
export function etiqueta(lista, valor) {
  return lista.find((o) => o.valor === valor)?.etiqueta ?? (valor == null ? 'No informado' : valor)
}

/** Formatea una probabilidad 0..1 como porcentaje con un decimal. */
export const porcentaje = (p) => `${(p * 100).toFixed(1)} %`
