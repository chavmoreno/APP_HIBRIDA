// Página de acceso: iniciar sesión / crear cuenta con correo y contraseña, o entrar con Google (Gmail).
import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Traduce los códigos de error de Firebase a mensajes claros en español
const MENSAJES_FIREBASE = {
  'auth/invalid-credential': 'Correo o contraseña incorrectos.',
  'auth/invalid-email': 'El correo no es válido.',
  'auth/email-already-in-use': 'Ya existe una cuenta con ese correo. Inicia sesión.',
  'auth/weak-password': 'La contraseña debe tener al menos 8 caracteres.',
  'auth/too-many-requests': 'Demasiados intentos. Espera unos minutos.',
  'auth/popup-closed-by-user': 'Cerraste la ventana de Google antes de terminar.',
  'auth/network-request-failed': 'Sin conexión con Firebase. Revisa tu internet.',
}
const mensajeFirebase = (e) => MENSAJES_FIREBASE[e?.code] || 'No se pudo completar la operación.'

export default function Login() {
  const auth = useAuth()
  const ubicacion = useLocation()
  const [modo, setModo] = useState('entrar') // 'entrar' | 'registrar'
  const [email, setEmail] = useState('')
  const [clave, setClave] = useState('')
  const [clave2, setClave2] = useState('')
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [ocupado, setOcupado] = useState(false)

  // Con sesión y correo verificado ya no tiene sentido estar aquí
  if (auth.usuario && auth.verificado) {
    return <Navigate to={ubicacion.state?.desde || '/nueva-consulta'} replace />
  }

  // Ejecuta una acción mostrando estado de carga y errores
  const ejecutar = async (accion) => {
    setError('')
    setAviso('')
    setOcupado(true)
    try {
      await accion()
    } catch (e) {
      setError(mensajeFirebase(e))
    } finally {
      setOcupado(false)
    }
  }

  const enviar = (e) => {
    e.preventDefault()
    if (modo === 'registrar') {
      if (clave.length < 8) return setError('La contraseña debe tener al menos 8 caracteres.')
      if (clave !== clave2) return setError('Las contraseñas no coinciden.')
      return ejecutar(async () => {
        await auth.registrarConCorreo(email, clave)
        setAviso('Cuenta creada. Te enviamos un correo de verificación: abre el enlace y vuelve aquí.')
      })
    }
    return ejecutar(() => auth.entrarConCorreo(email, clave))
  }

  // Sesión iniciada con correo pero sin verificar: se pide confirmar el enlace
  if (auth.usuario && !auth.verificado) {
    return (
      <main className="login">
        <section className="tarjeta">
          <h1>Verifica tu correo</h1>
          <p>
            Enviamos un enlace a <strong>{auth.usuario.email}</strong>. Ábrelo y luego pulsa “Ya verifiqué”.
          </p>
          {aviso && <p className="exito">{aviso}</p>}
          {error && <p className="alerta">{error}</p>}
          <div className="acciones">
            <button className="btn" disabled={ocupado} onClick={() => ejecutar(auth.recargarUsuario)}>
              Ya verifiqué
            </button>
            <button
              className="btn btn-secundario"
              disabled={ocupado}
              onClick={() => ejecutar(async () => {
                await auth.reenviarVerificacion()
                setAviso('Correo reenviado.')
              })}
            >
              Reenviar correo
            </button>
            <button className="btn btn-enlace" onClick={auth.salir}>
              Usar otra cuenta
            </button>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="login">
      <section className="tarjeta">
        <h1>🧠 Riesgo de Stroke</h1>
        <p className="subtitulo">{modo === 'entrar' ? 'Inicia sesión para continuar' : 'Crea tu cuenta'}</p>

        <button className="btn btn-google" disabled={ocupado} onClick={() => ejecutar(auth.entrarConGoogle)}>
          Continuar con Google
        </button>
        <div className="separador">o con tu correo</div>

        <form onSubmit={enviar} noValidate>
          <label>
            Correo electrónico
            <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              autoComplete={modo === 'entrar' ? 'current-password' : 'new-password'}
              required
              minLength={8}
              value={clave}
              onChange={(e) => setClave(e.target.value)}
            />
          </label>
          {modo === 'registrar' && (
            <label>
              Repite la contraseña
              <input type="password" autoComplete="new-password" required value={clave2} onChange={(e) => setClave2(e.target.value)} />
            </label>
          )}
          {error && <p className="alerta">{error}</p>}
          {aviso && <p className="exito">{aviso}</p>}
          <button className="btn" type="submit" disabled={ocupado}>
            {modo === 'entrar' ? 'Iniciar sesión' : 'Crear cuenta'}
          </button>
        </form>

        <div className="acciones-secundarias">
          {modo === 'entrar' ? (
            <>
              <button className="btn btn-enlace" onClick={() => setModo('registrar')}>
                ¿No tienes cuenta? Regístrate
              </button>
              <button
                className="btn btn-enlace"
                onClick={() => {
                  if (!email) return setError('Escribe tu correo para enviarte el enlace de recuperación.')
                  return ejecutar(async () => {
                    await auth.recuperarClave(email)
                    setAviso('Si el correo existe, recibirás un enlace para restablecer la contraseña.')
                  })
                }}
              >
                Olvidé mi contraseña
              </button>
            </>
          ) : (
            <button className="btn btn-enlace" onClick={() => setModo('entrar')}>
              ¿Ya tienes cuenta? Inicia sesión
            </button>
          )}
        </div>
      </section>
    </main>
  )
}
