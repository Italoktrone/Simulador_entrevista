# Tiempos de Ollama y preparación para la demostración

Unidad de diagnóstico previa a la consola. El usuario confirmó 352 pruebas y una respuesta correcta que tardó **275,82 s**. La evidencia original permanece en `outputs/results/ollama-smoke-5f2399bfb48b4c6e9e09d93a4122bc94.json` y no se modificó para añadirle métricas posteriores.

## Qué se pudo comprobar de esa llamada

El registro técnico del servicio, con finalización a las 03:06:35 del 31 de octubre de 2026 en Santiago, mostró:

| Medición del registro | Tiempo |
| --- | --- |
| Procesar los 5073 tokens de contexto | 232,60 s |
| Generar los 24 tokens de respuesta | 14,31 s |
| Total de esas dos fases | 246,91 s |
| Llamada completa medida por el cliente | 275,82 s |

La mayor parte del tiempo de esa consulta se consumió al procesar el contexto. La diferencia restante no se atribuye íntegramente a carga: el JSON antiguo no conservó su duración específica. La lectura actual de CPU/GPU no describe necesariamente su estado durante esa consulta. No se determinó la causa exacta de la variación frente a las llamadas anteriores.

## Cambio implementado

`LLMResponse` añade métricas opcionales que el adaptador Ollama obtiene de la respuesta del servicio:

| Campo | Fuente y significado |
| --- | --- |
| `server_total_seconds` | `total_duration`, total informado por el servidor. |
| `load_seconds` | `load_duration`, carga informada por el proveedor. |
| `prompt_eval_seconds` | `prompt_eval_duration`, procesamiento del contexto. |
| `eval_seconds` | `eval_duration`, generación de la respuesta. |
| `cached_input_tokens` | `prompt_eval_cached_count`, tokens de entrada reutilizados de caché. |

Las duraciones se convierten de nanosegundos a segundos según el [contrato de chat de Ollama](https://docs.ollama.com/api/chat). Un campo ausente o inválido queda en `None` y se muestra como `no informado`; cero es una medición válida. No se inventan métricas para OpenAI u otro proveedor. El tiempo de llamada del cliente sigue separado del total del servidor; no se presupone que las fases sumen exactamente ese total.

`OllamaSettings.keep_alive` vale ahora **`15m`** y el adaptador lo envía en cada solicitud local. Pide conservar el modelo en memoria después de responder, reduciendo la posibilidad de volver a cargarlo por una pausa de pocos minutos. Durante ese tiempo ocupa memoria. La opción no acelera por sí misma una preparación inicial sin caché y el servicio puede liberar el modelo si se detiene o necesita los recursos para otra carga.

No se aumentó la espera de lectura de 300 s ni se redujo la ventana de 8192 tokens para truncar antecedentes. Perfil, puesto, instrucciones y contexto autorizado permanecen iguales. La API externa continúa desactivada en estas comprobaciones.

## Mediciones después del cambio

Se ejecutaron dos consultas consecutivas de la misma pregunta, con el mismo mensaje de sistema:

| Medición | Primera | Repetición inmediata |
| --- | --- | --- |
| Llamada del cliente | 55,54 s | 2,18 s |
| Carga informada | 34,88 s | 0,02 s |
| Procesamiento del contexto | 18,58 s | 0,10 s |
| Generación | 1,94 s | 1,96 s |
| Total del servidor | 55,49 s | 2,17 s |
| Tokens de entrada | 5073 | 5073 |
| Tokens reutilizados | 0 | 5072 |
| Tokens de salida | 24 | 24 |

Ambas finalizaron con `stop`, conservaron la institución y el título exactos y comprobaron el original intacto. Evidencias:

- `outputs/results/ollama-smoke-4704e1947b3e498db5a82648ea37450b.json`.
- `outputs/results/ollama-smoke-817805040fce484da953c8f208c62767.json`.

Esto confirma reutilización del contexto en la repetición. No demuestra que cambiar `keep_alive` haya acelerado la primera consulta de 275,82 a 55,54 s: esa opción regula permanencia, no velocidad de procesamiento. Tampoco permite prometer 2,18 s para preguntas nuevas, otra carga del equipo o una entrevista completa. `ollama ps` confirmó que el modelo seguía cargado y que restaban 12 minutos al comprobarlo después de las pruebas.

## Repetir en PowerShell

Desde la raíz del proyecto, con Ollama abierto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
if ($LASTEXITCODE -eq 0) {
    .\.venv\Scripts\python.exe -X utf8 -m scripts.smoke_test
}
ollama ps
```

La suite debe mostrar **404 passed**: 394 casos unitarios y diez integraciones, sin consultas reales. Cada ejecución del script hace una pregunta local y muestra el desglose de tiempos y tokens reutilizados, junto con la respuesta y la comprobación del perfil. La repetición solo se ejecuta si la primera llamada termina correctamente. Si falla o agota la espera, conservar su evidencia y revisar el servicio antes de iniciar otra generación.

Para la demostración conviene preparar el candidato con una consulta de prueba antes de iniciar la entrevista, dejando margen para la carga y el procesamiento inicial. La prueba aislada no crea una sesión ni incrementa un contador de entrevista. Mantener pausas inferiores a la permanencia solicitada ayuda a conservar los recursos preparados; otras solicitudes o cambios de contexto pueden reducir la reutilización.

Si no se reutilizan tokens, conservar ambos JSON y la salida de `ollama ps` para revisarlos. Si aparece un tiempo de espera, no asumir que una solicitud nueva resolverá la lentitud ni activar la API automáticamente. El ajuste es local al proyecto y no cambia el plan de energía, los controladores o la configuración global de Ollama.
