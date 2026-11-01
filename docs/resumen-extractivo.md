# Etapa 7.4c: propuesta de resumen extractivo verificable

Esta unidad construye y muestra una propuesta para revisar turnos antiguos de una sesión guardada. Conserva preguntas completas, citas literales y los últimos pares completos de conversación. El perfil, la configuración y el registro original permanecen separados. Todavía no se sustituye el historial enviado al candidato.

## Componentes y dependencias

| Archivo | Responsabilidad |
| --- | --- |
| `harness/history_summary.py` | Preparar fuentes, solicitar índices al selector, copiar citas, conservar anclas y verificar la propuesta reconstruyéndola desde el original. |
| `scripts/preview_summary.py` | Leer una sesión validada, mostrar proveedor/modelo y generar una vista previa para revisión. No escribe archivos ni reanuda entrevistas. |
| `tests/unit/test_history_summary.py` | 51 casos de selección, citas, metadatos, cambios, tipos, ventanas recientes, integridad, errores y conservación de anclas. |
| `tests/integration/test_summary_preview_flow.py` | Cuatro casos de lectura → adaptador → selección → vista previa, con HTTP simulado y archivos temporales. |

No se añaden dependencias ni se cambia el contrato `LLMClient.generate`. Se reutilizan el lector de sesiones y el cliente seleccionado por la fábrica. La alternativa externa conserva su activación explícita; las comprobaciones reales de esta unidad utilizaron Ollama y `gemma4:e4b`, con API externa desactivada.

## Cómo se prepara la propuesta

1. Se recibe una sesión validada por `load_session`, con integridad registrada `unchanged`. Se obtienen únicamente intentos `completed`, conservando sus números originales. Los intentos fallidos permanecen en el archivo, pero no se envían al selector como conversación válida.
2. `keep_recent_pairs` determina cuántos pares completos recientes se mantienen. El valor predeterminado es dos; admite de uno a veinte. Si no hay turnos antiguos, no se crea un cliente ni se consulta un modelo.
3. Las respuestas antiguas se separan en fragmentos por puntuación seguida de espacio o saltos de línea. Es segmentación textual, no análisis lingüístico completo. Cada pregunta antigua se conserva íntegra.
4. El selector recibe solamente preguntas antiguas y fragmentos numerados, como datos en un mensaje `user`, con reglas separadas en `system`. No recibe el perfil interno, el puesto, credenciales, instrucciones del candidato, intentos fallidos o los turnos recientes.
5. El modelo debe devolver un JSON con números de pregunta y listas crecientes de índices. Python rechaza texto libre, campos adicionales, claves repetidas, turnos ausentes, cambios de orden, índices inexistentes o repetidos y selecciones cortadas. No reintenta una selección fallida por su cuenta.
6. Python añade anclas conservadoras aunque el selector las omita: primero y último fragmento; fragmentos con cifras, ciertas negaciones o límites; y palabras con mayúscula después de la primera palabra, como indicio de nombres. Estas reglas pueden conservar contenido adicional y no identifican toda la relevancia semántica.
7. Se copian las citas originales por sus índices. La propuesta indica fragmentos omitidos y fragmentos añadidos por la protección. Conserva configuración, candidato/puesto, hashes de perfil e instrucciones, huella del historial aceptado y huella de cada respuesta antigua.
8. `validate_summary` reconstruye la propuesta desde la sesión y compara su representación canónica. Detecta cambios de citas, preguntas, números, configuración, turnos recientes, estadísticas y campos adicionales. Una modificación posterior de la conversación fuente invalida la propuesta anterior.

El resultado lleva `summary_version: 1.0.0` y `review_status: not_reviewed`. No es un archivo de sesión nuevo ni una actualización de los antecedentes. El comando solo imprime; las propuestas incluidas en la evidencia técnica fueron guardadas por el verificador externo.

## Por qué usar citas y revisar omisiones

La generación libre de resúmenes puede introducir contenido no respaldado por la fuente; este riesgo está documentado en [Maynez et al., ACL 2020](https://aclanthology.org/2020.acl-main.173/). Esta implementación limita la salida del modelo a índices y copia las palabras desde el registro original.

La verificación demuestra procedencia, no verdad. Una respuesta anterior del candidato puede contener un error. Además, una selección literal puede cambiar el sentido al omitir contexto, y las reglas léxicas no garantizan que conserven todos los hechos importantes. Por eso se muestra como propuesta para revisión y todavía no se aplica al controlador. El perfil seguirá teniendo prioridad cuando se integre.

Las estadísticas cuentan caracteres de fragmentos, sin sus separadores. No miden tokens ni el ahorro total del futuro mensaje, que también necesitará preguntas, referencias y marcadores. Es válido conservar todos los fragmentos cuando la respuesta es breve o contiene hechos necesarios. No se fuerza una reducción porcentual.

## Comprobación en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.preview_summary '.\outputs\sessions\session-f7be73ff-ab02-42d4-8f63-17d78db4aeb0.json' --keep-recent-pairs 1
```

Esperado: **632 passed**, 602 unitarias y treinta integraciones. La vista previa debe mostrar:

- Sesión de origen `f7be73ff-ab02-42d4-8f63-17d78db4aeb0` y propuesta pendiente de revisión.
- Pregunta antigua **1**, con las dos citas sobre Inventario Aula y sus tecnologías. Ambas quedan protegidas por ser los extremos de esa respuesta.
- Pregunta reciente **3**, con su pregunta y respuesta completas.
- Dos fragmentos antiguos conservados, cero omitidos y **233 → 233** caracteres de fragmentos. No hace falta omitir contenido en esta respuesta breve.
- Confirmación de procedencia y citas verificadas contra la fuente.

No debe aparecer la larga entrada sintética del intento 2. Sus datos siguen en el archivo original. Tampoco se espera un nuevo archivo de sesión después de ejecutar la vista previa.

Con el valor predeterminado de dos pares recientes, esta sesión no tendría turnos antiguos: se mostrarían ambos completos sin consultar al modelo. El argumento uno permite ejercitar el selector en una entrevista corta sin inventar turnos nuevos.

Si falla la conexión, comprobar Ollama y el modelo. Si aparece un error de selección inválida o cortada, conservar la salida: no se acepta una propuesta parcial ni se modifica la fuente. La selección extensa también puede superar el contexto del modelo y ser rechazada por la protección de la 7.4b; aún no hay procesamiento por lotes o resumen jerárquico. Las instrucciones de la entrevista no necesitan cambios para esta prueba.

## Evidencia de desarrollo

El usuario confirmó la 7.4b con **577 passed in 28.46s**, dos respuestas completas y un rechazo por contexto, con estados `completed`, `error`, `completed` y código `context_limit`. La repregunta recordó Inventario Aula; las respuestas tardaron 64,76 y 3,47 s. La lectura local confirmó la sesión, la integridad y el archivo. Se registró en [context-guard-user-confirmation-1d88e6bfc79c41609280cc0042c7c521.json](../outputs/results/context-guard-user-confirmation-1d88e6bfc79c41609280cc0042c7c521.json).

Pasaron primero 48 casos nuevos. Tras añadir una comprobación de tipos en la revalidación, la suite de 626 casos pasó en 50,41 s. La comprobación real posterior detectó un problema: el selector omite anclas aunque el prompt pida conservarlas. La primera verificación se detuvo por incumplir el contrato del primer fragmento; una repetición capturó la respuesta en [summary-selector-preliminary-bebf1172639f49398fecefc0e529c018.json](../outputs/results/summary-selector-preliminary-bebf1172639f49398fecefc0e529c018.json). En esa fixture seleccionó `[1,4]` y `[2]`, omitiendo contexto sobre ausencia de clientes y administración de producción. No se aplicó la propuesta a una entrevista.

La corrección pasó la conservación de anclas a Python, mantuvo el rechazo de índices inexistentes y añadió regresiones. El selector puede proponer índices válidos sin todos los obligatorios: la aplicación repone las citas protegidas y lo indica. La respuesta preliminar guardada se reprodujo bajo la política final y se validó contra sus fuentes. No se depende solo de otra promesa en el prompt.

Los 55 casos nuevos finales pasaron en 6,04 s. La suite conjunta final terminó con **632 passed in 49.16s**, 602 unitarias y treinta integraciones. Son 51 casos unitarios y cuatro integraciones nuevos. Pytest utiliza proveedores simulados; las consultas reales se hicieron en una verificación externa separada.

La revisión final real realizó dos llamadas locales al selector:

- **Sesión real del usuario:** mantuvo sus dos fragmentos antiguos, con 233 → 233 caracteres y cero omisiones; conservó completa la pregunta 3. Selección en **6,37 s**.
- **Fixture explícita de cuatro turnos:** respuestas predefinidas con frases de relleno, no una entrevista natural nueva. Seleccionó `[1,2,4]` en cada una de las dos respuestas antiguas: ocho fragmentos pasaron a seis, 354 → 240 caracteres. Se omitieron únicamente las dos frases de relleno de esa muestra y se conservaron proyectos, tecnologías, ausencia de clientes y límite de producción; los dos turnos recientes quedaron completos. Selección en **11,50 s**. Esta muestra no demuestra que toda omisión futura sea irrelevante.

Evidencia final: [extractive-summary-15bb185e26174f998e069279cc7c8713.json](../outputs/results/extractive-summary-15bb185e26174f998e069279cc7c8713.json). Incluye solicitudes resumidas, salidas del selector, propuestas, vistas previas, reproducción de la selección preliminar y comparación de hashes. Todos los archivos de sesiones anteriores y los cuatro originales del escenario conservaron sus bytes. API externa desactivada, instrucciones 1.0.11 y referencia 2026-10-20 conservadas.

La integración del resumen en una entrevista activa, su presupuesto completo, marcadores de datos y política de activación siguen pendientes. Se espera la comprobación del usuario de esta unidad antes de continuar.

Confirmación posterior: el usuario obtuvo **632 passed in 30.47s** y la vista previa esperada, con citas 1/2 y pregunta reciente 3 completas, sin omisiones. La unidad 7.4d prepara el [contexto con resumen y una consulta aislada](contexto-con-resumen.md); la activación en una entrevista sigue siendo otro paso.
