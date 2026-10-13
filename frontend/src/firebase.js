// Inicialización de Firebase Authentication (correo/contraseña y Google).
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, browserLocalPersistence, setPersistence } from 'firebase/auth'

// La configuración web de Firebase se inyecta en build desde variables VITE_* (.env.local)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

export const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
auth.languageCode = 'es' // Correos de verificación / recuperación en español

// La sesión persiste en el navegador hasta que el usuario cierre sesión
setPersistence(auth, browserLocalPersistence)

// Proveedor de Google: siempre muestra el selector de cuenta
export const googleProvider = new GoogleAuthProvider()
googleProvider.setCustomParameters({ prompt: 'select_account' })
