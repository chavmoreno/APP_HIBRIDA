// Inicializa Swagger UI con las dos especificaciones OpenAPI generadas desde el código.
// El selector superior alterna entre la API pública (gateway) y el microservicio interno de inferencia.
window.ui = SwaggerUIBundle({
  urls: [
    { url: 'openapi-gateway.json', name: 'API Gateway (pública)' },
    { url: 'openapi-inferencia.json', name: 'Microservicio de inferencia (interno, sólo dentro de la VM)' },
  ],
  dom_id: '#swagger-ui',
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
  layout: 'StandaloneLayout',
  persistAuthorization: false, // No guarda el token en el navegador
  validatorUrl: null, // Sin validador externo (la CSP sólo permite conexiones a la propia API)
})
