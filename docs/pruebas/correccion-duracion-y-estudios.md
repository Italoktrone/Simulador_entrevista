# Duración laboral y comparación de estudios con todos los proyectos

Esta corrección responde a las preguntas nuevas de la comprobación del usuario. Se mantiene el alcance de la Etapa 7.1: memoria en ejecución, sin avanzar a sesiones persistentes.

## Observaciones de la ejecución del usuario

El usuario obtuvo **440 passed in 45.40s** con `gemma4:e4b`. Las preguntas de orden por inicio, solapamiento y término de los proyectos fueron correctas. El original quedó intacto. La primera respuesta tardó 83,54 s; no se midieron las fases de esa llamada y no se atribuye esa duración a una causa concreta.

La [evidencia estructurada del mensaje](../../outputs/results/temporal-user-27a8aaec91904d909ac51095afd5b6cc.json) conserva preguntas, respuestas, antecedentes y acciones de corrección.

| Pregunta | Observación | Referencia y resultado esperado |
| --- | --- | --- |
| «¿Cuantos meses trabajaste en total?» | Responde aproximadamente un año y medio incluyendo práctica. | 3 meses de práctica más 18 posteriores: **21 meses calendario**. El resumen profesional del perfil ya distingue práctica y experiencia posterior; no se cambia ese resumen. |
| «¿En el tiempo que no trabajabas en ellos que realizabas?» | Afirma que cursaba sus estudios, sin delimitar el periodo. | La pregunta es ambigua. Estudió hasta diciembre de 2025; debe precisar a qué periodo se refiere o limitar la afirmación a los meses correspondientes. No se presume que la respuesta sea falsa para todo periodo. |
| «¿Terminaste primero tus estudios o tus proyectos? y en que orden» | Menciona Inventario Aula y titulación, pero omite MesaFaro. | Inventario Aula en noviembre de 2025; término de estudios y titulación en diciembre de 2025; MesaFaro en septiembre de 2026. |

## Datos derivados y límites del cálculo

| Periodo laboral | Meses calendario | Jornada respaldada |
| --- | --- | --- |
| Práctica: enero a marzo de 2025 | 3 | El perfil no especifica las horas o jornada. |
| Desarrollador Junior: abril a diciembre de 2025 | 9 | Parcial. |
| Desarrollador Junior: enero a septiembre de 2026 | 9 | Completa. |
| Total de los roles laborales | **21** | No son 21 meses equivalentes a jornada completa. |

El conteo incluye ambos extremos de cada periodo mensual. Se unen los meses de los roles laborales para no duplicar meses si hay empleos simultáneos. No se suman proyectos académicos como empleos ni proyectos ya realizados dentro de un rol laboral. Los 18 meses posteriores a la práctica se mantienen separados de los 21 totales. No se calculan equivalentes a jornada completa sin horas o fracciones numéricas suficientes.

La secuencia conjunta distingue término de estudios y titulación, incluso si en otro perfil fueran meses diferentes. Los eventos que coinciden en el mismo mes no fijan un orden dentro de ese mes.

## Archivos y responsabilidades

| Archivo | Función |
| --- | --- |
| `harness/temporal_facts.py` | `build_temporal_facts()` calcula meses de empleo y términos conjuntos desde el perfil validado. `format_temporal_reference()` presenta esos mismos datos. Sin archivos, proveedores ni dependencias nuevas. |
| `harness/prompt_builder.py` | Añade `temporal_facts` al JSON autorizado. Después de las instrucciones se presenta la referencia cronológica de proyectos y, al final, los hechos temporales con la comparación conjunta de estudios y proyectos. |
| `agent/agent.md` | Instrucciones 1.0.11: consultar los cálculos, distinguir jornadas, comparar todos los proyectos con estudios y aclarar periodos ambiguos. |
| `tests/unit/test_temporal_facts.py` | Diez casos sobre duración, jornadas desconocidas, concurrencia, exclusión de proyectos académicos, términos y copias. |
| `tests/integration/test_temporal_context.py` | Verifica la incorporación de datos correctos aun cuando el historial contenga el total anterior incorrecto. |

El módulo recibe datos ya validados; no reemplaza la validación del perfil. El JSON original no se edita y el historial no convierte una respuesta previa errónea en un hecho. La salida del LLM no se sustituye por respuestas prefabricadas.

## Comprobación en PowerShell

Con Ollama abierto, desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

Resultado esperado actual: **477 passed** (464 unitarias y trece integraciones), sin solicitudes reales en pytest. En el programa, escribir de una en una:

```text
/iniciar
Cuéntame brevemente tu aporte al proyecto Inventario Aula.
¿Qué tecnologías utilizaste en MesaFaro?
De los proyectos mencionados, cuéntame el orden en el que los realizaste.
¿Durante qué meses coincidieron?
¿Cuál terminaste primero y cuándo terminó cada uno?
¿Cuantos meses trabajaste en total?
¿En el tiempo que no trabajabas en ellos que realizabas?
¿Terminaste primero tus estudios o tus proyectos? y en que orden
¿Ese total equivale a meses de jornada completa? Desglosa las jornadas sin inventar las horas.
/salir
```

Se espera que conserve el orden correcto de proyectos, responda 21 meses calendario laborales incluyendo la práctica, distinga jornadas e incluya MesaFaro al comparar con los estudios. La pregunta sobre periodos sin trabajar puede recibir una aclaración; no debe prolongar los estudios más allá de diciembre de 2025 ni fabricar actividades para periodos sin datos.

Si no se encuentra el modelo, comprobar `ollama list` y `OLLAMA_MODEL`. Si vuelve a omitir un proyecto o confunde los meses, conservar la transcripción para revisarla sin cambiar el perfil. Al terminar debe aparecer el original intacto. La verificación semántica del usuario sigue pendiente y esta unidad no garantiza consistencia universal.

## Intentos reales conservados

La evidencia [ecb63914](../../outputs/results/temporal-facts-ecb639143776469692bf7a3be5051070.json), con instrucciones **1.0.9**, contiene nueve turnos reales de la conversación ampliada y una regresión con una copia del historial que incluía la respuesta anterior incorrecta. Las diez llamadas terminaron completas y conservaron los archivos. El total fue 21 meses, la comparación incluyó Inventario Aula, estudios y MesaFaro, y el desglose distinguió nueve meses parciales y nueve completos. Ante la pregunta ambigua eligió condicionalmente la transición entre práctica y rol junior, en vez de preguntar el periodo. Al corregir el total anterior empezó con «sí», aunque después dio 21 meses. Se conservó el texto y se ajustaron esos detalles.

La evidencia [0a35c3f2](../../outputs/results/temporal-facts-0a35c3f20ad84ea28f0ee1f814c11f5f.json), con **1.0.10**, contiene cinco consultas con copias de los contextos anteriores. Pidió el periodo y reconoció el error del total, manteniendo 21 meses. Sin embargo, volvió a omitir MesaFaro en la comparación con estudios. En el desglose de jornadas dio los roles sin los dos periodos de nueve meses y añadió una rectificación innecesaria. No se registra ese intento como aprobado semánticamente.

La revisión **1.0.11** conserva la aclaración del periodo, distingue corregir un número erróneo de explicar jornadas de un número correcto y presenta al final la secuencia completa de estudios y proyectos. Las pruebas dependientes se actualizaron para el nuevo orden de referencias. Los historiales de prueba con errores son copias identificadas; no modifican el perfil ni implementan reapertura de sesiones.

## Revisión final con instrucciones 1.0.11

La suite final terminó con **451 passed in 18.36s**: 439 casos unitarios y doce integraciones. Son diez unitarias y una integración nuevas; las pruebas del formato del sistema se adaptaron a las referencias derivadas. No hubo solicitudes reales en pytest ni dependencias nuevas.

La evidencia [cb43fd58](../../outputs/results/temporal-facts-cb43fd58aa77453b80a6d8eafc13f389.json) conserva seis consultas reales con gemma4:e4b, usando copias identificadas de los contextos de la prueba inicial y una consulta sin historial. No se reabrieron sesiones guardadas y no se reescribieron respuestas anteriores.

| Caso | Observación final de la revisión del agente |
| --- | --- |
| Periodo ambiguo | Pide especificar el periodo, sin escoger un intervalo ni inventar actividades. |
| Historial con total anterior erróneo | Da 21 meses calendario incluyendo práctica y rol posterior. Comienza con «sí» y no reconoce explícitamente el error anterior: queda como matiz de autocorrección verbal bajo observación. |
| Estudios y proyectos | Incluye Inventario Aula en noviembre de 2025, término de estudios y titulación en diciembre de 2025, y MesaFaro en septiembre de 2026. |
| Jornada y calendario | No equipara el total a jornada completa; distingue 3 meses de práctica, 9 parciales y 9 completos, sin inventar horas. |
| Total sin historial | Responde 21 meses: 3 de práctica y 18 como junior. |
| Regresión de orden de inicio | Conserva MesaFaro en abril de 2025 antes de Inventario Aula en agosto de 2025. |

Las seis respuestas terminaron completas con stop y sin errores técnicos; las llamadas sumaron **110,27 s**, con máximo de **36,75 s**. La entrada máxima informada fue **6550 tokens**. La prueba cubre esos contextos breves, no valida entrevistas completas de veinte preguntas ni explica la variación de latencia.

La huella de sistema final es `351DA8FCD6D6CC963F307BAF931DDA18BDF6333557D03906ED0A36C77408051F`; la del archivo de instrucciones 1.0.11 es `3058B4797EFC654FF656DEDA9D1BE3E93420015D3D06451FCFADEEA8FBA17B05`. El perfil, puesto y configuración mantienen sus hashes originales y la referencia **2026-10-20**. Cada ejecución conservó también las instrucciones que había cargado. API externa desactivada.

Quedan verificadas en esta muestra las cifras y la comparación completa; la forma de reconocer un error previo no es uniforme y no se certifica como resuelta en todos los casos. Se mantiene pendiente la comprobación del usuario antes de otra unidad.

## Comprobación del usuario

El usuario obtuvo **451 passed in 19.21s** y cuatro respuestas completas en consola: 21 meses incluyendo práctica, nueve meses parciales y nueve completos en el rol junior, la secuencia completa Inventario Aula → estudios/titulación → MesaFaro y una petición de precisar el periodo ambiguo. El archivo original quedó intacto. Las respuestas tardaron 8,68; 12,16; 15,79 y 8,25 segundos. Se registraron en [temporal-user-confirmation-4ff8d4818cd74151bb2f0990d0afd65e.json](../../outputs/results/temporal-user-confirmation-4ff8d4818cd74151bb2f0990d0afd65e.json) sin generar nuevas respuestas para esa revisión.

Queda confirmada la corrección acotada de cifras, jornadas, comparación y aclaración en esa muestra. El reconocimiento verbal de una respuesta previa incorrecta no se ejercitó y permanece bajo observación. Se continuó con la unidad 7.2 de la misma etapa aprobada, centrada en metadatos y registro técnico de sesiones; no se cambiaron las instrucciones 1.0.11.
