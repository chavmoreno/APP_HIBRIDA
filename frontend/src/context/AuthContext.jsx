// Contexto de autenticación: expone el usuario actual y las acciones de login/registro/logout.
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from 'firebase/auth'
import { auth, googleProvider } from '../firebase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null) // Usuario de Firebase o null
  const [cargando, setCargando] = useState(true) // true hasta conocer el estado inicial de la sesión
  const [verificado, setVerificado] = useState(false) // Copia de emailVerified (cambia tras reload())

  useEffect(() => {
    // Firebase avisa cada vez que cambia la sesión (login, logout, recarga de página)
    const cancelar = onAuthStateChanged(auth, (u) => {
      setUsuario(u)
      setVerificado(Boolean(u?.emailVerified))
      setCargando(false)
    })
    return cancelar
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      cargando,
      // Las cuentas de Google ya vienen verificadas; las de correo deben confirmar el enlace
      verificado,
      entrarConCorreo: (email, clave) => signInWithEmailAndPassword(auth, email, clave),
      registrarConCorreo: async (email, clave) => {
        const cred = await createUserWithEmailAndPassword(auth, email, clave)
        await sendEmailVerification(cred.user) // El backend exige correo verificado
        return cred
      },
      entrarConGoogle: () => signInWithPopup(auth, googleProvider),
      reenviarVerificacion: () => auth.currentUser && sendEmailVerification(auth.currentUser),
      recuperarClave: (email) => sendPasswordResetEmail(auth, email),
      recargarUsuario: async () => {
        await auth.currentUser?.reload() // Refresca emailVerified tras pulsar el enlace del correo
        await auth.currentUser?.getIdToken(true) // Fuerza un token nuevo con email_verified=true
        setVerificado(Boolean(auth.currentUser?.emailVerified))
      },
      salir: () => signOut(auth),
    }),
    [usuario, cargando, verificado],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

/** Hook para usar el contexto de autenticación. */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}
