# Corrección del orden cronológico de los proyectos

Esta unidad corrige una incidencia detectada al comprobar el historial en memoria. No añade funciones de otra unidad de la Etapa 7.

## Incidencia observada

El usuario obtuvo **432 passed in 16.65s** y seis respuestas en consola con `gemma4:e4b`. Las cuatro primeras conservaron la referencia a Inventario Aula; la quinta describió tecnologías de MesaFaro. La sexta mostró una inconsistencia:

| Campo | Registro |
| --- | --- |
| Pregunta | «de los proyectos mencionados cuentame el orden en el que los realizaste» |
| Respuesta original | «Primero realicé el proyecto académico Inventario Aula, y posteriormente trabajé en el proyecto profesional MesaFaro.» |
| Referencia | MesaFaro: abril de 2025 a septiembre de 2026. Inventario Aula: agosto a noviembre de 2025. |
| Tipo de problema | Invierte el orden por inicio y presenta como sucesivos periodos que se solapan. |
| Esperado | Si se utiliza el inicio como criterio, MesaFaro primero e Inventario Aula después; ambos coinciden de agosto a noviembre de 2025. |
| Observado | Inventario Aula aparece primero, sin fechas ni aclaración del solapamiento. |
| Acción correctiva | Dar al modelo el orden y la intersección de periodos calculados desde el perfil, y distinguir el inicio del término y del orden de mención. |

El modelo mencionó los proyectos en el mismo orden en que aparecieron en esa conversación. Esa coincidencia no demuestra la causa interna de la respuesta. El archivo del candidato permaneció intacto, lo que no impidió el error semántico.

## Cambios

En `harness/prompt_builder.py`, `_project_chronology()` construye un índice adicional `project_chronology` dentro del sistema:

- `by_start_month`: identificador, nombre, inicio y término de cada proyecto, ordenados por inicio.
- `by_end_month`: los mismos datos, ordenados por término.
- `overlaps`: pares de proyectos y meses comunes a ambos periodos.

Las fechas del perfil ya están validadas en formato `AAAA-MM`; se comparan como meses completos. Una intersección que incluya un mismo mes se conserva a esa precisión, sin deducir días. Si dos proyectos empiezan el mismo mes, su posición en la lista no demuestra cuál comenzó primero dentro de ese mes. Los identificadores solo estabilizan la presentación en caso de empate.

No se copia un perfil alternativo ni se cambia la fuente. El índice se deriva en cada construcción del contexto y se mantiene separado de los mensajes del historial. No se inspecciona la pregunta para elegir una respuesta predefinida.

`agent/agent.md` pasa a **1.0.8**. Indica que se consulte esa cronología, que se explicite el criterio de inicio cuando la pregunta no indique otro, que se reconozcan los solapamientos y que se corrija una respuesta previa incompatible con las fechas. Después de las instrucciones se añade una vista breve de ambas listas y sus solapamientos, bajo `REFERENCIA_CRONOLOGICA_DERIVADA`. Es una presentación de los datos calculados, independiente de la pregunta; no es una respuesta prefabricada que sustituya la salida del modelo. El historial y los adaptadores siguen utilizando sus contratos anteriores. Se actualizaron las pruebas del formato del sistema para distinguir instrucciones y esta referencia final.

## Fechas esperadas

| Proyecto | Tipo | Inicio | Término |
| --- | --- | --- | --- |
| MesaFaro | Profesional | Abril de 2025 | Septiembre de 2026 |
| Inventario Aula | Académico | Agosto de 2025 | Noviembre de 2025 |

Por inicio, MesaFaro va primero. Por término, Inventario Aula va primero. Hubo coincidencia de agosto a noviembre de 2025. No se presenta toda la experiencia como una sucesión sin solapamientos.

## Comprobación en PowerShell

Con Ollama abierto, en la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -m pytest tests\unit tests\integration -q --tb=short
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview
```

La suite actual debe mostrar **477 passed** (464 unitarias y trece integraciones). Las pruebas de Python no consultan modelos reales.

Escribir en la consola estas entradas, de una en una y esperando cada respuesta:

```text
/iniciar
Cuéntame brevemente tu aporte al proyecto Inventario Aula.
¿Qué tecnologías utilizaste en ese proyecto?
¿Se usó con clientes comerciales o en producción?
¿Cómo se llamaba el proyecto de mi primera pregunta?
¿Puedes explicar que tecnologias utilizaste en tu proyecto MesaFaro?
de los proyectos mencionados cuentame el orden en el que los realizaste
¿Durante qué meses coincidieron ambos proyectos?
¿Cuál terminaste primero y cuándo terminó cada uno?
/salir
```

Se espera el orden por inicio y los meses de la tabla; al preguntar por término, debe reconocer que Inventario Aula terminó antes. Las respuestas pueden variar en su redacción. Debe conservarse el original y la API externa debe seguir desactivada.

Si aparece «modelo no encontrado», comprobar `ollama list` y la selección `OLLAMA_MODEL`. Si la respuesta vuelve a invertir las fechas, conservar la transcripción; no cambiar el perfil para ajustarlo a lo que dijo el modelo.

Esta ayuda de contexto no certifica fidelidad universal. La verificación del usuario se espera antes de continuar con otra unidad.

## Pruebas y primer intento conservado

Ocho casos nuevos en `tests/unit/test_project_chronology.py` verifican el índice del perfil real, independencia del orden de los datos y del historial, periodos separados, meses compartidos en los límites, contención, cambio de año y coincidencia del mes inicial. Se actualizaron las comprobaciones del objeto de contexto y la integración con los archivos reales. La suite terminó con **440 passed in 16.95s**, sin solicitudes reales en pytest. Estas pruebas verifican el cálculo, no obediencia del modelo.

El [registro de la incidencia del usuario](../../outputs/results/chronology-user-e7ebfa8766304c978a48c45cccd75d37.json) conserva la pregunta, respuesta, antecedentes y acción propuesta. No se ha editado la respuesta original.

La primera repetición real, con instrucciones **1.0.6**, se conserva en [5a66f70b](../../outputs/results/project-chronology-5a66f70bc95a46ec8e65d8915c8decf2.json). Incluye ocho turnos reales y dos regresiones con historiales de prueba claramente marcados. Las diez llamadas terminaron completas y los archivos quedaron intactos. El caso original dio MesaFaro primero con abril de 2025; la repregunta de coincidencia dio agosto a noviembre de 2025; por término dio Inventario Aula primero, noviembre de 2025, frente a septiembre de 2026. Una copia con la respuesta errónea anterior se corrigió al contrastar las fechas.

**Persistió una contradicción en otro orden de mención:** en el caso `reversed-mention-order` dijo «Comencé con el proyecto de Inventario Aula en agosto de 2025» y después «Posteriormente, empecé a trabajar en MesaFaro en abril de 2025». Las fechas eran literales, pero «posteriormente» invertía su relación. No se considera esa prueba semánticamente aprobada. La versión 1.0.7 precisó que la respuesta siguiera una lista por fecha de inicio y comprobara los conectores temporales; se repitieron ambos órdenes y los demás casos cronológicos.

Los historiales con una respuesta errónea son copias usadas para probar corrección de antecedentes: no son un cambio del perfil, una reapertura de sesiones ni una nueva función del producto. Las evidencias conservan su origen y los textos enviados.

### Segundo intento: criterio de término

La evidencia [c09c1a6a](../../outputs/results/project-chronology-c09c1a6a0ae044e8b40b42a7189c2835.json), con **instrucciones 1.0.7**, conserva cinco regresiones. El caso original y el otro orden de mención respondieron con MesaFaro primero por inicio. El historial con un error previo se rectificó. La consulta sin historial dio fechas y solapamiento correctos, aunque enumeró primero Inventario Aula sin ordenar explícitamente la frase.

Al preguntar «¿Cuál terminaste primero y cuándo terminó cada uno?», dijo «Ordenando por fecha de inicio, el primer proyecto fue Inventario Aula…». La posición coincidía con el término, pero la etiqueta y la afirmación de que ese era el orden de inicio eran incorrectas. No se considera aprobada esa respuesta. Se añadió en 1.0.8 la secuencia por término ya calculada y una referencia legible de ambos criterios al final del sistema. Se conserva íntegra la evidencia fallida.

## Revisión final con instrucciones 1.0.8

La suite final terminó con **440 passed in 16.94s**: 429 unitarias y once integraciones. La vista legible y el índice se comprobaron para inicio y término; las pruebas dependientes distinguen ahora el texto de instrucciones de la referencia derivada final. No se incorporaron dependencias.

La evidencia [74e4d7da](../../outputs/results/project-chronology-74e4d7da5b864355a82644a3a04fd85a.json) conserva seis llamadas reales con gemma4:e4b: cinco regresiones cronológicas y un control de instrucciones internas. Se reutilizaron copias de los historiales de prueba anteriores para comparar el mismo contexto con el sistema revisado. No se reabrieron sesiones ni se sobrescribieron los textos del usuario.

| Caso | Observación de la revisión final |
| --- | --- |
| Conversación original: Inventario Aula y luego MesaFaro mencionados | Por fecha de inicio, MesaFaro en abril de 2025 e Inventario Aula en agosto de 2025. |
| Otro orden de mención | Conservó el mismo orden de inicio e indicó los periodos correctos de ambos proyectos. |
| Historial con la respuesta errónea insertada en una copia | Rectificó el orden al contrastar las fechas del perfil. |
| Consulta sin historial sobre inicio y coincidencia | MesaFaro primero; coincidencia de agosto a noviembre de 2025. |
| Pregunta por término | Indicó explícitamente «Por fecha de término»: Inventario Aula en noviembre de 2025 y MesaFaro en septiembre de 2026. |
| Petición de mostrar instrucciones | Rechazo breve, sin mostrar el contenido interno. |

Las seis respuestas terminaron con stop, sin errores o cortes, y las llamadas sumaron **80,63 s**. La más lenta tardó **33,63 s**. El proveedor informó como máximo **5253 tokens de entrada** en esta muestra. No se atribuyen estas duraciones a una causa específica ni se valida con ello el presupuesto de conversaciones extensas.

La huella del sistema final es `D979169ECC9392190D63A6BB16BC586D28F7312AD2A768E6C327F193316137AF`; la del archivo de instrucciones 1.0.8 es `39F22FFADC4DA569C2485D5E834A185B8A1ACB8D030C5D7FDBE9B92300E1C9D1`. El perfil, puesto y configuración conservan sus hashes aprobados, la referencia 2026-10-20 y el máximo de veinte preguntas. Cada ejecución real conservó también el archivo de instrucciones que utilizaba.

La revisión del agente encontró corregidos los fallos de orden en estos seis casos. El registro mantiene pendiente la comprobación del usuario; no acredita consistencia universal. Los intentos insuficientes de 1.0.6 y 1.0.7 quedan conservados, y no se continúa a otra unidad de la Etapa 7 antes de recibir el resultado.
