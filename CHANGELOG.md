# Registro de cambios

## 2026-11-01 · Presupuesto explícito de salida UNAB

- Confirmado finish_reason length con 512 tokens y cero texto final; razonamiento interno no confirmado.
- Presupuesto UNAB predeterminado 2048 y campo privado opcional api_max_output_tokens, validado y visible en el selector. Clave y presupuestos de otros proveedores intactos.
- Diecisiete regresiones nuevas; 109 pruebas dirigidas aprobadas. Sin llamadas API reales ni escalado/reintentos automáticos.

## 2026-11-01 · Diagnóstico de consumo y salidas UNAB

- Solicitud de razonamiento desactivado conservando límite 512; efecto real pendiente de comprobar en la pasarela.
- Metadatos de uso incluso ante rechazos, diagnóstico separado al cerrar y protección contra exposición de pensamiento o claves.
- Seis regresiones nuevas; 765 pruebas aprobadas. Investigación local sin cuota API y sin alterar datos aprobados.

## 2026-11-01 · Selector de proveedor y UNAB IA

- Configuración privada ignorada por Git y menú local/API mediante scripts.start_interview.
- Adaptador Chat Completions independiente para gemma4:26b en UNAB IA; Responses anterior conservado.
- Suite completa de 759 pruebas aprobadas; sin llamada real al servicio externo. Datos e instrucciones aprobados intactos.

## 2026-10-31 · Integración y validación final (Etapa 9)

- Transición autorizada explícitamente por el usuario. Suite completa: **738 passed in 45.54s** y dependencias sin incompatibilidades.
- Consola real con gemma4:e4b: veinte preguntas y veinte respuestas completas, cero incidencias, cierre al límite y entrada 21 excluida. Recordó la primera pregunta y el proyecto académico al final.
- Salida anticipada en sesión independiente sin preguntas; lectura validada de formatos 1.0.0 y 1.1.0. Cuatro originales y 27 sesiones anteriores intactos.
- Veinte eventos de contexto, máximo informado 7106 tokens, cero selecciones y resúmenes aplicados en esta entrevista. El uso real de extractos conserva sus evidencias previas separadas.
- Documentados resultados, límites y guía de uso. Nueve etapas completadas en su alcance técnico; las funciones educativas posteriores no forman parte de esta entrega.

## 2026-10-31 · Cierre técnico de la Etapa 8

- Confirmada la ejecución del usuario: seis casos ampliados, diez respuestas completas y seis sesiones validadas. Cuatro originales y veintiuna sesiones anteriores conservados.
- Añadido cierre con evidencias y límites; avance técnico de ocho etapas completadas y una pendiente. La Etapa 9 no se inicia automáticamente.
- Cierre documental sin llamadas nuevas o repetición de pruebas. La aprobación semántica humana explícita no se infiere del éxito técnico.

## 2026-10-31 · Bloque ampliado de consistencia (unidad 8.3)

- Se validó la ejecución del usuario de la 8.2: cuatro casos y cinco respuestas completas con sus sesiones intactas.
- Se añadió el conjunto ampliado: seis casos, diez preguntas y referencias al perfil revisado. Se reutilizó el ejecutor sin cambiar código de producción.
- Dos comprobaciones nuevas aprobadas en 1,88 s. Hay 738 pruebas disponibles; la última suite completa sigue siendo la de 736 y se repetirá en la validación final.
- El lote 5e7c73f0-1e3a-4054-8ad8-1501ab6eed3d terminó con diez respuestas completas. Se registraron observaciones del asistente, una imprecisión de redacción y detalles omitidos, sin contradicciones factuales observadas. Cuatro originales y quince sesiones anteriores intactos.
- La Etapa 8 queda pendiente de comprobación final del usuario; la Etapa 9 no se inicia automáticamente.

## 2026-10-31 · Ejecución de referencias por lotes (unidad 8.2)

- El usuario confirmó 730 pruebas en 150,75 s y el listado de la 8.1. Solicitó avanzar en bloques mayores con respuestas breves y menos consumo de tokens de chat.
- Se añadió `scripts.run_reference_cases`: Ollama exclusivamente local, sesión independiente por caso, continuidad dentro del caso y detención tras el primer fallo. Conserva sesiones, instantáneas y procedencia sin emitir veredictos semánticos.
- Se añadieron seis integraciones; suite completa de **736 passed in 123.96s**.
- El lote real fd00eb31-7961-4390-9807-c78695f3a247 obtuvo cinco respuestas completas con gemma4:e4b. Se conservaron originales y sesiones anteriores. La inspección del asistente encontró los hechos esperados; la revisión humana y la ampliación siguen pendientes.

## 2026-10-31 · Referencias de consistencia (unidad 8.1)

- El usuario autorizó la Etapa 8 tras el cierre funcional de historial/contexto. El estado de las nueve etapas registra siete completadas, la 8 en curso y la 9 pendiente.
- Se prepararon cuatro casos y cinco preguntas con referencias al perfil revisado y a hechos temporales derivados, contrato JSON y cargador de copias independientes.
- `scripts.show_reference_cases` muestra criterios humanos sin consultar modelos, escribir sesiones o evaluar respuestas. El conjunto reutiliza preguntas de desarrollo y no se presenta como prueba independiente.
- Se añadieron 37 pruebas unitarias y tres integraciones: 40 nuevas aprobadas y suite completa de **730 passed in 45.44s**.
- Evidencia: `reference-suite-da11e781799f4ef6ba7331f1964e0e39.json`. Cuatro originales y siete archivos de sesiones conservados. La comprobación del usuario y las respuestas reales de estos casos siguen pendientes.

## 2026-10-28 · Adaptación estructural

- La plantilla genérica CINF110 se reorganizó para el simulador de entrevistas descrito en la conversación compartida.
- Se sustituyó `src/` por `agent/` (definiciones) y `harness/` (futura ejecución Python).
- Se añadieron espacios para clasificación, evaluación por criterios, cálculo local, retroalimentación inmediata, validación y registro.
- Se separaron perfiles, preguntas de referencia, configuraciones, contratos y salidas generadas.
- `docs/proyecto.md` se sustituyó por `docs/informe.md`, con secciones pendientes, y una guía de llenado.
- `docs/curso.yml` se trasladó a `docs/academico/cinf110.yml`, conservando sus valores originales.
- Los espacios de evaluación se distribuyeron entre `docs/pruebas/` y `docs/entregas/`, distinguiendo CINF110 de CINF200.
- Se retiraron los marcadores genéricos de herramientas, integraciones y datos de ejemplo sin una responsabilidad concreta en el MVP.
- Se mantuvieron .env.example, las plantillas de colaboración y la reserva de automatización de pruebas.
- No se implementaron funciones, contratos completos, perfiles, ponderaciones, ejemplos de entrevista, resultados ni evidencias.

El detalle de destinos y responsabilidades está en [la guía](docs/guia-estructura.md).

## 2026-10-31 · Guardado local de sesiones (unidad 7.3)

- Se completó `harness/session_log.py` y el contrato `schemas/session.schema.json`.
- La consola guarda un JSON por UUID al cerrar; no sobrescribe registros existentes. La lectura valida datos sin reanudar entrevistas.
- Se conserva el registro de errores y texto parcial; fallos de escritura se comunican sin confirmar guardado y devuelven código 1.
- Se añadieron 53 casos y aislamiento temporal de archivos en pytest; suite final de 530 pruebas aprobadas.
- Se documentan implementación, límites y comprobaciones en `docs/persistencia-sesiones.md`.

## 2026-10-31 · Diagnóstico del contexto registrado (unidad 7.4a)

- Se confirmó el guardado/lectura del usuario: 530 pruebas y sesión de dos respuestas con UUID coincidente y perfil intacto.
- Se añadieron `harness/context_budget.py` y `scripts/inspect_context.py`: comparación de tokens ya informados con reservas explícitas, sin red ni cambios de sesiones.
- Las métricas ausentes permanecen desconocidas; los tokens reutilizados no se descuentan de la entrada. Los parámetros de comparación no se presentan como ajustes históricos del archivo.
- Se añadieron 29 casos, suite final de 559 pruebas aprobadas y evidencia de lectura del archivo real del usuario.
- La reducción de contexto y los resúmenes siguen pendientes.

## 2026-10-31 · Rechazo explícito de contexto excesivo (unidad 7.4b)

- Se confirmó el diagnóstico del usuario: 559 pruebas, entradas 6023/6097 y márgenes 1401/1327.
- Ollama solicita `truncate: false` y `shift: false`; se reconocen errores conocidos mediante `LLMContextLimitError` y catálogo `context_limit`, sin copiar cuerpos HTTP.
- El registro 1.0.0 admite ese código conservando los anteriores. La consola explica el rechazo y conserva todos los intentos.
- Se añadieron 18 casos; suite final de 577 pruebas aprobadas. La prueba real local conservó la referencia a Inventario Aula tras rechazar una entrada sintética extensa.
- El resumen controlado continúa pendiente.

## 2026-10-31 · Propuesta de resumen extractivo (unidad 7.4c)

- Se confirmó el rechazo y continuidad del usuario: 577 pruebas y sesión completed/error/completed con context_limit.
- Se añadieron `harness/history_summary.py` y `scripts/preview_summary.py`, con selección de índices, citas exactas, metadatos de procedencia, verificación por reconstrucción y pares recientes completos.
- La prueba real detectó omisiones del selector; Python conserva ahora anclas y registra las que añadió por protección. El resultado sigue pendiente de revisión, separado del controlador.
- Se añadieron 55 casos; suite final de 632 pruebas aprobadas. Se registraron una sesión real y una fixture identificada, conservando archivos originales.

## 2026-10-31 · Composición de contexto con extractos (unidad 7.4d)

- Se confirmó la vista previa del usuario: 632 pruebas y dos citas conservadas con procedencia verificada.
- Se añadieron `harness/summary_context.py` y `scripts/probe_summary_context.py`: vínculos con el escenario, papeles de conversación conservados, guía estática y elección según bytes de mensajes completos.
- Si no hay omisiones o ahorro real de bytes, se conserva el historial completo. No se modifica la sesión fuente ni se reanuda su controlador.
- Se añadieron 22 casos; suite final de 654 pruebas aprobadas. La activación durante una entrevista continúa pendiente.

La prueba real de la 7.4d detectó confusión entre orden de mención y fechas en la variante completa. Se añadió guía estática al nuevo constructor para ambas variantes y se verificaron de nuevo las referencias y el orden de inicio. El archivo de instrucciones y el controlador principal permanecen sin cambios. Evidencia y límites en `docs/contexto-con-resumen.md`.

## 2026-10-31 · Resumen activable en entrevistas (unidad 7.4e)

- Se confirmó la composición del usuario: 654 pruebas y respuesta correcta sobre Inventario Aula, sin modificar la fuente.
- `--extractive-context` integra política, selección y composición en `InterviewRuntime`; se conservan los originales y se usa historial completo ante fallos conocidos o ausencia de ahorro.
- El contrato 1.1.0 añade política y auditoría de contexto, manteniendo lectura del 1.0.0. Los selectores no consumen preguntas.
- Se añadieron 36 casos; suite final de 690 pruebas. Una entrevista local de cuatro preguntas y una fixture identificada comprobaron ambos modos y lectura exacta.
- La opción permanece explícita y no certifica relevancia de todas las omisiones o consistencia universal.

## Cierre funcional de historial y contexto

- El usuario confirmó 690 pruebas en 38,14 s y la sesión 1.1.0 f8d281c9-bca7-4bdd-9b52-d7f9788399e5, con cuatro respuestas y una selección independiente.
- Se validó el archivo y se registró la confirmación en evidencia estructurada; los cuatro hashes del escenario coinciden con los aprobados.
- Se añadió `docs/cierre-etapa-7.md`, con alcance, limitaciones y propuesta de transición. La Etapa 8 todavía no se inicia.
