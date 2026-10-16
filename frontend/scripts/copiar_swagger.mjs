// Antes de cada build (script "prebuild"): copia la documentación Swagger de docs/api y los archivos de
// Swagger UI (paquete swagger-ui-dist) a public/swagger, para publicarla junto a la app en /swagger/.
import { cpSync, mkdirSync } from 'node:fs'

const DESTINO = 'public/swagger'
mkdirSync(DESTINO, { recursive: true })

// Especificaciones OpenAPI, index.html y swagger-init.js (el README es para el repositorio, no se publica)
cpSync('../docs/api', DESTINO, { recursive: true, filter: (ruta) => !ruta.endsWith('README.md') })

// Swagger UI servido desde el mismo sitio: la CSP de Firebase Hosting no permite cargarlo de un CDN
for (const archivo of ['swagger-ui.css', 'swagger-ui-bundle.js', 'swagger-ui-standalone-preset.js']) {
  cpSync(`node_modules/swagger-ui-dist/${archivo}`, `${DESTINO}/${archivo}`)
}

console.log(`Swagger copiado a ${DESTINO}`)
