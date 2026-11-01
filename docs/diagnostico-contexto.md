# Etapa 7.4a: diagnóstico del contexto registrado

Esta unidad permite revisar los tokens de entrada que el proveedor informó en una sesión ya guardada. Es la base de medición antes de integrar una política de reducción o resumen. El comando funciona sin consultar a Ollama o a una API y no escribe archivos. No cambia el controlador, la conversación enviada, el perfil, las instrucciones o el formato de sesión 1.0.0.

## Componentes y dependencias

| Archivo | Función |
| --- | --- |
| `harness/context_budget.py` | `ContextBudget` valida reservas y calcula el límite de entrada; `assess` compara una métrica; `build_context_report` reúne un informe sin copiar textos de la entrevista. |
| `scripts/inspect_context.py` | Lee una sesión mediante `load_session` y muestra su diagnóstico. Acepta capacidad, reserva de salida y margen explícitos. |
| `tests/unit/test_context_budget.py` | 25 casos de límites, valores desconocidos, entradas inválidas, reserva configurable, copias y protección de textos. |
| `tests/integration/test_context_inspection_flow.py` | Cuatro casos del recorrido archivo → validación → informe, sin red ni cambios de archivos. |

No se añaden dependencias. El módulo de cálculo usa la biblioteca estándar. El comando reutiliza el lector y validador de sesiones; obtiene sus valores predeterminados de capacidad y salida de `OllamaSettings`, sin crear un cliente, leer credenciales o cambiar ajustes del proveedor.

## Cálculo y significado

La política de comparación elegida para este proyecto es:

```text
Capacidad de comparación:       8192 tokens
Reserva máxima de salida:       512 tokens
Margen adicional de la política: 256 tokens
Límite de entrada: 8192 - 512 - 256 = 7424 tokens
Margen disponible = 7424 - entrada informada
```

Los 256 tokens son una reserva inicial configurable del proyecto, no un requisito del modelo ni una garantía estadística. Los parámetros se proporcionan al diagnóstico: el archivo 1.0.0 no conserva la capacidad o el máximo de salida solicitado. Por eso el informe no los presenta como metadatos históricos del archivo y no infiere la capacidad a partir del nombre del modelo. Cambiar `--context-size` cambia solo la comparación; no reconfigura Ollama.

La entrada registrada procede de `LLMResponse.input_tokens`. En el adaptador Ollama se obtiene de `prompt_eval_count`, documentado como el número de tokens del prompt. `prompt_eval_cached_count` indica tokens leídos de la caché: se conserva como métrica independiente y no se resta para calcular espacio libre. Fuentes primarias consultadas el 31 de octubre de 2026: [Chat API](https://docs.ollama.com/api/chat) y [Usage](https://docs.ollama.com/api/usage).

El resultado por intento es `within_budget` si queda margen positivo, `at_limit` si queda cero y `over_budget` si es negativo. Si no hubo respuesta o falta `input_tokens`, es `unknown` y el margen queda desconocido. Un cero informado se distingue de una métrica ausente. Se incluyen métricas de respuestas parciales o intentos fallidos que conserven una respuesta; no se inventan conteos para los demás.

Estos son estados de uso técnico; no clasifican preguntas ni evalúan su calidad. El informe conserva el estado original del intento, muestra su número y métricas, y excluye preguntas, respuestas, perfil interno e incidencias detalladas.

## Comprobar en PowerShell

Desde la raíz del proyecto, usando el archivo que el usuario acaba de verificar:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.inspect_context '.\outputs\sessions\session-d8964573-f78f-4fe6-802a-391e2e6913d7.json' --context-size 8192 --max-output-tokens 512 --safety-margin 256
```

Esperado: **559 passed**, 534 unitarias y 25 integraciones. El diagnóstico debe conservar el UUID `d8964573-f78f-4fe6-802a-391e2e6913d7`, mostrar límite de entrada 7424 y:

| Intento | Entrada informada | Margen con las reservas elegidas | Resultado |
| --- | --- | --- | --- |
| 1 | 6023 | 1401 | Dentro del presupuesto |
| 2 | 6097 | 1327 | Dentro del presupuesto |

Mayor entrada informada: 6097. Intentos sin métrica: cero. La ejecución del diagnóstico debe ser breve y no necesita Ollama abierto. No es necesario iniciar otra entrevista para esta unidad.

Si aparece «No se pudo revisar el contexto», comprobar la ruta del JSON y que las reservas dejen entrada positiva. Un archivo inválido se rechaza mediante el lector de sesiones. El programa devuelve código 1 sin modificarlo. No se debe editar la evidencia para que encaje en el presupuesto.

## Evidencia y límites

El usuario confirmó previamente la unidad 7.3: **530 passed in 26.55s**, sesión cerrada con dos respuestas completas, cero incidencias, fuente intacta y el mismo UUID al guardar y leer. Las respuestas dieron 21 meses calendario y nueve meses por cada jornada; latencias 63,13 y 13,22 s. La lectura local del archivo confirmó esos estados y sus métricas. Registro estructurado de la confirmación: [session-persistence-user-confirmation-93b7cab3eadb498d808facee10093926.json](../outputs/results/session-persistence-user-confirmation-93b7cab3eadb498d808facee10093926.json).

La suite de esta unidad pasó con **559 passed in 27.36s**, sin fallos ni solicitudes reales. Se añadieron 25 casos unitarios y cuatro integraciones. Las integraciones impiden llamadas HTTP y comparan los bytes de los archivos antes y después del diagnóstico.

El comando real leyó el archivo anterior y obtuvo los márgenes 1401 y 1327, con código 0. Los hashes de todos los archivos de sesiones y de perfil, puesto, configuración e instrucciones se conservaron. Evidencia: [context-budget-7bbc164655844b038dfe497a064d4101.json](../outputs/results/context-budget-7bbc164655844b038dfe497a064d4101.json). Esta evidencia adicional la escribe el verificador; el comando de diagnóstico solo lee e imprime.

El diagnóstico analiza llamadas pasadas. No cuenta exactamente los tokens de una pregunta futura, no demuestra que el servidor conservara todos los mensajes recibidos y no detecta por sí solo un recorte anterior. No usa equivalencias entre caracteres y tokens ni extrapola cuántas preguntas faltan. Veinte preguntas es el límite de envíos, no una garantía de capacidad del contexto.

La conservación automática de referencias y hechos durante un resumen, la elección del punto de reducción y su integración antes de enviar una pregunta siguen pendientes. Un resumen generado por otro LLM puede omitir o inventar hechos; habrá que conservar las fuentes originales y los registros completos por separado y validar su contenido antes de usarlo. Esta unidad deja comprobada la medición disponible y espera el resultado del usuario antes de continuar.

Confirmación posterior: el usuario obtuvo **559 passed in 25.70s** y los valores esperados del diagnóstico. Antes de resumir, la unidad 7.4b incorpora una [protección frente al recorte de contexto](proteccion-contexto.md), verificada con Ollama 0.34.2. Las mediciones y cifras de la 7.4a se conservan como evidencia histórica.
