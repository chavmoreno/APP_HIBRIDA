# Manual de usuario

**Riesgo de Stroke** estima la probabilidad de sufrir un derrame cerebral (ictus) a partir de datos de
salud básicos. Es una herramienta **orientativa**: no es un diagnóstico médico.

> ⚠️ Si tú u otra persona presentan de forma súbita debilidad o adormecimiento de un lado del cuerpo,
> dificultad para hablar, boca desviada, pérdida de visión o dolor de cabeza intenso, **llama a emergencias de inmediato**.

## 1. Crear una cuenta e iniciar sesión

Abre <https://app-hibrida-511815.web.app> (siempre empieza por `https://`).

**Con Google (Gmail):** pulsa **Continuar con Google** y elige tu cuenta.

**Con correo y contraseña:**

1. Pulsa **¿No tienes cuenta? Regístrate**.
2. Escribe tu correo y una contraseña de al menos 8 caracteres (dos veces) y pulsa **Crear cuenta**.
3. Recibirás un correo de verificación. Abre el enlace y vuelve a la aplicación.
4. Pulsa **Ya verifiqué**. Si no te llegó, revisa *spam* o pulsa **Reenviar correo**.

¿Olvidaste la contraseña? Escribe tu correo y pulsa **Olvidé mi contraseña**: recibirás un enlace para cambiarla.

## 2. Pestaña «Nueva consulta»

Completa el formulario:

| Campo | Qué poner |
|---|---|
| Sexo | Mujer / Hombre |
| Edad | En años |
| ¿Hipertensión? | Si un médico te diagnosticó presión alta |
| ¿Enfermedad cardíaca? | Si tienes alguna enfermedad del corazón diagnosticada |
| ¿Alguna vez casado/a? | Sí / No |
| Tipo de trabajo | Sector privado, independiente, sector público, menor de edad o nunca ha trabajado |
| Residencia | Urbana / Rural |
| Tabaquismo *(opcional)* | Nunca, exfumador/a, fuma actualmente o prefiero no decirlo |
| Glucosa promedio *(opcional)* | En mg/dL (aparece en tus análisis de sangre) |
| Índice de masa corporal *(opcional)* | Peso (kg) ÷ estatura² (m). Ej.: 70 kg y 1,70 m → 24,2 |

Si no conoces un dato opcional, déjalo vacío: el modelo usará el valor típico de la población.

Pulsa **Calcular riesgo**. A la derecha verás:

- **Probabilidad** estimada (por ejemplo, `8.4 %`).
- **Nivel de riesgo**, comparado con la frecuencia de derrames en los datos de entrenamiento (~5 %):

| Nivel | Probabilidad | Color |
|---|---|---|
| Bajo | menor a 5 % | Verde |
| Moderado | 5 % – 15 % | Naranja |
| Alto | 15 % o más | Rojo |

Cada consulta se guarda automáticamente en tu histórico (si en ese momento la base de datos está apagada, verás el
resultado igual, pero la app avisará que no se guardó). **Limpiar** vacía el formulario.

## 3. Pestaña «Histórico»

Muestra todas tus consultas, de la más reciente a la más antigua: fecha, edad, sexo, probabilidad y nivel.
Pulsa **Ver datos** para ver lo que capturaste en esa consulta. Usa **Anterior / Siguiente** para cambiar de página.
Sólo tú puedes ver tus consultas.

## 4. Mensajes que puedes ver

| Pantalla / mensaje | Qué significa | Qué hacer |
|---|---|---|
| **401 – Tu sesión no es válida** | La sesión expiró o se cerró en otro dispositivo | Inicia sesión de nuevo |
| **404 – Página no encontrada** | La dirección no existe | Vuelve al inicio |
| **500 – Error del servidor** | Falló algo de nuestro lado; ya quedó registrado | Inténtalo más tarde; si persiste, comparte la *Referencia* |
| «El servicio de predicción no está disponible» | El servidor del modelo está apagado o en mantenimiento | Inténtalo más tarde |
| «Algo salió mal» | Error inesperado en la página; ya quedó registrado | Pulsa **Volver al inicio** |

## 5. Cerrar sesión

Pulsa **Salir** arriba a la derecha. Hazlo siempre en computadoras compartidas.

## 6. Panel de administración (sólo administradores)

Los correos configurados como administradores pueden abrir `/admin` para ver el resumen de errores de las
últimas 24 horas y el listado filtrable por severidad. Los errores **CRITICAL** también llegan por Telegram o correo.

## 7. Privacidad

- Tus datos viajan siempre cifrados (HTTPS).
- Las consultas se guardan asociadas a tu identificador de usuario, no a tu nombre.
- Los registros de errores no guardan tus datos de salud ni tu dirección IP en claro.
