# Etapa 9: integración y validación final del agente candidato

El usuario autorizó la transición con «Pasemos a la Etapa 9». Se reúne la verificación en un bloque, con Ollama local y la API externa desactivada. La validación no incorpora clasificación, rúbrica, puntuaciones, retroalimentación educativa, Godot ni almacenamiento en la nube.

**Resultado: Etapa 9 completada en el alcance técnico comprobado; nueve de nueve etapas del agente terminadas.** La revisión humana de contenido queda separada del éxito técnico. La entrega del agente no declara terminado el proyecto educativo de tres semestres.

## Resultado real y evidencia

| Comprobación | Resultado |
| --- | --- |
| Dependencias | `No broken requirements found.` |
| Suite completa | **738 passed in 45.54s**: 687 unitarias y 51 integraciones, con proveedores simulados. |
| CV y puesto en consola | Mostrados; título, organización y las seis competencias del puesto comprobados en la salida real. |
| Entrevista con Ollama | **20 preguntas exactas y 20 respuestas completas**, cero incidencias. |
| Contador | `/sesion` no consume preguntas; repetir `/iniciar` conserva el contador en 2. |
| Límite | Cierre por `question_limit` en 20; entrada 21 identificada y no registrada ni enviada como pregunta del candidato. |
| Historial | En la respuesta 20 recordó la primera pregunta de formación y el nombre Inventario Aula. |
| Contexto | Veinte eventos válidos en formato 1.1.0; máximo de entrada informado **7106 tokens**. Cero selecciones y cero resúmenes usados: no alcanzó el umbral normal de 7424. |
| Salida anticipada | Sesión independiente 1.0.0, cierre `user_exit`, cero preguntas y UUID distinto. |
| Guardado y lectura | Ambos archivos JSON se leyeron, validaron y compararon con las instantáneas y huellas. |
| Integridad | Cuatro originales y **27 sesiones anteriores** intactos. |

El [registro técnico completo](../outputs/results/final-validation-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b.json) contiene preguntas, comandos, resultados de pytest, entorno, salidas y sesiones. La [verificación final separada](../outputs/results/final-delivery-verification-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b.json) conserva la huella del registro, manifiesto de implementación e inspección del asistente.

- [Sesión de veinte preguntas](../outputs/sessions/session-191fc87c-311f-4cc5-b29c-648589f52ead.json), con [salida completa de consola](../outputs/results/final-console-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b-limite20.txt).
- [Sesión de salida anticipada](../outputs/sessions/session-2794e104-65bb-4f07-a87e-517a612278c7.json), con [salida completa de consola](../outputs/results/final-console-0a8fcec9-17ba-43c5-9094-2b255a7a9f5b-salida-anticipada.txt).

La inspección del asistente no observó contradicciones factuales en las veinte respuestas. Conservó formación, proyectos, tecnologías, aportes, cronología, total de 21 meses con desglose 3/18 y jornadas 9/9 del rol junior. Reconoció los límites de Kubernetes/AWS/Azure, pidió aclaración del periodo y mantuvo el papel de candidato. La respuesta 11 presenta una imprecisión gramatical en «estudios e titulación», sin alterar el hito ni las fechas; se conserva sin reescribir el texto original.

La respuesta final fue: «Usted me preguntó primero “¿Dónde estudiaste y qué título obtuviste?”. El proyecto académico del que hablamos se llama “Inventario Aula”». Esta observación no se convierte en una aprobación semántica humana ni garantiza toda conversación futura.

Entorno comprobado: Python **3.14.3**, `jsonschema` **4.26.0**, `pytest` **9.2.0** y `httpx` **0.28.1**. El modelo fue **gemma4:e4b**, Ollama local. No se cambiaron código de producción, perfil, instrucciones, configuración, dependencias o parámetros para completar la validación.

Esta entrevista no ejercitó una reducción extractiva efectiva: el contexto completo siguió cabiendo. La selección, su integración, fallos y el uso de extractos están cubiertos por pruebas previas y la fixture identificada de la [Etapa 7](resumen-en-entrevista.md); no se presentan como selecciones ocurridas en esta ejecución final.

## Procedimiento

El [guion de verificación](../outputs/results/validate-stage9.py) es un artefacto separado del programa. Ejecuta las 738 pruebas existentes y después abre la consola real mediante un proceso independiente, sin sustituir el proveedor ni el controlador. Conserva el guion de entrada, salidas completas, parámetros, instantáneas y huellas.

La entrevista preparada contiene veinte preguntas reales al modelo **gemma4:e4b**. Antes consulta ayuda, CV, puesto y sesión; después de dos preguntas vuelve a consultar la sesión y prueba `/iniciar` sin reiniciar el contador. Se entrega una entrada adicional identificada para comprobar que la pregunta 21 no se consume. Se activa `--extractive-context` con su política normal, sin forzar el umbral a 1. El historial y las decisiones de memoria se conservan y validan al leer el JSON 1.1.0.

Una segunda ejecución consulta CV/puesto, inicia y termina con `/salir`, sin generar respuestas. Comprueba salida anticipada, independencia del UUID, cero preguntas y lectura del formato 1.0.0. Las pruebas automatizadas cubren además errores de proveedor, tiempos de espera, interrupciones, protección de integridad, contextos rechazados, resumen aplicado y compatibilidad.

Se compara el hash de los cuatro originales y todas las sesiones anteriores antes/después. Las respuestas reales se inspeccionan contra el perfil y las referencias de la Etapa 8. Se separan estado técnico y revisión humana; las pruebas no aprueban semánticamente el texto.

## Uso del agente entregado

Desde PowerShell:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview --extractive-context
```

Usar `/cv`, `/puesto`, `/sesion`, `/iniciar`, escribir preguntas y finalizar con `/salir` o al llegar a veinte envíos. Las preguntas fallidas también cuentan. El programa conserva cada sesión en `outputs/sessions/session-<UUID>.json`.

Para repetir únicamente las pruebas técnicas:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
```

Para revisar un archivo de sesión, `harness.session_log.load_session` valida forma, relaciones y auditoría; no reanuda una conversación. El diagnóstico opcional de tokens está documentado en [diagnóstico del contexto](diagnostico-contexto.md).

## Alcance y límites

Este cierre se refiere al agente del primer semestre y al escenario aprobado con referencia **2026-10-20**, instrucciones **1.0.11** y máximo **20**. Las ejecuciones usan preguntas preparadas y un modelo local; no representan un piloto libre ni una prueba independiente del ajuste previo. No garantizan consistencia universal, cualquier latencia o que preguntas arbitrariamente extensas quepan en la capacidad configurada.

La selección extractiva puede omitir contexto relevante. Los registros completos y el perfil conservan su prioridad; los estados de selección no constituyen revisión humana. Los tiempos y tokens se informan cuando existen, sin convertir valores ausentes en cero. La API externa está implementada y probada con simulaciones; no se realizó validación real de un modelo externo.

Los componentes reservados de clasificación/evaluación de la plantilla pertenecen a fases posteriores. Su presencia no significa que estén implementados ni que formen parte de la entrega actual.
