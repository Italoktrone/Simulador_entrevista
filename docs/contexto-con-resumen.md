# Etapa 7.4d: composición del contexto y consulta aislada

Esta unidad reúne el escenario autorizado, las citas antiguas verificadas, los turnos recientes completos y una pregunta de comprobación. Elige la versión con extractos solo si reduce el JSON completo de mensajes. La comparación incluye las marcas y las reglas adicionales, no solo los caracteres de las citas.

La consulta es una prueba aislada sobre una sesión archivada. No reabre esa entrevista, no añade intentos a su registro y no cambia sus contadores. La consola principal continúa usando su controlador actual; la política de activación durante una entrevista sigue pendiente.

## Archivos y funciones

| Archivo | Responsabilidad |
| --- | --- |
| `harness/summary_context.py` | `prepare_summary_context`: revalidar citas, vincular fuentes al escenario, preparar las dos versiones y elegir mensajes junto con un diagnóstico. |
| `scripts/probe_summary_context.py` | Cargar el archivo y el escenario, preparar una propuesta, consultar al candidato y comprobar la integridad del perfil. Solo imprime el resultado. |
| `tests/unit/test_summary_context.py` | 16 casos de composición, vínculos, roles, copias, preguntas inválidas, conservación del sistema y elección según bytes. |
| `tests/integration/test_summary_context_probe_flow.py` | Seis casos con archivo y componentes reales, HTTP simulado y protección de la fuente ante errores o interrupción. |

Se reutilizan `build_messages`, `validate_summary`, `load_session` y la fábrica de clientes. No se añaden dependencias ni se cambian perfil, configuración, puesto, instrucciones del candidato, adaptadores, controlador o esquema de sesión.

## Qué comprueba la preparación

La propuesta se reconstruye desde la sesión antes de cada preparación. Después se comprueban identificador y hash del candidato, referencia del puesto, configuración completa y hash del texto de instrucciones frente a `InterviewSetup` y las instrucciones actuales. Si no coinciden, se rechaza la composición. El archivo 1.0.0 registra la referencia del puesto, no una huella histórica de su descripción; no se afirma verificar un dato que no contiene.

El contexto base se obtiene del constructor existente. El perfil, puesto, configuración y referencias derivadas siguen dentro del mismo mensaje de sistema. Los textos de la conversación no se copian al sistema como reglas nuevas.

Cada pregunta antigua conserva su mensaje `user` exacto. Si su respuesta tiene omisiones, conserva su papel `assistant` y lleva una marca de extracto con el número original. Las citas mantienen su orden y se señala `[…]` entre fragmentos no consecutivos. Si no hay omisiones en esa respuesta, se recupera el texto original completo, incluidos sus espacios. Los pares recientes y la pregunta actual quedan intactos.

Ambas alternativas añaden una guía estática para distinguir orden de mención en la conversación y cronología de los proyectos. La alternativa con extractos añade además otra guía para sus marcas, el carácter histórico de las citas y la prioridad del perfil. Estas guías no incluyen valores procedentes del entrevistador o del selector. Los intentos fallidos siguen excluidos de la conversación enviada y permanecen en el registro completo.

Se comparan los bytes UTF-8 de ambas listas de mensajes serializadas de la misma forma. Si hay omisiones y la alternativa es estrictamente menor, se elige `extractive_summary`. De lo contrario, se elige `full_history`, con motivo `no_omissions` o `no_byte_savings`. La decisión no modifica la propuesta, el registro o el escenario.

La medición corresponde a mensajes generales antes de adaptar el modelo. No equivale a tokens, no incluye el cuerpo completo del transporte y no garantiza que la solicitud quepa. Los controles `truncate: false` y `shift: false` del adaptador local continúan solicitando rechazo ante exceso. No se implementan reenvíos automáticos tras un rechazo.

## Comprobar en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.probe_summary_context '.\outputs\sessions\session-f7be73ff-ab02-42d4-8f63-17d78db4aeb0.json' --keep-recent-pairs 1 --question '¿Cómo se llamaba el proyecto académico que mencionaste antes?'
```

Esperado: **654 passed**, 618 unitarias y 36 integraciones. En esta sesión corta, los dos fragmentos antiguos están conservados; por eso debe elegir **historial completo**, con motivo `no_omissions` y el mismo número de bytes antes y después. La respuesta de comprobación debe identificar **Inventario Aula**, sin exigir una frase idéntica entre ejecuciones.

El comando puede realizar una selección y una consulta al candidato. Si todos los pares se conservan como recientes, solo consulta al candidato. La alternativa externa conserva su activación explícita, pero las variables anteriores seleccionan únicamente Ollama local.

La salida debe terminar indicando que la sesión fuente y sus contadores permanecen sin cambios. No debe generar un archivo nuevo de sesión. Esta prueba no necesita abrir la consola interactiva ni introducir `/iniciar`.

Si aparece un error de coincidencia de fuentes, conservar el mensaje: la sesión y el escenario actual no deben mezclarse modificando sus hashes. Si aparece una selección inválida, una respuesta cortada o un error del proveedor, no se presenta una respuesta de comprobación válida. Se mantienen intactos los archivos y se cierran los recursos del cliente. Ante un error de conexión, comprobar Ollama y el modelo indicado.

## Evidencia y límites

El usuario confirmó la 7.4c con **632 passed in 30.47s**. La propuesta conservó pregunta 1, sus dos citas y la pregunta reciente 3 completa: 233 → 233 caracteres, cero omisiones y procedencia verificada. Se registró en [extractive-summary-user-confirmation-052ae0d7f51c44a1a21a26697ab3d166.json](../outputs/results/extractive-summary-user-confirmation-052ae0d7f51c44a1a21a26697ab3d166.json), distinguiendo el resultado comunicado de la lectura local de la fuente.

Los 22 casos nuevos pasaron en **2,97 s**. La primera suite conjunta terminó con **654 passed in 33.72s**; después de la guía de referencias, la suite final terminó con **654 passed in 34.08s**, 618 unitarias y 36 integraciones, sin fallos. Pytest utiliza proveedores simulados. Las pruebas verifican composición reducida y conservación del historial completo, rechazo de fuentes incompatibles, papeles de conversación, copia independiente, manejo de fallos y archivos sin cambios.

El resumen mantiene su estado `not_reviewed`. Esta unidad comprueba su composición y una consulta de prueba; no certifica que todas las omisiones sean irrelevantes. Las reglas de anclas son conservadoras y las citas pueden contener errores previos del modelo. La integración en una entrevista activa deberá conservar el registro completo y documentar su política de activación y presupuesto.

Durante una prueba real previa, la variante de historial completo respondió por fechas de inicio a una pregunta sobre el primer proyecto mencionado. No se llegó a consultar la alternativa con extractos en esa ejecución. Se registró la discrepancia, sin inventar métricas perdidas, en [summary-context-mention-incident-cb4c3ab00b03407597009c09e7a3e76d.json](../outputs/results/summary-context-mention-incident-cb4c3ab00b03407597009c09e7a3e76d.json). Se añadió la guía de referencias a ambas variantes del constructor de esta unidad. El archivo de instrucciones y los archivos anteriores permanecieron intactos. La consola principal todavía no incorpora este constructor.

La comprobación final real con Ollama y `gemma4:e4b` pasó:

| Caso | Resultado observado |
| --- | --- |
| Archivo real del usuario | Historial completo por `no_omissions`, 27 496 → 27 496 bytes de mensajes; identificó Inventario Aula. Respuesta en 5,39 s. |
| Fixture con historial completo | Identificó Inventario Aula como primer proyecto mencionado y pytest como herramienta de la última respuesta; entrada 6620 tokens, respuesta en 6,69 s. |
| La misma fixture con extractos | Mantuvo esas dos referencias; entrada 6364 tokens, respuesta en 7,94 s. |
| Regresión de fechas con extractos | Indicó MesaFaro como primer proyecto por inicio, en abril de 2025; entrada 6360 tokens, respuesta en 5,08 s. |

La fixture contiene respuestas y selección predefinidas, con frases de relleno introducidas para ejercitar el ahorro. No es una entrevista natural nueva y no se archivó como sesión de la aplicación. En ella, los mensajes pasaron de **30 167 a 28 133 bytes**, ahorro de 2034 bytes. La reducción observada de 256 tokens corresponde solo a las dos consultas comparables de esta muestra; los tiempos no demuestran una mejora de latencia.

La evidencia está en [summary-context-b67d45e6960a4b9dbcb53f51df027355.json](../outputs/results/summary-context-b67d45e6960a4b9dbcb53f51df027355.json). Distingue la consulta sobre el archivo real de las pruebas con fixture y conserva las respuestas completas, métricas, decisiones y hashes. No copia el perfil interno del mensaje de sistema. Todos los archivos de sesiones previos y los cuatro originales del escenario conservaron sus bytes. La API externa permaneció desactivada.

Las referencias y fechas observadas pasaron para estos casos. No se considera resuelta universalmente la interpretación del historial ni se valida automáticamente la calidad semántica de todas las respuestas. La guía nueva afecta a este constructor de prueba; su integración en el controlador principal y la activación durante entrevistas siguen pendientes. Se espera la comprobación del usuario antes de otra unidad.

Confirmación posterior: el usuario obtuvo **654 passed in 35.88s** y la consulta esperada, con Inventario Aula, historial completo y archivo intacto. La unidad 7.4e incorpora la [opción de resumen en el controlador](resumen-en-entrevista.md), conservando la modalidad anterior sin la opción.
