# Cierre funcional de la Etapa 7: historial y contexto

La Etapa 7 queda implementada y comprobada en el alcance descrito aquí. La confirmación final del usuario fue **690 passed in 38.14s**, una entrevista nueva de cuatro preguntas y lectura validada del archivo 1.1.0. Este cierre no declara terminadas las pruebas ampliadas de consistencia de la Etapa 8 ni la validación final de la Etapa 9.

## Funcionalidad y evidencia

| Capacidad | Estado comprobado |
| --- | --- |
| Conservar conversación y referencias | Historial completo por sesión y pares recientes completos al preparar extractos; repregunta del usuario conservó Inventario Aula. |
| Identidad y aislamiento | UUID por ejecución, configuración copiada y sesiones independientes; pruebas automatizadas y comprobaciones manuales anteriores. |
| Límite y cierre | Máximo configurable hasta veinte envíos, incluidos fallos del candidato; límites y cierres comprobados con simulaciones. La ejecución final del usuario tuvo cuatro envíos. |
| Guardado y lectura | JSON local UTF-8, creación sin sobrescribir y validación de forma/relaciones. Formatos 1.0.0 y 1.1.0 legibles. |
| Proteger antecedentes | Perfil comprobado antes/después de llamadas y al finalizar; sus bytes y el hash de instrucciones coinciden con la procedencia del archivo final. |
| Medir contexto | Métricas informadas y reservas explícitas; se distingue información pasada de una predicción del siguiente envío. |
| Rechazar exceso | Controles de Ollama y error `context_limit`; el usuario confirmó rechazo, conservación del historial y repregunta posterior. |
| Preparar resumen | Selección de índices, citas literales verificables, anclas conservadas por Python y dos pares recientes completos por defecto. |
| Usar resumen en el controlador | Opción `--extractive-context`, activación por política y eventos separados del contador de preguntas. Una fixture identificada ejercitó el uso real de extractos y conservó referencias. |
| Recuperarse de fallos del selector | Respaldo con historial completo, interrupción antes del envío y protección de integridad; pruebas automatizadas con errores simulados. |

Las comprobaciones unitarias e integraciones usan proveedores simulados. Las llamadas reales y las fixtures están identificadas en sus evidencias; una fixture no se presenta como entrevista natural ni como medición real de sus datos predefinidos.

## Confirmación final del usuario

Archivo: [session-f8d281c9-bca7-4bdd-9b52-d7f9788399e5.json](../outputs/sessions/session-f8d281c9-bca7-4bdd-9b52-d7f9788399e5.json).

- Estado `closed`, motivo `user_exit`, integridad `unchanged` y versión **1.1.0**.
- Cuatro preguntas enviadas y cuatro respuestas `completed`.
- Cero incidencias técnicas.
- Cuatro preparaciones; tres selectores `not_requested` y el cuarto `completed`.
- Una selección de memoria y cero resúmenes aplicados, porque las citas antiguas se conservaron completas.
- Preparación final `full_history` por `no_omissions`, con **27 951 → 27 951 bytes** de mensajes generales.
- Latencias comunicadas: **67,15; 7,51; 7,37 y 3,45 s** para el candidato; **4,58 s** adicionales de preparación en la cuarta pregunta.

El candidato conservó Inventario Aula, sus tecnologías y el total de 21 meses calendario incluyendo práctica. La cuarta respuesta conservó la referencia correcta, aunque su expresión «mi primera pregunta» puede afinarse a «mi primera respuesta». Se registra como observación de redacción para la revisión posterior, sin convertirla en un fallo técnico o afirmar que se alteró el antecedente.

La lectura local reprodujo los estados y la auditoría comunicados, sin modificar el archivo. La confirmación estructurada está en [live-context-user-confirmation-209e77b7567a4699827786bb493d3e7c.json](../outputs/results/live-context-user-confirmation-209e77b7567a4699827786bb493d3e7c.json). Distingue el resultado del usuario de la lectura local y conserva los hashes.

## Uso normal

Con las variables locales y el modelo ya seleccionados, desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview --extractive-context
```

El umbral normal del cliente actual es **7424 tokens de entrada informada**. El valor **1** de la prueba final fue un ajuste deliberado para ejercitar la selección en una conversación breve; no modifica el valor normal. Sin `--extractive-context` se mantiene la ruta anterior.

La opción sigue siendo explícita. Ollama es el proveedor principal; la API externa permanece como alternativa de activación explícita y no se utilizó en estas pruebas reales. Perfil, puesto, configuración aprobada, referencia **2026-10-20**, máximo **20** e instrucciones **1.0.11** se conservan.

## Límites que pasan a la validación posterior

Los estados `completed` y los hashes no certifican la verdad de todas las respuestas. La selección de citas puede omitir contexto importante pese a las anclas; su estado `not_reviewed` no se convierte en una revisión humana. El ahorro de bytes no equivale automáticamente al de tokens y el umbral se basa en llamadas pasadas.

No se garantiza que veinte preguntas arbitrariamente extensas quepan en la capacidad disponible. No se han validado exhaustivamente entrevistas naturales de veinte turnos ni todas las variaciones de modelo. La primera llamada y la preparación pueden tardar; las observaciones aisladas no prueban una latencia garantizada o una mejora de rendimiento.

La clasificación de preguntas, la rúbrica, puntuaciones, niveles y retroalimentación educativa continúan fuera de esta fase. Este cierre no incorpora esos componentes.

## Propuesta de transición a la Etapa 8

La instrucción inicial del usuario indica: «No avances automáticamente entre etapas». Tras este cierre, el usuario autorizó explícitamente la transición con «Pasemos a la etapa 8 también muéstrame que etapas completamos y cuantas faltan». Se inició la [unidad 8.1](pruebas/referencias-consistencia.md). El [estado de las nueve etapas](estado-etapas.md) registra siete completadas y dos por terminar.

La primera unidad propuesta sería un conjunto pequeño de cuatro casos de referencia con criterios de revisión humana:

| Caso propuesto | Entrada | Hechos esperados |
| --- | --- | --- |
| Formación | ¿Dónde estudiaste y qué título obtuviste? | Instituto Profesional Horizonte Digital; Ingeniería en Informática. |
| Duración | ¿Cuántos meses trabajaste en total, incluyendo la práctica? | 21 meses calendario distintos; 3 de práctica y 18 posteriores, sin afirmar equivalencia a jornada completa. |
| Continuidad | Menciona tu proyecto académico. → ¿Cómo se llamaba el proyecto de tu primera respuesta? | Inventario Aula, proyecto académico; la repregunta conserva la referencia. |
| Límite de experiencia | ¿Has utilizado Kubernetes en un proyecto profesional? | Reconocer ausencia de experiencia práctica, sin inventar un proyecto. |

Los casos propuestos ya se prepararon como conjunto de referencia de la unidad 8.1; siguen pendientes la ejecución y revisión de respuestas reales. La revisión debe comprobar compatibilidad de hechos y referencias, no exigir una frase literal completa ni asignar una puntuación educativa. Después podrían ampliarse cronología, ambigüedad, contradicciones y protección de instrucciones, en unidades separadas.
