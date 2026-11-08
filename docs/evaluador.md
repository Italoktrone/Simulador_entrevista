# Evaluador de preguntas: rúbrica, decisiones y calibración

[Índice general](../README.md#documentación)

Las secciones fechadas y los registros de etapas describen el estado y las pruebas de su momento.

## Contenido

- [Cierre del MVP del evaluador — 2 de noviembre de 2026](#cierre-mvp-evaluador)
- [Estado de los bloques del evaluador — 2 de noviembre de 2026](#estado-bloques-evaluador)
- [Evaluador provisional de preguntas](#evaluador-preguntas)
- [Evaluación provisional por pregunta](#rubrica)
- [Referencias propuestas para revisión humana](#referencias-evaluacion-propuesta)
- [Propuesta revisada de 40 referencias del evaluador — 2 de noviembre de 2026](#revision-referencias-evaluador)
- [Verificación técnica inicial del evaluador de preguntas](#pruebas-evaluador-preguntas)
- [Diagnóstico y corrección del evaluador local](#correccion-evaluador-local)
- [Estabilización de evidencia del evaluador — 2 de noviembre de 2026](#estabilizacion-evidencia-evaluador)
- [Comparación y aprobación de regla crítica — 2 de noviembre de 2026](#comparacion-regla-critica-evaluador)
- [Regla Crítica y Few-Shot del evaluador — 2 de noviembre de 2026](#calibracion-evaluador-few-shot)
- [Calibración inicial del evaluador con seis demostraciones](#pruebas-calibracion-evaluador-few-shot)
- [Calibración ampliada: Claridad y Neutralidad — 2 de noviembre de 2026](#calibracion-ampliada-claridad-neutralidad)

<a name="cierre-mvp-evaluador"></a>

## Cierre del MVP del evaluador — 2 de noviembre de 2026

### Aceptación y estado

El usuario declaró: «Doy por cerrado y validado el Bloque 11» y aceptó los resultados observados como suficientes para el MVP. Indicó que no se invertirán más recursos intentando obtener inferencia perfecta en casos límite como E11 y E30 con la configuración local evaluada.

**Los doce bloques del plan del evaluador están completados para el MVP.** El Bloque 12, documentación y evidencia, ya estaba implementado; este cierre actualiza su estado y registra las limitaciones aceptadas. No requiere cambios del programa, nuevas inferencias ni repetir las pruebas técnicas.

La aceptación corresponde al alcance práctico del MVP. Los resultados experimentales, las referencias y las discrepancias conservan sus valores; cerrar el bloque no equivale a corregir las predicciones que discrepan.

### Versión y evidencia aceptadas

- Rúbrica 1.1.0 con cuatro criterios y Regla Crítica: cualquier nivel 1 limita el global como máximo a En desarrollo, conservando el porcentaje.
- Cuarenta referencias revisadas 1.1.0 y sus contextos aprobados, con seis demostraciones de desarrollo activas.
- Protocolo de análisis 1.2.0, registros de evaluación 1.3.0 y lectura compatible de sesiones anteriores.
- Calibración ampliada sobre doce casos nuevos fuera de las demostraciones: Claridad 12/12, Neutralidad 9/12 y coincidencia completa de los cuatro criterios/global en 5/12.
- Última suite completa: 1810 pruebas aprobadas, sin fallos, errores u omisiones. No se repitió por este cambio exclusivamente documental.

La [lista de bloques](#estado-bloques-evaluador) contiene el estado final. El [informe de calibración ampliada](#calibracion-ampliada-claridad-neutralidad) conserva método, resultados y límites. La evidencia técnica está en `outputs/results/evaluator-clarity-expanded-verification.json`; la aceptación posterior se registra por separado en `outputs/results/evaluator-mvp-acceptance-20261102.json`.

### Limitaciones aceptadas

- E11 mantiene claridad 3 frente al 4 de referencia y una explicación incompleta; no se atribuye una causa nueva sin evidencia.
- E10/E19 tienen diferencias de anclaje de neutralidad; E30 no detecta una presuposición de revisión no confirmada.
- Persisten diferencias en otros criterios y razones genéricas o incompletas en algunos casos. Las métricas de Claridad/Neutralidad no representan coincidencia completa de todas las notas.
- La latencia medida de los doce casos nuevos válidos fue de 40,62 a 64,50 s. Se conserva el timeout inicial de E11 y su comprobación adicional.
- La discrepancia conocida de comunicación del clasificador sigue documentada en su propio informe.

Se registran como limitaciones de Gemma `gemma4:e4b` en la configuración y muestra evaluadas. No se alteran las referencias para hacerlas coincidir con el modelo ni se afirma precisión universal. No queda una tarea activa de optimización de estos casos dentro del MVP cerrado.

### Trabajo posterior

No quedan bloques obligatorios del plan actual. Una interfaz gráfica o integración con Godot y la evaluación global de sesión con nota 1–7 son ampliaciones fuera del alcance aprobado. Si se solicitan, se planificarán como una fase nueva con objetivos y criterios propios; no son condiciones para cerrar este MVP.

---

<a name="estado-bloques-evaluador"></a>

## Estado de los bloques del evaluador — 2 de noviembre de 2026

**12 de 12 bloques completados dentro del alcance del MVP.** El usuario cerró y validó explícitamente el Bloque 11 el 2 de noviembre de 2026, aceptando los resultados de la calibración como suficientes y las discrepancias restantes como limitaciones conocidas de la configuración evaluada. No quedan bloques obligatorios pendientes. [Acta de cierre y alcance](#cierre-mvp-evaluador).

| Bloque | Trabajo | Estado |
|---|---|---|
| 1 | Auditoría y diseño del evaluador | Completado |
| 2 | Rúbrica de cuatro criterios y 16 descriptores | Completado para el MVP; acuerdos aprobados |
| 3 | Pesos, umbrales y reglas de puntuación | Completado; máximo En desarrollo ante cualquier criterio en 1 |
| 4 | Contratos JSON y validación de evidencia | Completado; protocolo 1.2.0 y registro 1.3.0 |
| 5 | Motor matemático local | Completado |
| 6 | Evaluación semántica de cada pregunta | Completado para el MVP; limitaciones documentadas |
| 7 | Explicación, sugerencia y reformulación | Completado para el MVP; limitaciones documentadas |
| 8 | Integración con entrevista y candidato | Completado |
| 9 | Registro, errores y compatibilidad | Completado; diagnóstico por campo y regla |
| 10 | Preparar y aprobar 40 referencias del evaluador | Completado; versión 1.1.0 y contextos aprobados |
| 11 | Pruebas, calibración y ajustes | Cerrado y validado por el usuario para el MVP; Claridad 12/12, Neutralidad 9/12 |
| 12 | Documentación y evidencia de lo implementado | Completado; cierre y limitaciones actualizados |

Dentro del bloque 11, el Few-Shot del clasificador corrigió dos de tres discrepancias conocidas; queda la pregunta sobre comunicación. La estabilización del evaluador recuperó los dos fallos técnicos de la sesión reciente. La calibración posterior pasó de 0/4 a 3/4 coincidencias completas en casos conocidos; tres eran demostraciones y el cuarto conserva una diferencia de claridad. El caso amplio de informática coincide con la referencia y reconoce la ausencia de objetivo explícito. [Resultados, alcance y límites](#pruebas-calibracion-evaluador-few-shot).

El conjunto de calibración activo es `data/reference_questions/evaluacion_calidad_aprobada.json`. Las 40 referencias aprobadas del clasificador son otro conjunto independiente.

La [revisión editorial 1.1.0](#revision-referencias-evaluador) conserva el original y documenta los cambios aprobados. La [Regla Crítica](#comparacion-regla-critica-evaluador) ya limita a En desarrollo el global con cualquier criterio en 1 y cambia tres categorías derivadas, sin modificar porcentajes. Las seis demostraciones se validan contra las referencias aprobadas y excluyen comprobación conocida. [Implementación y calibración](#calibracion-evaluador-few-shot).

Última verificación técnica: 1810 pruebas aprobadas, sin fallos. Se añadió la instrucción de separación Claridad/Neutralidad y se evaluaron doce casos nuevos ajenos a las seis demostraciones. E11 conserva claridad 3 frente al 4 aprobado y una razón incompleta; la aceptación del MVP no modifica ese resultado. [Resultados de la calibración ampliada](#calibracion-ampliada-claridad-neutralidad). E11, las diferencias de neutralidad y las demás observaciones quedan registradas como limitaciones aceptadas, sin trabajo adicional de calibración requerido para cerrar este plan.

Godot, una interfaz gráfica y la evaluación global de sesión con nota 1–7 pertenecen a un desarrollo posterior, fuera de estos doce bloques. No se inicia esa fase con este cierre.

---

<a name="evaluador-preguntas"></a>

## Evaluador provisional de preguntas

El MVP está cerrado y aceptado por el usuario: doce de doce bloques completados. Las limitaciones semánticas observadas quedan documentadas y no requieren seguir optimizando la configuración local para cerrar este alcance. [Acta de cierre](#cierre-mvp-evaluador).

Implementado como extensión opcional del simulador. Conserva el perfil ficticio, puesto, configuración de entrevista, instrucciones del candidato y definiciones del clasificador. Los tres archivos antes reservados (`question_evaluator.py`, `scoring.py`, `feedback.py`) tienen ahora responsabilidades ejecutables separadas. No se añadieron dependencias.

### Uso desde PowerShell

Desde `C:\Users\franc\Downloads\Ejemplo_de_proyecto`:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview --evaluate
```

El selector mantiene las opciones local/API ya existentes. Con API se usa el proveedor seleccionado también para el evaluador, mediante otro cliente y presupuesto; esto añade consumo. El programa no cambia de proveedor automáticamente. El inicio sin `--evaluate` conserva el comportamiento anterior.

Alternativa local explícita, sin cargar el archivo privado:

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_ALLOW_EXTERNAL_API = 'false'
$env:OLLAMA_MODEL = 'gemma4:e4b'
.\.venv\Scripts\python.exe -X utf8 -m scripts.run_interview --evaluate --extractive-context
```

`--evaluate` activa también `--classify`. `--evaluator-model` permite elegir un modelo independiente. `--evaluation-config` permite una configuración de rúbrica alternativa; el archivo de entrevista y el perfil no se modifican. No es obligatorio usar un modelo diferente al candidato: las llamadas e instrucciones son independientes, aunque eso no garantiza independencia estadística de sus errores.

### Flujo y estados

1. Se registra la intervención y se clasifica con la política actual.
2. Si la política pide aclaración, declara no evaluable o tiene un error técnico, se registra la omisión apropiada sin invocar candidato ni evaluador. La etiqueta no evaluable de esta rama no recibe revisión semántica adicional en el MVP; corregir falsos negativos de esa política queda pendiente.
3. Si se autoriza la pregunta, se captura el contexto anterior. Se genera y muestra la respuesta del candidato.
4. El evaluador recibe pregunta, cargo, configuración, competencia/objetivo opcionales, fragmentos de contexto anterior y clasificación auxiliar. Nunca recibe la respuesta recién generada.
5. Se valida JSON estricto, contrato, niveles enteros, citas literales y turnos autorizados. El protocolo compacto 1.2.0 comparte citas mediante índices y solicita como máximo una sugerencia; Python expande las referencias sin inventar niveles ni evidencias. En Ollama, el formato de generación exige al menos un índice para niveles numéricos y ninguno para null; las fuentes de contexto solo admiten números presentes en esta petición. Una sugerencia ausente no invalida los criterios observados. JSON/contrato inválidos permiten una única reparación. Los rechazos de contrato registran `validation.path`, `rule` y `message` en cada intento, y esa información controlada orienta la reparación. No se reinyecta texto rechazado ni mensajes privados de excepciones.
6. Python calcula nivel y feedback; se registra antes de recibir otra pregunta y antes de guardar el cierre por límite.

El candidato continúa disponible si la evaluación falla. El registro distingue fallo de clasificación, error del candidato y fallo del evaluador. Una cancelación interrumpe y conserva el turno completado; no se trata como un nivel bajo.

El evaluador tiene 2048 tokens máximos por generación y 90 segundos de espera de lectura por defecto, configurables. No tiene reintentos automáticos de transporte. El límite HTTP es de inactividad de lectura, no un plazo absoluto de pared; con una reparación puede haber dos esperas. La latencia real debe medirse con el proveedor elegido antes de considerar satisfactoria la inmediatez.

### Contratos y archivos

- `agent/evaluator.md`: instrucciones independientes del candidato y del clasificador.
- `config/evaluation.json`: 16 descriptores, pesos, umbrales y límites.
- `harness/evaluation_contract.py`: validación estructural y relaciones entre análisis y cálculo.
- `schemas/llm_question_evaluation.schema.json`: solamente datos interpretativos del LLM.
- `schemas/question_evaluation.schema.json`: registro completo calculado por el programa.
- `harness/evaluation_log.py`: correspondencia con pregunta, clasificación y contexto anterior.
- `harness/quality_references.py`: referencias y comparación con cobertura y error ordinal absoluto.

Los desacuerdos incluyen la clasificación original, interpretación alternativa, motivo, cita y estado pendiente de revisión. Nunca se sobrescribe el resultado original. Si un error del clasificador impide enviar la pregunta, no se ejecuta el evaluador para eludir esa política. Puede probarse de forma independiente mediante casos de referencia.

### Persistencia y compatibilidad

Sesiones con evaluación usan 1.3.0 e incorporan `evaluation_policy` y `evaluations` en la raíz; se conservan los formatos originales de intervenciones e intentos. El guardado valida que cada intervención tenga resultado u omisión, identidad correcta y contexto exclusivamente anterior. Se verifica de nuevo el cálculo y la derivación del feedback. Las sesiones 1.0.0, 1.1.0 y 1.2.0 siguen leyéndose sin migración ni reescritura.

El análisis compacto/expandido conserva 1.2.0 y los registros nuevos usan 1.3.0, con `few_shot` obligatorio. Los registros 1.0.0/1.1.0/1.2.0 conservan su lectura y sus reglas originales. Todo intento nuevo rechazado por contrato requiere diagnóstico; un intento válido, error de transporte o corte de salida lleva `validation=null`. La huella del prompt comprende las instrucciones realmente seleccionadas, descriptores, esquema y demostraciones si están activas. El formato específico de Ollama se deriva de los números de `request.context_turns`, conservados en el registro.

La rúbrica 1.1.0 aplica el máximo En desarrollo ante cualquier criterio en 1, sin modificar promedio ni porcentaje. La rúbrica 1.0.0 conserva su política histórica. Las sesiones originales no se migran.

`evaluation_generation_schema()` adapta únicamente el formato nativo: mantiene los límites de longitud y retira el patrón de texto no blanco que puede interferir con ellos en el conversor de Ollama. La validación Python continúa usando `llm_evaluation_schema()` completo, incluido ese patrón. Los textos vacíos, en blanco o demasiado largos siguen siendo inválidos. La adaptación no se aplica al candidato ni al clasificador.

El feedback no se utiliza como mensaje del candidato. El registro no contiene claves, salidas rechazadas ni razonamiento interno. Las citas y explicaciones aceptadas son datos de texto, no instrucciones ejecutables. El candidato y las sesiones originales permanecen intactos.

### Referencias aprobadas y demostraciones

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.evaluate_questions --preview --split todos
```

La vista previa es completamente local y no crea clientes. El conjunto predeterminado es `data/reference_questions/evaluacion_calidad_aprobada.json`: las 40 referencias revisadas 1.1.0 y sus contextos fueron aprobados por el usuario. Los niveles por criterio coinciden con la propuesta aprobada; tres globales se recalcularon por la Regla Crítica también aprobada. Se conservan ambos originales anteriores. No se cambian referencias para mejorar métricas.

Seis demostraciones (E03/E05/E07/E08/E12/E15), todas de desarrollo, se incorporan por defecto al evaluador. Sus fuentes y descriptores están fijados por huellas. No se incorporan los diez casos de comprobación conocida ni respuestas del candidato actual. `--no-evaluator-examples` desactiva las demostraciones en `scripts.start_interview --evaluate`, `scripts.run_interview --evaluate` y `scripts.evaluate_questions`. La configuración histórica 1.0.0 las desactiva con motivo registrado; un cargo distinto al de los ejemplos también las desactiva. Cambiar los descriptores requiere ejemplos compatibles o desactivarlos explícitamente. [Selección y calibración](#calibracion-evaluador-few-shot).

Un piloto pequeño puede ejecutarse así:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.evaluate_questions --case-id E01 --case-id E03
```

Este comando consulta el proveedor del entorno; sin aprobación de los casos se detiene antes de crear un cliente. El informe conserva análisis, evidencia, diferencias, cobertura, error absoluto por criterio, versiones y consumo disponible. Una predicción ausente no se cuenta como error ordinal cero ni como acierto. Los casos de comprobación conocida se ejecutan por separado; no deben usarse reiteradamente para ajustar el prompt y presentarlos luego como prueba independiente.

### Alcance de la validación

Las pruebas con HTTP simulado comprueban operación y contratos, no que el modelo interprete correctamente cada criterio. Las referencias revisadas ya están aprobadas; la calibración del modelo continúa. Tras la sesión real 6255d38d, se corrigió el protocolo y se ejecutó un piloto local de dos preguntas con contexto original: ambas aceptadas al primer intento, 61,76 y 36,83 segundos. Es una comprobación histórica del componente, no del flujo completo ni de precisión general. [Diagnóstico y límites de la corrección](#correccion-evaluador-local).

El Few-Shot del clasificador corrigió dos de sus tres discrepancias conocidas; la de comunicación se conserva como limitación documentada. El usuario aceptó la evidencia disponible y cerró la calibración del MVP. La precisión educativa general permanece fuera de lo demostrado; no se requiere ampliar los ensayos para completar estos doce bloques.

---

<a name="rubrica"></a>

## Evaluación provisional por pregunta

### Criterios y evidencias observables

La versión inicial contiene cuatro criterios, cada uno con niveles enteros de 1 a 4 y cuatro descriptores observables. La definición ejecutable está en `config/evaluation.json`. Pertinencia pregunta **qué** información es útil para el cargo; adecuación metodológica pregunta **cómo** obtener el tipo de evidencia buscado. Claridad analiza comprensión y alcance; neutralidad analiza inducción, presión y presuposiciones. No se penaliza automáticamente una etiqueta cerrada, directiva, compuesta o mixta.

### Adecuación al contexto y mezclas pertinentes

Una aclaración factual puede apoyar una entrevista conductual o situacional. Se utiliza el objetivo explícito cuando exista; si es null, solo la intención observable. La competencia puede ser null y no se inventa una selección: el cargo proporciona el marco disponible. El evaluador recibe fragmentos de hasta tres turnos completos anteriores, con límites configurables y señal de truncamiento; nunca la respuesta del turno evaluado ni el perfil privado completo.

### Escala interna

1 Inicial; 2 En desarrollo; 3 Logrado; 4 Destacado. Son anclajes ordinales. La media ponderada supone una separación numérica uniforme como convención práctica del MVP, no demuestra intervalos psicológicos iguales ni validez científica. Cada nivel observado exige cita literal, descriptor y justificación breve; una cita válida demuestra procedencia, no corrección de la interpretación.

### Pesos y cálculo local

Pesos iniciales: pertinencia 35 %, adecuación metodológica 30 %, claridad 20 %, neutralidad 15 %. Se aceptan únicamente pesos finitos no negativos, con suma 100 dentro de tolerancia absoluta 0,000001 puntos porcentuales. Dentro de esa tolerancia se normalizan explícitamente por su suma real al calcular; fuera de ella se rechaza la configuración, sin repararla. La configuración original queda íntegra en la sesión.

`P = suma(peso_i × nivel_i) / suma(pesos)`; `S = (P - 1) / 3 × 100`. Todos en 1 → 0; todos en 2 → 33,33; todos en 3 → 66,67; todos en 4 → 100. Se utiliza Decimal y ROUND_HALF_UP a dos decimales para el registro. No se redondea antes de determinar el nivel. El LLM no produce porcentajes, pesos ni nivel global.

### Rangos y cuatro niveles visibles

Se compara P sin redondear: [1; 1,5) Inicial; [1,5; 2,5) En desarrollo; [2,5; 3,5) Logrado; [3,5; 4] Destacado. Los tres umbrales son configurables. La Regla Crítica aprobada limita el global como máximo a **En desarrollo si cualquiera de los cuatro criterios tiene nivel 1**, incluso si ese criterio tiene peso cero. Se conservan P y S. `critical_cap_applied=true` indica que la regla redujo la categoría; si ya era Inicial o En desarrollo, no se eleva ni se marca una reducción inexistente. Ejemplo: [4,4,4,1] produce P=3,55 y S=85, pero nivel En desarrollo. Un resultado parcial sigue sin global.

Esta regla corresponde a la rúbrica 1.1.0. Las sesiones con rúbrica 1.0.0 conservan su política original de máximo Logrado y su explicación; no se recalculan ni se reescriben. La configuración histórica está en `config/evaluation.legacy-1.0.0.json`.

### Criterios no observables y preguntas ambiguas

No se imputa 2,5 ni se renormalizan criterios faltantes. Se preservan los niveles observados, pero con cualquier criterio null no hay puntuación ni nivel global. `parcial` conserva alguno observado; `no_disponible` identifica ausencia completa de evidencia o un fallo técnico; `no_evaluable` corresponde a intervenciones fuera de la rúbrica, no a preguntas deficientes; `no_ejecutada` registra una omisión por la política del clasificador, error del candidato o interrupción. Ninguno es un quinto nivel de desempeño. Un objetivo o una competencia sin seleccionar no obliga por sí solo a declarar todos los criterios insuficientes.

### Explicación y sugerencia inmediata

La respuesta se presenta antes de esperar al evaluador. Después se muestran nivel o estado, explicación y una sugerencia prioritaria. Python selecciona la deficiencia por déficit ponderado y deriva la presentación de la evidencia validada. La reformulación es opcional y solo se muestra para un criterio observado inferior a 4. Cuando no se detectan deficiencias, se recomienda mantener la formulación sin inventar un error. No se realiza una segunda llamada de redacción ni se añade feedback a la memoria del candidato.

### Reproducibilidad y versionado

Rúbrica 1.1.0; protocolo compacto y análisis expandido 1.2.0; registro de evaluación 1.3.0; sesiones con evaluación 1.3.0. Los registros nuevos incluyen metadatos de las seis demostraciones aprobadas y la huella del prompt realmente utilizado. Los registros 1.0.0/1.1.0/1.2.0 y sus rúbricas anteriores conservan su validación y presentación. Los contratos del clasificador no cambian. Se preservan configuración, contexto real utilizado, clasificación auxiliar, análisis, derivados, intentos, errores controlados con campo y regla, tiempos y tokens disponibles. La reproducción matemática es determinista; la evaluación semántica del modelo no está garantizada como determinista.

### Validación y limitaciones

Hay pruebas de límites, estados, citas/contexto, reparación única, errores, protección del historial, cierre al turno 20, persistencia, compatibilidad anterior y bloqueo de referencias pendientes. El usuario aprobó las 40 referencias revisadas 1.1.0 y sus contextos el 2 de noviembre de 2026. El conjunto activo está en `data/reference_questions/evaluacion_calidad_aprobada.json`; se conserva la propuesta original. Incluye preguntas buenas, deficientes, contexto ausente, saludos, mezcla y clasificaciones auxiliares erróneas. Su división 30/10 es conocida y no constituye un conjunto ciego. No se ejecutan casos pendientes como referencia aprobada.

La calibración con seis demostraciones de desarrollo se describe en `docs/evaluador.md#calibracion-evaluador-few-shot`. La aprobación de los niveles no sustituye medir las predicciones. Se mantienen límites de latencia y de representatividad; no se afirma ausencia universal de sesgos ni validación científica por aprobar pruebas automatizadas.

### Diferencia respecto de una futura evaluación de sesión

La evaluación se aplica por intervención. No calcula nota 1–7, estadísticas globales de habilidad, decisiones de contratación ni evaluación final de la sesión. Godot y la evaluación global siguen fuera del alcance.

---

<a name="referencias-evaluacion-propuesta"></a>

## Referencias propuestas para revisión humana

Estas 40 valoraciones fueron propuestas por el asistente. Ninguna está aprobada. P/E/C/N = pertinencia, adecuación metodológica, claridad y neutralidad. Un guion significa información insuficiente, sin imputación. Las justificaciones por criterio y el contexto literal están en `data/reference_questions/evaluacion_calidad.json`.

| Caso | Pregunta | P/E/C/N | Global propuesto | Contexto |
|---|---|---|---|---|
| E01 | ¿Cómo identificaste y corregiste un error en una aplicación? | 4/4/4/4 | Destacado | Sin historial |
| E02 | ¿Qué harías si una prueba automática comienza a fallar después de un cambio? | 4/4/4/4 | Destacado | Sin historial |
| E03 | ¿Has utilizado Git para controlar versiones? | 3/3/4/4 | Logrado | Sin historial |
| E04 | ¿Qué herramientas utilizaste en tu proyecto académico más reciente? | 3/3/4/4 | Logrado | Sin historial |
| E05 | Cuéntame una ocasión en la que tuviste que pedir apoyo a un compañero. | 4/4/4/4 | Destacado | Sin historial |
| E06 | ¿Cómo explicarías a una persona no técnica un retraso en una tarea? | 4/4/4/4 | Destacado | Sin historial |
| E07 | ¿Qué haces normalmente cuando encuentras un error? | 3/2/4/4 | Logrado | Sin historial |
| E08 | ¿Qué sabes de informática? | 2/2/2/4 | En desarrollo | Sin historial |
| E09 | ¿Cuál es tu color favorito? | 1/3/4/4 | Logrado | Sin historial |
| E10 | ¿Cuántos equipos internacionales de más de cien personas has dirigido? | 1/3/4/3 | Logrado | Sin historial |
| E11 | ¿Verdad que siempre pruebas todo antes de entregar? | 3/2/4/2 | Logrado | Sin historial |
| E12 | Como eres irresponsable, ¿por qué entregaste tarde? | 3/2/3/1 | En desarrollo | Sin historial |
| E13 | ¿Qué aprendiste de una estimación que resultó demasiado optimista? | 4/4/4/4 | Destacado | Turno anterior |
| E14 | ¿Qué hiciste después para comprobar que el problema estaba resuelto? | 4/4/4/4 | Destacado | Turno anterior |
| E15 | ¿Qué hiciste después? | -/-/-/4 | parcial | Sin historial |
| E16 | ¿Y el resultado? | 4/4/4/4 | Destacado | Turno anterior |
| E17 | ¿Qué lenguaje usaste y qué harías si una prueba fallara? | 3/3/3/4 | Logrado | Sin historial |
| E18 | Explica tu proyecto, sus tecnologías, todos sus errores, los requisitos, los plazos y qué harías en otra empresa. | 3/2/2/4 | Logrado | Sin historial |
| E19 | ¿Usaste Python o JavaScript en ese proyecto? | 3/3/4/3 | Logrado | Turno anterior |
| E20 | ¿Qué opción elegiste y qué alternativas descartaste? | 4/4/4/4 | Destacado | Turno anterior |
| E21 | Hola, buenos días. | -/-/-/- | no_evaluable | Sin historial |
| E22 | Gracias por tu respuesta. | -/-/-/- | no_evaluable | Sin historial |
| E23 | (vacía) | -/-/-/- | no_evaluable | Sin historial |
| E24 | Describe cómo comprobarías una consulta SQL antes de publicarla. | 4/4/4/4 | Destacado | Sin historial |
| E25 | ¿Has usado Python? | 3/3/4/4 | Logrado | Sin historial; etiqueta errónea deliberada |
| E26 | Cuéntame cómo resolviste un desacuerdo en tu equipo. | 4/4/4/4 | Destacado | Sin historial; etiqueta errónea deliberada |
| E27 | ¿Qué harías si una entrega no cumpliera los requisitos? | 4/4/4/4 | Destacado | Sin historial; etiqueta errónea deliberada |
| E28 | ¿Cómo demostrarías que nunca cometes errores? | 2/1/3/1 | En desarrollo | Sin historial |
| E29 | ¿Qué periodo de tu trayectoria corresponde a esa estimación? | 3/3/4/4 | Logrado | Turno anterior |
| E30 | ¿En qué parte del proyecto pediste revisión y por qué? | 4/4/4/4 | Destacado | Turno anterior |
| E31 | ¿Para qué sirve una clave primaria en una base de datos? | 4/4/4/4 | Destacado | Sin historial |
| E32 | ¿Cómo organizarías tu trabajo si dos tareas urgentes coincidieran? | 4/4/4/4 | Destacado | Sin historial |
| E33 | Tu solución fue obviamente mala, ¿por qué no elegiste la correcta? | 3/1/2/1 | En desarrollo | Turno anterior |
| E34 | ¿Puedes detallar qué aportaste tú y qué correspondió al resto del equipo? | 4/4/4/4 | Destacado | Turno anterior |
| E35 | ¿Cómo lo hiciste? | 4/4/4/4 | Destacado | Turno anterior |
| E36 | ¿Cómo lo hiciste? | -/-/-/4 | parcial | Sin historial |
| E37 | ¿Cuántos meses duró tu práctica? | 3/3/4/4 | Logrado | Sin historial |
| E38 | ¿Qué experiencia tienes liderando despliegues globales sin supervisión? | 2/3/4/3 | Logrado | Sin historial |
| E39 | ¿Qué cambió después de aplicar esa corrección? | 4/4/4/4 | Destacado | Turno anterior |
| E40 | Cuéntame una dificultad, qué hiciste para resolverla y qué resultado obtuviste. | 4/4/4/4 | Destacado | Sin historial |

### Motivo y objetivo de cada propuesta

- **E01**: Pide una experiencia concreta de depuración, apropiada al puesto junior. Objetivo: Obtener evidencia de resolución de problemas.
- **E02**: Un escenario delimitado permite explicar una estrategia sin atribuir experiencia. Objetivo: Explorar investigación de fallos.
- **E03**: Una pregunta cerrada factual puede ser pertinente dentro de una entrevista conductual. Objetivo: Aclarar una herramienta usada antes de profundizar.
- **E04**: Es pertinente para un junior y no necesita forzar una experiencia laboral. Objetivo: Identificar herramientas del proyecto.
- **E05**: Solicita un episodio propio sin descalificar la petición de ayuda. Objetivo: Explorar colaboración y reconocimiento de límites.
- **E06**: El escenario es apropiado para comunicación y responsabilidad en un cargo junior. Objetivo: Explorar comunicación de dificultades.
- **E07**: Una respuesta habitual no aporta necesariamente un episodio pasado, aunque es pertinente. Objetivo: Obtener un episodio pasado concreto de resolución de problemas.
- **E08**: El alcance amplio no concreta qué conocimiento se desea comprobar. Objetivo: Explorar bases técnicas para el puesto.
- **E09**: El dato es ajeno al puesto; el método factual es adecuado al objetivo declarado y no se penaliza dos veces. Objetivo: Consultar preferencias personales.
- **E10**: Impone una expectativa de trayectoria impropia de este cargo junior. Objetivo: Verificar liderazgo ejecutivo como requisito obligatorio.
- **E11**: La confirmación sugerida favorece una respuesta idealizada en lugar de evidencia concreta. Objetivo: Explorar prácticas reales de pruebas.
- **E12**: La descalificación y atribución causal condicionan la respuesta. Objetivo: Explorar una demora mencionada previamente.
- **E13**: La repregunta explora aprendizaje sobre un antecedente disponible. Objetivo: Explorar aprendizaje de una estimación descrita.
- **E14**: El antecedente de depuración permite interpretar una repregunta breve. Objetivo: Explorar verificación posterior a una corrección relatada.
- **E15**: Sin antecedente no se identifica la acción previa ni el objetivo; no se inventa contexto. Objetivo: No seleccionado; no se inventa uno.
- **E16**: La brevedad no reduce claridad cuando el antecedente permite interpretarla. Objetivo: Conocer el efecto de una mejora relatada.
- **E17**: Dos demandas relacionadas pueden ser manejables sin penalización automática por mezcla. Objetivo: Combinar aclaración factual y razonamiento situacional.
- **E18**: Acumula varias demandas y cambia de experiencia a hipótesis sin organizar el alcance. Objetivo: Explorar un proyecto de forma ordenada.
- **E19**: Las alternativas sirven para aclarar, pero pueden limitar una respuesta distinta. Objetivo: Precisar un lenguaje de un proyecto previamente identificado.
- **E20**: Pregunta por la decisión y su contraste sin imponer la opción correcta. Objetivo: Explorar una decisión técnica relatada.
- **E21**: Es un saludo, no una pregunta de entrevista. Objetivo: No seleccionado; no se inventa uno.
- **E22**: Es un agradecimiento sin una nueva petición de información. Objetivo: No seleccionado; no se inventa uno.
- **E23**: La intervención vacía no debe puntuarse. Objetivo: No seleccionado; no se inventa uno.
- **E24**: La petición imperativa es evaluable y apropiada para razonamiento técnico. Objetivo: Explorar comprobación de una consulta.
- **E25**: No se rebaja por ser cerrada ni por una etiqueta auxiliar directiva errónea. Objetivo: Comprobar una base técnica.
- **E26**: La evidencia de una experiencia prevalece sobre una clasificación situacional errónea. Objetivo: Explorar colaboración mediante una experiencia.
- **E27**: No es directiva solo por solicitar explicar una actuación. Objetivo: Explorar actuación frente a requisitos incumplidos.
- **E28**: Exige una afirmación absoluta y presupone un desempeño sin errores. Objetivo: Explorar cómo reconoce y gestiona errores.
- **E29**: Una aclaración factual puede apoyar el análisis conductual. Objetivo: Aclarar la ubicación temporal de un ejemplo relatado.
- **E30**: Delimita una acción propia y su motivo sin exigir autonomía senior. Objetivo: Explorar límites y colaboración en un proyecto relatado.
- **E31**: Una definición técnica es pertinente si el objetivo del turno es comprobar fundamentos. Objetivo: Comprobar una base de SQL.
- **E32**: El escenario permite explicar prioridades sin exigir decidir unilateralmente. Objetivo: Explorar organización y comunicación de prioridades.
- **E33**: Impone el juicio de que la alternativa fue incorrecta sin permitir justificarla. Objetivo: Explorar una decisión técnica relatada.
- **E34**: Delimita responsabilidades sin atribuir todo el proyecto a una sola persona. Objetivo: Distinguir contribución propia de contribución colectiva.
- **E35**: La pregunta breve tiene antecedente suficiente y permite explorar el procedimiento. Objetivo: Profundizar en una acción técnica recién mencionada.
- **E36**: La misma pregunta sin contexto carece de referente; no debe confundirse con una pregunta siempre deficiente. Objetivo: No seleccionado; no se inventa uno.
- **E37**: Una respuesta factual breve cumple el objetivo sin necesitar un relato completo. Objetivo: Aclarar la duración de una experiencia formativa.
- **E38**: Es periférica para un junior y debe distinguirse de responsabilidades obligatorias. Objetivo: Explorar exposición adicional, sin convertirla en requisito del cargo.
- **E39**: El contexto previo permite contrastar el efecto sin sugerir que necesariamente mejoró. Objetivo: Explorar el resultado de una corrección relatada.
- **E40**: Las demandas están relacionadas y organizadas alrededor de un único episodio. Objetivo: Obtener un episodio con acción y resultado.

---

<a name="revision-referencias-evaluador"></a>

## Propuesta revisada de 40 referencias del evaluador — 2 de noviembre de 2026

Revisión editorial 1.1.0 aprobada explícitamente por el usuario el 2 de noviembre de 2026, incluidos los 40 casos y sus contextos. No se consultó un modelo ni se usaron predicciones para fijar estos niveles. Las tablas siguientes conservan la propuesta previa a aplicar la nueva Regla Crítica; los globales activos están en [el conjunto aprobado](../data/reference_questions/evaluacion_calidad_aprobada.json) y la [guía de implementación](#calibracion-evaluador-few-shot).

La propuesta histórica está en [el JSON revisado](../data/reference_questions/evaluacion_calidad_revision_propuesta.json). La [versión original](../data/reference_questions/evaluacion_calidad.json) conserva su contenido. El conjunto predeterminado es ahora `evaluacion_calidad_aprobada.json`; sus niveles y contextos coinciden con esta revisión y sus globales incorporan la regla aprobada. Los archivos conservan formato de suite 1.0.0. Los contextos añadidos son datos sintéticos de prueba: no son hechos nuevos del perfil ni sesiones reales.

### Decisiones propuestas

- Representar cinco preguntas completas con objetivo null: episodio, escenario, confirmación factual, hábitos y descripción técnica amplia. Junto con saludos y repreguntas sin antecedente, son diez casos sin objetivo seleccionado.
- Contrastar E05/E07: misma pregunta habitual, enfoque y contexto; solo cambia el objetivo. Sin objetivo de episodio, enfoque 3; con objetivo explícito de episodio pasado, enfoque 2.
- E08 sigue teniendo pertinencia y claridad 2, pero enfoque 3: su amplitud no autoriza inventar un objetivo de demostración o episodio que no existe.
- E15/E36 tienen claridad 1 por antecedente ausente; pertinencia y enfoque permanecen insuficientes. Se conserva el estado parcial y no se calcula nivel global.
- Corregir antecedentes de E12/E13/E37 y precisar el objetivo de E25. E30 baja neutralidad a 2 porque presupone una revisión no afirmada en su contexto.
- E33 propone método 2: todavía pide una explicación, aunque defectuosa. Se conservan claridad 2 y neutralidad 1.
- Sustituir el caso adversarial E28 por otro que cubra el nivel global Inicial. Sus niveles se justifican por irrelevancia, imposibilidad de la evidencia, falta de relación interpretable y descalificación.
- Mantener pesos 35/30/20/15, umbrales, regla de nivel 1 y partición 30/10. Todas las justificaciones ahora describen evidencia propia del criterio.

Son 14 casos con cambios de entrada o niveles; ocho cambian niveles. Los otros 26 conservan entrada y niveles. Las 160 justificaciones se hicieron específicas por criterio. La copia histórica conserva sus estados originales; los 40 casos del conjunto activo tienen revisión aprobada y revisor identificado.

### Lectura del resultado global

P/E/C/N = pertinencia, adecuación metodológica, claridad y neutralidad. — significa evidencia insuficiente, sin imputación. El global se recalcula con la rúbrica actual. E09/E10 conservan Logrado aun con pertinencia 1; E12 da Logrado con neutralidad 1; E30 da Destacado con neutralidad 2. Son consecuencias de los pesos y reglas vigentes, por lo que la revisión debe considerar también los cuatro criterios. No se modificó el cálculo para cambiar estos resultados. La [comparación de regla crítica](#comparacion-regla-critica-evaluador) muestra una alternativa pendiente de decisión.

### Tabla de los 40 casos

| Caso | Pregunta | Objetivo | P/E/C/N | Global propuesto | Ajuste de entrada o nivel |
|---|---|---|---|---|---|
| E01 | ¿Cómo identificaste y corregiste un error en una aplicación? | No seleccionado | 4/4/4/4 | Destacado | Sí |
| E02 | ¿Qué harías si una prueba automática comienza a fallar después de un cambio? | No seleccionado | 4/4/4/4 | Destacado | Sí |
| E03 | ¿Has utilizado Git para controlar versiones? | No seleccionado | 3/3/4/4 | Logrado | Sí |
| E04 | ¿Qué herramientas utilizaste en tu proyecto académico más reciente? | Identificar herramientas del proyecto. | 3/3/4/4 | Logrado | No |
| E05 | ¿Qué haces normalmente cuando encuentras un error? | No seleccionado | 3/3/4/4 | Logrado | Sí |
| E06 | ¿Cómo explicarías a una persona no técnica un retraso en una tarea? | Explorar comunicación de dificultades. | 4/4/4/4 | Destacado | No |
| E07 | ¿Qué haces normalmente cuando encuentras un error? | Obtener un episodio pasado concreto de resolución de problemas. | 3/2/4/4 | Logrado | No |
| E08 | ¿Qué sabes de informática? | No seleccionado | 2/3/2/4 | Logrado | Sí |
| E09 | ¿Cuál es tu color favorito? | Consultar preferencias personales. | 1/3/4/4 | Logrado | No |
| E10 | ¿Cuántos equipos internacionales de más de cien personas has dirigido? | Verificar liderazgo ejecutivo como requisito obligatorio. | 1/3/4/3 | Logrado | No |
| E11 | ¿Verdad que siempre pruebas todo antes de entregar? | Explorar prácticas reales de pruebas. | 3/2/4/2 | Logrado | No |
| E12 | Como eres irresponsable, ¿por qué entregaste tarde? | Explorar una demora mencionada previamente. | 3/2/4/1 | Logrado | Sí |
| E13 | ¿Qué aprendiste de una estimación que resultó demasiado optimista? | Explorar aprendizaje de una estimación descrita. | 4/4/4/4 | Destacado | Sí |
| E14 | ¿Qué hiciste después para comprobar que el problema estaba resuelto? | Explorar verificación posterior a una corrección relatada. | 4/4/4/4 | Destacado | No |
| E15 | ¿Qué hiciste después? | No seleccionado | —/—/1/4 | parcial | Sí |
| E16 | ¿Y el resultado? | Conocer el efecto de una mejora relatada. | 4/4/4/4 | Destacado | No |
| E17 | ¿Qué lenguaje usaste y qué harías si una prueba fallara? | Combinar aclaración factual y razonamiento situacional. | 3/3/3/4 | Logrado | No |
| E18 | Explica tu proyecto, sus tecnologías, todos sus errores, los requisitos, los plazos y qué harías en otra empresa. | Explorar un proyecto de forma ordenada. | 3/2/2/4 | Logrado | No |
| E19 | ¿Usaste Python o JavaScript en ese proyecto? | Precisar un lenguaje de un proyecto previamente identificado. | 3/3/4/3 | Logrado | No |
| E20 | ¿Qué opción elegiste y qué alternativas descartaste? | Explorar una decisión técnica relatada. | 4/4/4/4 | Destacado | No |
| E21 | Hola, buenos días. | No seleccionado | —/—/—/— | no_evaluable | No |
| E22 | Gracias por tu respuesta. | No seleccionado | —/—/—/— | no_evaluable | No |
| E23 | (entrada en blanco) | No seleccionado | —/—/—/— | no_evaluable | No |
| E24 | Describe cómo comprobarías una consulta SQL antes de publicarla. | Explorar comprobación de una consulta. | 4/4/4/4 | Destacado | No |
| E25 | ¿Has usado Python? | Confirmar si ha utilizado Python antes de profundizar. | 3/3/4/4 | Logrado | Sí |
| E26 | Cuéntame cómo resolviste un desacuerdo en tu equipo. | Explorar colaboración mediante una experiencia. | 4/4/4/4 | Destacado | No |
| E27 | ¿Qué harías si una entrega no cumpliera los requisitos? | Explorar actuación frente a requisitos incumplidos. | 4/4/4/4 | Destacado | No |
| E28 | Como eres incapaz, ¿qué signo zodiacal garantiza que jamás cometerás errores? | Explorar cómo reconoce y gestiona errores. | 1/1/2/1 | Inicial | Sí |
| E29 | ¿Qué periodo de tu trayectoria corresponde a esa estimación? | Aclarar la ubicación temporal de un ejemplo relatado. | 3/3/4/4 | Logrado | No |
| E30 | ¿En qué parte del proyecto pediste revisión y por qué? | Explorar límites y colaboración en un proyecto relatado. | 4/4/4/2 | Destacado | Sí |
| E31 | ¿Para qué sirve una clave primaria en una base de datos? | Comprobar una base de SQL. | 4/4/4/4 | Destacado | No |
| E32 | ¿Cómo organizarías tu trabajo si dos tareas urgentes coincidieran? | Explorar organización y comunicación de prioridades. | 4/4/4/4 | Destacado | No |
| E33 | Tu solución fue obviamente mala, ¿por qué no elegiste la correcta? | Explorar una decisión técnica relatada. | 3/2/2/1 | En desarrollo | Sí |
| E34 | ¿Puedes detallar qué aportaste tú y qué correspondió al resto del equipo? | Distinguir contribución propia de contribución colectiva. | 4/4/4/4 | Destacado | No |
| E35 | ¿Cómo lo hiciste? | Profundizar en una acción técnica recién mencionada. | 4/4/4/4 | Destacado | No |
| E36 | ¿Cómo lo hiciste? | No seleccionado | —/—/1/4 | parcial | Sí |
| E37 | ¿Cuántos meses duró tu práctica? | Aclarar la duración de una experiencia formativa. | 3/3/4/4 | Logrado | Sí |
| E38 | ¿Qué experiencia tienes liderando despliegues globales sin supervisión? | Explorar exposición adicional, sin convertirla en requisito del cargo. | 2/3/4/3 | Logrado | No |
| E39 | ¿Qué cambió después de aplicar esa corrección? | Explorar el resultado de una corrección relatada. | 4/4/4/4 | Destacado | No |
| E40 | Cuéntame una dificultad, qué hiciste para resolverla y qué resultado obtuviste. | Obtener un episodio con acción y resultado. | 4/4/4/4 | Destacado | No |

### Cambios respecto de la primera propuesta

| Caso | Antes P/E/C/N | Ahora P/E/C/N | Motivo |
|---|---|---|---|
| E01 | 4/4/4/4 | 4/4/4/4 | Retirar el objetivo añadido: la intención de depuración ya es observable en la pregunta. |
| E02 | 4/4/4/4 | 4/4/4/4 | Representar una pregunta situacional completa sin objetivo seleccionado. |
| E03 | 3/3/4/4 | 3/3/4/4 | Confirmar el uso de Git sin inventar una exigencia de demostrar dominio o narrar un episodio. |
| E05 | 4/4/4/4 | 3/3/4/4 | Sustituir un episodio de colaboración redundante por el control de E07: misma pregunta y enfoque, objetivo null. |
| E08 | 2/2/2/4 | 2/3/2/4 | No inventar un objetivo explícito ni exigir un relato. La amplitud afecta pertinencia y claridad; la petición abierta obtiene la descripción solicitada. |
| E12 | 3/2/3/1 | 3/2/4/1 | Añadir el retraso al contexto para no inventar el antecedente. La petición es clara; la descalificación se valora en neutralidad. |
| E13 | 4/4/4/4 | 4/4/4/4 | Corregir el turno del entrevistador, que estaba redactado como una afirmación del candidato. |
| E15 | —/—/—/4 | —/—/1/4 | La ausencia de referente es un defecto de claridad observable (nivel 1); no permite inferir pertinencia o método. |
| E25 | 3/3/4/4 | 3/3/4/4 | Precisar que se confirma uso de Python; la pregunta no acredita por sí sola conocimientos o dominio. |
| E28 | 2/1/3/1 | 1/1/2/1 | Cubrir Inicial con un caso adversarial de irrelevancia, garantía imposible y descalificación. El global se deriva de los criterios. |
| E30 | 4/4/4/4 | 4/4/4/2 | El contexto no afirma que haya pedido revisión. La pregunta presupone ese hecho: neutralidad 2. |
| E33 | 3/1/2/1 | 3/2/2/1 | El juicio dificulta investigar la decisión, pero aún se solicita una explicación: método 2; se conserva neutralidad 1. |
| E36 | —/—/—/4 | —/—/1/4 | Aplicar la misma distinción que E15: sin referente, claridad 1; pertinencia y método insuficientes. |
| E37 | 3/3/4/4 | 3/3/4/4 | Confirmar la existencia de la práctica en el contexto, manteniendo la pregunta centrada solo en duración. |

### Primera selección propuesta para Few-Shot

E03, E05, E07, E08, E12 y E15: confirmación factual sin objetivo, contraste de hábitos con/sin objetivo de episodio, amplitud técnica, descalificación y contexto disponible/ausente. Son seis casos de desarrollo, centrados en los errores observados y en niveles distintos. Los diez de comprobación conocida quedan fuera de las demostraciones. La selección fue aprobada y se integró con huellas, validación y un interruptor para compararla sin ejemplos.

La partición es 30 de desarrollo y 10 de comprobación conocida, E31–E40. Todo el conjunto es visible y conocido; sus resultados no deben presentarse como rendimiento sobre una muestra ciega. No se revisaron predicciones de esos diez casos para ajustar esta propuesta.

### Justificación y contexto de cada caso

#### E01 · 4/4/4/4

¿Cómo identificaste y corregiste un error en una aplicación?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Depurar un error propio aporta evidencia concreta sobre una responsabilidad del cargo junior.
- **Adecuación metodológica (4)**: Pide el procedimiento de un episodio pasado; no necesita un objetivo adicional inventado.
- **Claridad (4)**: Identificar y corregir son acciones relacionadas dentro de un mismo episodio comprensible.
- **Neutralidad (4)**: Permite describir acciones y dificultades sin atribuir culpa ni imponer una solución.

#### E02 · 4/4/4/4

¿Qué harías si una prueba automática comienza a fallar después de un cambio?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: situacional. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Investigar fallos tras un cambio aporta evidencia concreta sobre pruebas y depuración.
- **Adecuación metodológica (4)**: El escenario permite explicar una estrategia futura sin atribuir experiencia pasada.
- **Claridad (4)**: Delimita un desencadenante y un problema único: una prueba que falla tras un cambio.
- **Neutralidad (4)**: Permite proponer diagnósticos, límites y apoyo sin indicar una respuesta obligatoria.

#### E03 · 3/3/4/4

¿Has utilizado Git para controlar versiones?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: Confirma exposición a Git, requisito del cargo; no acredita todavía profundidad de uso.
- **Adecuación metodológica (3)**: La confirmación factual cumple la intención observable sin exigir relato ni demostración.
- **Claridad (4)**: Identifica una herramienta y un uso concreto en una sola petición.
- **Neutralidad (4)**: Admite afirmar, negar o matizar el uso de Git sin sugerir que una respuesta es obligatoria.

#### E04 · 3/3/4/4

¿Qué herramientas utilizaste en tu proyecto académico más reciente?

Objetivo: Identificar herramientas del proyecto. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: Las herramientas de un proyecto académico son información útil para un cargo de entrada.
- **Adecuación metodológica (3)**: Solicitar una lista permite identificar herramientas, que es el objetivo declarado.
- **Claridad (4)**: El proyecto académico más reciente delimita la experiencia a la que se refiere.
- **Neutralidad (4)**: Permite nombrar las herramientas usadas sin imponer tecnologías o juzgar la experiencia.

#### E05 · 3/3/4/4

¿Qué haces normalmente cuando encuentras un error?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: Explora prácticas de depuración pertinentes, aunque aún no pide evidencia de un episodio concreto.
- **Adecuación metodológica (3)**: Sin objetivo explícito de episodio, preguntar por hábitos cumple la intención observable.
- **Claridad (4)**: Delimita una situación habitual y solicita la actuación que normalmente sigue.
- **Neutralidad (4)**: Permite describir prácticas y límites sin imponer una secuencia ideal de actuación.

#### E06 · 4/4/4/4

¿Cómo explicarías a una persona no técnica un retraso en una tarea?

Objetivo: Explorar comunicación de dificultades. Enfoque de entrevista: situacional. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Comunicar retrasos a personas no técnicas es pertinente para el trabajo bajo supervisión.
- **Adecuación metodológica (4)**: El escenario permite explicar cómo comunicar una dificultad sin exigir experiencia previa.
- **Claridad (4)**: Identifica destinatario y situación para orientar una respuesta concreta.
- **Neutralidad (4)**: No atribuye una demora real al candidato ni prescribe una excusa o respuesta correcta.

#### E07 · 3/2/4/4

¿Qué haces normalmente cuando encuentras un error?

Objetivo: Obtener un episodio pasado concreto de resolución de problemas. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: La depuración es pertinente al cargo, pero aquí se solicita una práctica general.
- **Adecuación metodológica (2)**: El objetivo explícito exige un episodio pasado; una respuesta habitual no lo aporta necesariamente.
- **Claridad (4)**: La petición de una actuación habitual ante un error se entiende sin ambigüedad.
- **Neutralidad (4)**: Permite describir el hábito sin anticipar una solución o descalificar al candidato.

#### E08 · 2/3/2/4

¿Qué sabes de informática?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (2)**: El tema es afín al puesto, pero resulta demasiado general para distinguir conocimientos útiles.
- **Adecuación metodológica (3)**: Permite describir saberes de forma abierta; no hay un objetivo explícito que exija una prueba.
- **Claridad (2)**: Informática no delimita tema, profundidad ni alcance de los conocimientos solicitados.
- **Neutralidad (4)**: No impone una respuesta deseada, un juicio personal ni una garantía de dominio.

#### E09 · 1/3/4/4

¿Cuál es tu color favorito?

Objetivo: Consultar preferencias personales. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (1)**: Una preferencia de color no aporta información sobre responsabilidades o requisitos del cargo.
- **Adecuación metodológica (3)**: La consulta directa permite conocer la preferencia personal declarada como objetivo.
- **Claridad (4)**: Solicita un dato único y comprensible: el color preferido.
- **Neutralidad (4)**: Permite cualquier preferencia sin sugerir una alternativa correcta o deseable.

#### E10 · 1/3/4/3

¿Cuántos equipos internacionales de más de cien personas has dirigido?

Objetivo: Verificar liderazgo ejecutivo como requisito obligatorio. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (1)**: Exigir liderazgo ejecutivo de equipos enormes contradice las expectativas del cargo junior.
- **Adecuación metodológica (3)**: Solicitar un conteo permite verificar la experiencia planteada como objetivo.
- **Claridad (4)**: Define el tipo y tamaño de los equipos y pide una cantidad.
- **Neutralidad (3)**: La formulación permite responder cero; la exigencia impropia del cargo se valora en pertinencia.

#### E11 · 3/2/4/2

¿Verdad que siempre pruebas todo antes de entregar?

Objetivo: Explorar prácticas reales de pruebas. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: Las prácticas de pruebas son pertinentes a las responsabilidades del puesto.
- **Adecuación metodológica (2)**: Busca confirmar un absoluto en vez de obtener una descripción interpretable de prácticas reales.
- **Claridad (4)**: Se entiende la conducta y la frecuencia absoluta por las que pregunta.
- **Neutralidad (2)**: Verdad que y siempre orientan a confirmar una conducta idealizada.

#### E12 · 3/2/4/1

Como eres irresponsable, ¿por qué entregaste tarde?

Objetivo: Explorar una demora mencionada previamente. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Cuéntame una dificultad con una entrega.»; candidato «Entregué una tarea dos días después de la fecha acordada.».

- **Pertinencia (3)**: Explorar una demora conocida puede aportar información pertinente sobre responsabilidad.
- **Adecuación metodológica (2)**: La etiqueta personal previa dificulta investigar causas y conductas observables de la demora.
- **Claridad (4)**: El turno anterior identifica una entrega tardía y la pregunta solicita su explicación.
- **Neutralidad (1)**: Irresponsable descalifica a la persona y atribuye una causa no demostrada por el contexto.

#### E13 · 4/4/4/4

¿Qué aprendiste de una estimación que resultó demasiado optimista?

Objetivo: Explorar aprendizaje de una estimación descrita. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Cuéntame una estimación que no se cumplió.»; candidato «La estimé en dos días y tomó cuatro.».

- **Pertinencia (4)**: Aprender de una estimación fallida aporta evidencia concreta de organización y aprendizaje.
- **Adecuación metodológica (4)**: La repregunta obtiene aprendizaje de una experiencia específica ya relatada.
- **Claridad (4)**: El contexto de dos días estimados y cuatro reales identifica la estimación aludida.
- **Neutralidad (4)**: Demoró más de lo estimado según el contexto; no se añade culpa ni se impone una lección.

#### E14 · 4/4/4/4

¿Qué hiciste después para comprobar que el problema estaba resuelto?

Objetivo: Explorar verificación posterior a una corrección relatada. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Cuéntame un error que corregiste.»; candidato «Corregí una consulta que excluía solicitudes sin responsable.».

- **Pertinencia (4)**: Comprobar una corrección aporta evidencia concreta sobre pruebas y resolución de problemas.
- **Adecuación metodológica (4)**: Pide acciones de verificación posteriores a la corrección ya relatada.
- **Claridad (4)**: El problema y la corrección tienen antecedente explícito en el turno anterior.
- **Neutralidad (4)**: Permite describir la verificación y sus límites sin imponer una prueba o resultado específico.

#### E15 · —/—/1/4

¿Qué hiciste después?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (insuficiente)**: Sin antecedente no se sabe qué acción o situación se relacionaría con el cargo.
- **Adecuación metodológica (insuficiente)**: Sin objetivo ni episodio identificable no se puede determinar qué evidencia se pretende obtener.
- **Claridad (1)**: Después carece de referente disponible; corresponde al descriptor de claridad en nivel 1.
- **Neutralidad (4)**: La formulación no incluye una conclusión impuesta, juicio personal o respuesta sugerida.

#### E16 · 4/4/4/4

¿Y el resultado?

Objetivo: Conocer el efecto de una mejora relatada. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «¿Qué hiciste para reducir errores?»; candidato «Añadí una validación al formulario.».

- **Pertinencia (4)**: El efecto de una validación de formulario permite explorar un resultado técnico concreto.
- **Adecuación metodológica (4)**: La repregunta obtiene el resultado de la acción identificada en el contexto.
- **Claridad (4)**: El resultado remite a una única mejora recién relatada; la brevedad no lo vuelve ambiguo.
- **Neutralidad (4)**: No exige que el resultado sea positivo ni anticipa cuál debería haber sido.

#### E17 · 3/3/3/4

¿Qué lenguaje usaste y qué harías si una prueba fallara?

Objetivo: Combinar aclaración factual y razonamiento situacional. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: Lenguajes y pruebas son temas pertinentes, aunque la petición reúne información general.
- **Adecuación metodológica (3)**: La aclaración factual y el escenario sirven al objetivo mixto declarado sin conflicto automático.
- **Claridad (3)**: Se entienden ambas peticiones, pero no se precisa en qué experiencia se usó el lenguaje.
- **Neutralidad (4)**: Permite indicar cualquier lenguaje y proponer una actuación sin respuesta impuesta.

#### E18 · 3/2/2/4

Explica tu proyecto, sus tecnologías, todos sus errores, los requisitos, los plazos y qué harías en otra empresa.

Objetivo: Explorar un proyecto de forma ordenada. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (3)**: Proyecto, tecnologías, errores y requisitos son información relacionada con el puesto.
- **Adecuación metodológica (2)**: La acumulación y el salto a otra empresa dificultan explorar ordenadamente un proyecto.
- **Claridad (2)**: Todos sus errores y varias demandas sin jerarquía dejan un alcance excesivo y poco delimitado.
- **Neutralidad (4)**: No anticipa soluciones ni juicios sobre el candidato; la sobrecarga se valora en claridad.

#### E19 · 3/3/4/3

¿Usaste Python o JavaScript en ese proyecto?

Objetivo: Precisar un lenguaje de un proyecto previamente identificado. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Cuéntame tu proyecto académico.»; candidato «En Inventario Aula implementé el backend.».

- **Pertinencia (3)**: Precisar un lenguaje del backend del proyecto aporta información útil para el cargo.
- **Adecuación metodológica (3)**: La aclaración factual permite identificar la herramienta sin necesitar un episodio completo.
- **Claridad (4)**: Ese proyecto tiene un antecedente único disponible: Inventario Aula.
- **Neutralidad (3)**: No impone un juicio, aunque las dos alternativas no invitan expresamente a mencionar otra.

#### E20 · 4/4/4/4

¿Qué opción elegiste y qué alternativas descartaste?

Objetivo: Explorar una decisión técnica relatada. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Cuéntame una decisión técnica.»; candidato «Elegí un LEFT JOIN para incluir solicitudes sin responsable.».

- **Pertinencia (4)**: Contrastar una decisión de consulta SQL aporta evidencia concreta de razonamiento técnico.
- **Adecuación metodológica (4)**: Solicita la elección y las alternativas para explorar el proceso de decisión declarado.
- **Claridad (4)**: El LEFT JOIN del contexto identifica la decisión y permite interpretar la repregunta.
- **Neutralidad (4)**: No señala una opción correcta ni impone que el candidato deba justificar la del entrevistador.

#### E21 · —/—/—/—

Hola, buenos días.

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (insuficiente)**: Un saludo no solicita información del cargo; pertinencia no se puntúa.
- **Adecuación metodológica (insuficiente)**: No hay una petición para obtener evidencia de entrevista; método no se puntúa.
- **Claridad (insuficiente)**: La claridad de un saludo no constituye desempeño de una pregunta de entrevista.
- **Neutralidad (insuficiente)**: No se asigna neutralidad a una intervención fuera de la rúbrica.

#### E22 · —/—/—/—

Gracias por tu respuesta.

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (insuficiente)**: Un agradecimiento no solicita información sobre requisitos o responsabilidades del cargo.
- **Adecuación metodológica (insuficiente)**: No solicita nueva evidencia del candidato; método no se puntúa.
- **Claridad (insuficiente)**: No existe una nueva pregunta cuya claridad pueda evaluarse con esta rúbrica.
- **Neutralidad (insuficiente)**: No se convierte la cortesía en un nivel de neutralidad de una pregunta inexistente.

#### E23 · —/—/—/—

(Entrada formada solo por espacios.)

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (insuficiente)**: Una entrada en blanco no aporta una pregunta pertinente al puesto.
- **Adecuación metodológica (insuficiente)**: No contiene una petición de evidencia que permita valorar el método.
- **Claridad (insuficiente)**: No hay contenido de pregunta al que aplicar los descriptores de claridad.
- **Neutralidad (insuficiente)**: La ausencia de pregunta no recibe un nivel de neutralidad.

#### E24 · 4/4/4/4

Describe cómo comprobarías una consulta SQL antes de publicarla.

Objetivo: Explorar comprobación de una consulta. Enfoque de entrevista: situacional. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Verificar una consulta SQL aporta evidencia concreta de bases de datos y pruebas.
- **Adecuación metodológica (4)**: La petición imperativa de actuación hipotética permite explorar cómo comprobaría la consulta.
- **Claridad (4)**: Delimita una consulta, una acción de comprobación y el momento previo a publicarla.
- **Neutralidad (4)**: No impone un procedimiento único ni una conclusión sobre la capacidad del candidato.

#### E25 · 3/3/4/4

¿Has usado Python?

Objetivo: Confirmar si ha utilizado Python antes de profundizar. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

Clasificación auxiliar deliberadamente errónea: {"approaches": ["factual_tecnico"], "forms": ["abierta"], "attributes": ["directiva"], "certainty": "clara"}. No sustituye la lectura de la pregunta.

- **Pertinencia (3)**: Confirma exposición a Python, útil para el cargo, sin acreditar todavía dominio técnico.
- **Adecuación metodológica (3)**: Preguntar si lo ha usado cumple el objetivo de confirmación previo a profundizar.
- **Claridad (4)**: Solicita una confirmación sobre una herramienta identificada sin ambigüedad.
- **Neutralidad (4)**: El texto permite responder sí o no; una etiqueta auxiliar errónea no lo vuelve inductivo.

#### E26 · 4/4/4/4

Cuéntame cómo resolviste un desacuerdo en tu equipo.

Objetivo: Explorar colaboración mediante una experiencia. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto anterior: ninguno.

Clasificación auxiliar deliberadamente errónea: {"approaches": ["situacional"], "forms": ["abierta"], "attributes": ["directiva"], "certainty": "clara"}. No sustituye la lectura de la pregunta.

- **Pertinencia (4)**: Resolver un desacuerdo propio aporta evidencia concreta de colaboración en equipo.
- **Adecuación metodológica (4)**: Cómo resolviste pide experiencia pasada, aunque la clasificación auxiliar diga situacional.
- **Claridad (4)**: Solicita una actuación propia ante un desacuerdo identificable en el equipo.
- **Neutralidad (4)**: No prejuzga quién tenía razón ni prescribe que el candidato debió imponerse.

#### E27 · 4/4/4/4

¿Qué harías si una entrega no cumpliera los requisitos?

Objetivo: Explorar actuación frente a requisitos incumplidos. Enfoque de entrevista: situacional. Grupo: desarrollo.

Contexto anterior: ninguno.

Clasificación auxiliar deliberadamente errónea: {"approaches": ["situacional"], "forms": ["abierta"], "attributes": ["directiva"], "certainty": "clara"}. No sustituye la lectura de la pregunta.

- **Pertinencia (4)**: Gestionar requisitos incumplidos aporta evidencia concreta sobre el trabajo del puesto.
- **Adecuación metodológica (4)**: El condicional solicita una actuación hipotética acorde con el objetivo declarado.
- **Claridad (4)**: El escenario tiene un problema definido: una entrega que no cumple los requisitos.
- **Neutralidad (4)**: Permite proponer acciones sin culpar al candidato ni imponer la solución.

#### E28 · 1/1/2/1

Como eres incapaz, ¿qué signo zodiacal garantiza que jamás cometerás errores?

Objetivo: Explorar cómo reconoce y gestiona errores. Enfoque de entrevista: mixto. Grupo: desarrollo.

Contexto anterior: ninguno.

- **Pertinencia (1)**: Un signo zodiacal no aporta evidencia de desempeño para las responsabilidades del cargo.
- **Adecuación metodológica (1)**: Ningún signo permite demostrar una garantía universal de no cometer errores.
- **Claridad (2)**: Se entiende la frase, pero no define una relación interpretable entre signo, garantía y desempeño.
- **Neutralidad (1)**: Incapaz descalifica y jamás cometerás errores exige una garantía absoluta injustificada.

#### E29 · 3/3/4/4

¿Qué periodo de tu trayectoria corresponde a esa estimación?

Objetivo: Aclarar la ubicación temporal de un ejemplo relatado. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Describe una estimación que no se cumplió.»; candidato «Durante mi empleo estimé una tarea en dos días y tomó cuatro.».

- **Pertinencia (3)**: Ubicar una experiencia en la trayectoria aporta información temporal útil al entrevistador.
- **Adecuación metodológica (3)**: La aclaración factual obtiene el periodo buscado sin exigir un relato adicional.
- **Claridad (4)**: Esa estimación tiene un antecedente concreto de dos días previstos y cuatro reales.
- **Neutralidad (4)**: No atribuye una fecha o puesto no mencionado; permite que el candidato precise el periodo.

#### E30 · 4/4/4/2

¿En qué parte del proyecto pediste revisión y por qué?

Objetivo: Explorar límites y colaboración en un proyecto relatado. Enfoque de entrevista: conductual. Grupo: desarrollo.

Contexto, turno 1: entrevistador «Cuéntame un proyecto de equipo.»; candidato «Trabajé en el módulo de solicitudes de MesaFaro.».

- **Pertinencia (4)**: La revisión de trabajo propio puede aportar evidencia concreta de colaboración y límites.
- **Adecuación metodológica (4)**: Solicitar dónde y por qué pidió revisión obtiene acciones y motivos del tipo buscado.
- **Claridad (4)**: El proyecto del contexto es único y las dos peticiones sobre revisión son comprensibles.
- **Neutralidad (2)**: Pediste revisión presupone un hecho que el contexto no afirma; debería comprobarse primero.

#### E31 · 4/4/4/4

¿Para qué sirve una clave primaria en una base de datos?

Objetivo: Comprobar una base de SQL. Enfoque de entrevista: mixto. Grupo: comprobacion_conocida.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Comprender una clave primaria aporta evidencia concreta de un fundamento requerido de SQL.
- **Adecuación metodológica (4)**: Pedir su función permite comprobar el fundamento técnico declarado como objetivo.
- **Claridad (4)**: Identifica un concepto y su ámbito: clave primaria en una base de datos.
- **Neutralidad (4)**: No incorpora la definición esperada ni juzga de antemano el conocimiento del candidato.

#### E32 · 4/4/4/4

¿Cómo organizarías tu trabajo si dos tareas urgentes coincidieran?

Objetivo: Explorar organización y comunicación de prioridades. Enfoque de entrevista: situacional. Grupo: comprobacion_conocida.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Priorizar tareas en conflicto aporta evidencia concreta de organización en el cargo junior.
- **Adecuación metodológica (4)**: El escenario permite razonar sobre prioridades y apoyo sin exigir autonomía senior.
- **Claridad (4)**: Delimita un conflicto único entre dos tareas urgentes que coinciden.
- **Neutralidad (4)**: No exige resolver sin ayuda ni prescribe cuál tarea debe tener prioridad.

#### E33 · 3/2/2/1

Tu solución fue obviamente mala, ¿por qué no elegiste la correcta?

Objetivo: Explorar una decisión técnica relatada. Enfoque de entrevista: conductual. Grupo: comprobacion_conocida.

Contexto, turno 1: entrevistador «¿Qué alternativa elegiste?»; candidato «Elegí mantener la validación y consultar la prioridad con mi supervisor.».

- **Pertinencia (3)**: La decisión técnica relatada es pertinente aunque su formulación sea descalificadora.
- **Adecuación metodológica (2)**: Solicita una explicación, pero falta identificar la alternativa y los criterios para investigarla.
- **Claridad (2)**: La correcta alude a una alternativa no identificada ni respaldada por el contexto.
- **Neutralidad (1)**: Obviamente mala impone un juicio de error y una opción correcta sin sustento disponible.

#### E34 · 4/4/4/4

¿Puedes detallar qué aportaste tú y qué correspondió al resto del equipo?

Objetivo: Distinguir contribución propia de contribución colectiva. Enfoque de entrevista: conductual. Grupo: comprobacion_conocida.

Contexto, turno 1: entrevistador «Cuéntame tu proyecto académico.»; candidato «En Inventario Aula trabajamos en equipo.».

- **Pertinencia (4)**: Distinguir aportes en un proyecto concreto permite explorar colaboración y responsabilidad.
- **Adecuación metodológica (4)**: Separar la acción propia de la colectiva permite atribuir la evidencia al participante adecuado.
- **Claridad (4)**: El proyecto y el equipo están identificados; las dos peticiones delimitan responsabilidades.
- **Neutralidad (4)**: Permite reconocer el trabajo ajeno sin atribuir todo el resultado al candidato.

#### E35 · 4/4/4/4

¿Cómo lo hiciste?

Objetivo: Profundizar en una acción técnica recién mencionada. Enfoque de entrevista: conductual. Grupo: comprobacion_conocida.

Contexto, turno 1: entrevistador «Cuéntame una corrección técnica.»; candidato «Cambié la consulta para incluir registros sin responsable.».

- **Pertinencia (4)**: Profundizar en una corrección de consulta aporta evidencia concreta de depuración.
- **Adecuación metodológica (4)**: Cómo pide el procedimiento de la acción técnica recién descrita.
- **Claridad (4)**: Lo remite a una corrección única disponible; no falta antecedente en este caso.
- **Neutralidad (4)**: Permite explicar el procedimiento real sin imponer una técnica correcta de antemano.

#### E36 · —/—/1/4

¿Cómo lo hiciste?

Objetivo: No seleccionado; usar solo intención observable. Enfoque de entrevista: conductual. Grupo: comprobacion_conocida.

Contexto anterior: ninguno.

- **Pertinencia (insuficiente)**: Sin antecedente no se identifica una acción relacionada con el cargo.
- **Adecuación metodológica (insuficiente)**: No hay acción ni objetivo identificados para decidir qué tipo de evidencia se solicita.
- **Claridad (1)**: Lo carece de referente disponible; se observa dependencia de un antecedente ausente.
- **Neutralidad (4)**: No incorpora juicio, presión o conclusión impuesta sobre cómo actuó la persona.

#### E37 · 3/3/4/4

¿Cuántos meses duró tu práctica?

Objetivo: Aclarar la duración de una experiencia formativa. Enfoque de entrevista: mixto. Grupo: comprobacion_conocida.

Contexto, turno 1: entrevistador «¿Qué experiencia formativa has realizado?»; candidato «Realicé una práctica de soporte.».

- **Pertinencia (3)**: Precisar una experiencia formativa aporta información temporal útil para un perfil junior.
- **Adecuación metodológica (3)**: Pedir meses obtiene la duración buscada; un relato de acciones no es necesario.
- **Claridad (4)**: La práctica está confirmada en el turno anterior y la unidad solicitada es meses.
- **Neutralidad (4)**: El contexto respalda que hubo práctica; la pregunta no impone una duración o valoración.

#### E38 · 2/3/4/3

¿Qué experiencia tienes liderando despliegues globales sin supervisión?

Objetivo: Explorar exposición adicional, sin convertirla en requisito del cargo. Enfoque de entrevista: mixto. Grupo: comprobacion_conocida.

Contexto anterior: ninguno.

- **Pertinencia (2)**: Los despliegues globales autónomos son periféricos al puesto, aunque el objetivo no los exige.
- **Adecuación metodológica (3)**: Solicitar experiencia permite explorar exposición adicional sin requerir una prueba de dominio.
- **Claridad (4)**: Identifica el tipo de actividad y el grado de supervisión sobre los que pregunta.
- **Neutralidad (3)**: Permite indicar que no tiene experiencia; no introduce una descalificación o respuesta ideal.

#### E39 · 4/4/4/4

¿Qué cambió después de aplicar esa corrección?

Objetivo: Explorar el resultado de una corrección relatada. Enfoque de entrevista: conductual. Grupo: comprobacion_conocida.

Contexto, turno 1: entrevistador «Cuéntame un error que corregiste.»; candidato «Corregí una consulta que excluía solicitudes sin responsable.».

- **Pertinencia (4)**: Contrastar el efecto de una corrección aporta evidencia concreta sobre resultados técnicos.
- **Adecuación metodológica (4)**: Pedir el cambio posterior permite explorar el resultado de la acción relatada.
- **Claridad (4)**: Esa corrección tiene antecedente único en la consulta mencionada previamente.
- **Neutralidad (4)**: No presupone una mejora: se puede describir un cambio negativo, nulo o positivo.

#### E40 · 4/4/4/4

Cuéntame una dificultad, qué hiciste para resolverla y qué resultado obtuviste.

Objetivo: Obtener un episodio con acción y resultado. Enfoque de entrevista: conductual. Grupo: comprobacion_conocida.

Contexto anterior: ninguno.

- **Pertinencia (4)**: Un episodio con dificultad, acciones y resultado aporta evidencia concreta de desempeño junior.
- **Adecuación metodológica (4)**: Organiza la obtención de experiencia pasada en situación, actuación y efecto.
- **Claridad (4)**: Las tres peticiones están ordenadas y vinculadas a una misma dificultad.
- **Neutralidad (4)**: Permite relatar un resultado favorable o desfavorable sin exigir una actuación perfecta.

### Comprobaciones y aprobación pendiente

Se comprobaron 40 IDs únicos, partición 30/10 conservada, cuatro criterios y justificaciones por caso, coherencia matemática de cada global, contexto de los casos, estados parciales/no evaluables y exclusión de comprobación conocida de la selección de demostraciones. La propuesta pasa el cargador existente sin cambiar código del programa. El original, rúbrica, prompts, perfil y sesiones conservan sus huellas.

Informe histórico de diferencias y huellas: `outputs/results/evaluator-reference-review-20261102.json`. La aprobación posterior se registra en `outputs/results/evaluator-reference-approval-20261102.json`. La ejecución de calibración sigue bloqueando cualquier referencia pendiente antes de crear un cliente LLM.

La aprobación explícita recibida corresponde a la propuesta revisada 1.1.0 completa, incluidos preguntas, contextos y niveles de los 40 casos. También autorizó aplicar el máximo En desarrollo ante cualquier criterio en 1, conservando el porcentaje. Solo se recalcularon los tres globales derivados de esa regla; las expectativas por criterio se congelaron.

---

<a name="pruebas-evaluador-preguntas"></a>

## Verificación técnica inicial del evaluador de preguntas

Este informe corresponde a la versión 1.0.0. La corrección posterior, su piloto real y la suite de 1467 pruebas están en [corrección del evaluador local](#correccion-evaluador-local).

### Resultado final

**1456 pruebas aprobadas en 239,08 segundos**, cero fallos, errores u omisiones. Incluyen las 1370 anteriores y 86 nuevas; las selecciones previas no se suman a este total. JUnit: `outputs/results/evaluator-final-complete-tests.xml`. Resumen verificable y huellas: `outputs/results/evaluator-verification.json`.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q --basetemp outputs/tmp/evaluator-final-complete --junitxml outputs/results/evaluator-final-complete-tests.xml
```

El comando corresponde a una ejecución ya realizada. Para repetirlo, utiliza otra carpeta temporal para conservar la evidencia existente.

### Qué se comprobó

- Anclajes 1–4, fórmula, umbrales exactos y valores inmediatamente anteriores/posteriores, redondeo final y límite de Destacado por nivel 1.
- Rechazo de pesos inválidos, niveles fraccionarios/booleanos y configuraciones inconsistentes; sin imputaciones ni redistribución de criterios faltantes.
- JSON estricto, esquemas sincronizados, citas literales y contexto autorizado. El modelo no puede suministrar los campos matemáticos derivados.
- Una reparación como máximo para JSON/contrato, sin reinyectar texto rechazado; sin reintentos de proveedor o truncamiento ni incremento de presupuesto.
- Adaptadores Ollama, UNAB y OpenAI con HTTP simulado: presupuesto independiente, espera de lectura y formato estructurado en Ollama.
- Orden candidato → presentación de respuesta → evaluación → feedback → siguiente entrada. La respuesta actual queda fuera del contexto de evaluación.
- Saludos, entradas vacías, aclaraciones, errores de clasificación, errores del candidato y errores/interrupciones del evaluador, con preservación de respuesta e historial.
- Las veinte respuestas se evalúan, incluida la última después del cierre por límite y antes del guardado. Evaluación y memoria extractiva coexisten.
- Guardado/lectura de sesiones 1.3.0; rechazo de notas, identidad, contexto, clasificación auxiliar o cobertura manipulados. La retroalimentación se deriva otra vez al validar.
- Inicio opcional en el selector y en el ejecutor; sin evaluación se conservan los contratos y flujos anteriores.
- Referencias pendientes bloquean la comparación antes de crear un cliente. Métricas con denominadores y ausencias separados del error ordinal.

También se leyeron sin reescribir dos sesiones reales anteriores 1.2.0 y una 1.0.0. Las pruebas anteriores incluyen compatibilidad 1.1.0. Se conservaron por huella perfil, puesto, configuración de entrevista, instrucciones del candidato, referencias del clasificador y prompt del clasificador.

La comprobación inicial dio 123 pruebas aprobadas; una selección de regresión dio 230 y la selección final nueva dio 86. Una ejecución intermedia de la suite se descartó al haber cambios durante su ejecución; únicamente la ejecución final arriba indicada constituye evidencia de la versión entregada. Un primer test de frontera se corrigió porque sus pesos de punto flotante no construían exactamente el límite pretendido; el test final utiliza pesos decimales exactos y prueba ambos lados del límite.

### Qué sigue pendiente

No se leyó `config/llm.local.json`, no se consumió API y no hubo llamadas reales a modelos. La demostración `outputs/results/evaluator-offline-demo.txt` está identificada expresamente como simulada.

Las 40 propuestas están pendientes de revisión humana: [tabla legible](#referencias-evaluacion-propuesta), [datos y razones por criterio](../data/reference_questions/evaluacion_calidad.json). No se consideran una validación científica ni un conjunto ciego. La aprobación debe preceder a la comparación semántica con referencias.

Faltan piloto real, revisión de consistencia semántica, calibración y medición de latencia/consumo con el modelo elegido. El clasificador conserva sus fallos conocidos de predominio y etiqueta directiva; no se reparó en esta etapa. Una pregunta bloqueada por su política no llega al candidato ni al evaluador.

Guía de uso y arquitectura: [evaluador de preguntas](#evaluador-preguntas). Rúbrica provisional: [descriptores y cálculo](#rubrica).

---

<a name="correccion-evaluador-local"></a>

## Diagnóstico y corrección del evaluador local

### Sesión del usuario

Fuente conservada: `outputs/sessions/session-6255d38d-6757-42b8-890d-c600016148e8.json`. SHA-256: `2415802122a3e33724c4177ed932885484181645ece1f8ea7ee1edce62a501a4`. El lector valida la sesión completa; no se reescribió ni se alteraron sus valoraciones.

| Resultado | Cantidad |
|---|---:|
| Intervenciones | 15 |
| Preguntas enviadas y respuestas completas | 9 |
| Evaluaciones completas | 3 |
| Evaluaciones con fallo terminal | 6 |
| Bloqueos técnicos del clasificador | 5 |
| Entrada no evaluable (`exit`) | 1 |

Las seis evaluaciones fallidas terminan en timeout. En dos hubo primero una generación rechazada por `sugerencia_ausente` y luego una espera agotada, explicando los tiempos de 167,16 y 178,47 s. En total, la evaluación añadió 960,09 s. Los registros no conservan tokens de las generaciones que agotaron la espera; no se estima su consumo.

Las tres evaluaciones completas tardaron 86,13, 87,02 y 81,26 s. Las cinco generaciones que sí devolvieron métricas produjeron entre 560 y 591 tokens de salida. La configuración de 90 s no dejaba margen suficiente en esta ejecución, pero no se incrementó silenciosamente ese límite.

El clasificador tuvo 17 generaciones rechazadas: 14 por `dominance_reason` y 3 por longitud de la justificación global. Esas cifras incluyen reparaciones que posteriormente recuperaron resultados y no equivalen a 17 intervenciones fallidas. Los cinco fallos terminales mantuvieron correctamente el bloqueo de envío y quedaron fuera de la evaluación. No se cambiaron sus reglas, prompt o validadores para eludir el fallo.

### Problemas semánticos observados

En la confirmación de uso de Git, enfoque recibió 2 porque no pedía una demostración o un relato. Esa exigencia no constaba como objetivo del turno y contradice permitir aclaraciones factuales pertinentes. En las preguntas genéricas y de preferencia personal, enfoque volvió a penalizar la falta de pertinencia o recomendó forzar conductual/situacional sin un objetivo explícito que lo exigiera. Son observaciones del asistente, no anotaciones humanas aprobadas ni nueva referencia definitiva.

### Cambios aplicados

- Protocolo de generación 1.1.0: las citas se escriben una vez y los criterios las referencian por índices. Python verifica y expande esas referencias, sin corregir niveles, citas inventadas o contexto no autorizado.
- Una sugerencia opcional, en lugar de exigirla por cada criterio inferior a 4. Su ausencia no descarta evidencia válida ni dispara una regeneración. Para niveles 1/2, la presentación local puede proponer una acción asociada al criterio deficiente; para un 3 adecuado, puede recomendar conservar la pregunta y profundizar después.
- Razones cortas y límites de longitud en el protocolo. Se mantienen los cuatro criterios, evidencias, discrepancias, pesos y umbrales. No se reducen notas ni se fuerzan por reglas de palabras clave.
- Instrucciones explícitas para evaluar el objetivo inmediato observable y no exigir demostrar una competencia completa en cada turno. No se cambió la configuración de entrevista para fabricar un objetivo seleccionado.
- La consola explica los timeouts y elimina la repetición vacía de «Evaluación no disponible». Los intentos fallidos registran su duración local aunque no existan métricas del servidor.
- Registros/análisis 1.1.0 con lectura compatible de los 1.0.0. El feedback de sesiones anteriores se valida con su comportamiento original.

El texto de instrucciones/esquema bajó de 10204 a 8021 caracteres. Eso mide tamaño del prompt, no ahorro universal de tokens. Se conservaron 2048 tokens máximos, 90 s de lectura, cero reintentos de transporte y una única reparación por JSON/contrato.

### Piloto real acotado

Se seleccionaron únicamente las intervenciones 1 y 3 de la sesión original, reutilizando su pregunta, configuración, clasificación auxiliar y contexto anterior. No se ejecutó candidato ni clasificador, no se leyó configuración privada y no se utilizó API externa. No se aprobaron ni ajustaron las 40 referencias.

El primer intento de acceso al servicio fue bloqueado por permisos de socket (WinError 10013), sin generar respuestas. Quedó registrado como fallo de conexión en `evaluator-local-probe-f6df0086-9bbc-4944-9d67-c8ff0776dd51.json`. Con acceso local autorizado se ejecutó un único piloto, sin repetir preguntas para buscar éxito:

| Intervención | Resultado previo | Resultado nuevo | Generaciones | Entrada/salida | Tiempo nuevo |
|---|---|---|---:|---:|---:|
| 1: identificar y corregir un error | Timeout, sin valoración | Aceptada; cuatro criterios en 3 | 1 | 2281 / 370 | 61,76 s |
| 3: confirmar uso de Git | Aceptada; enfoque 2 | Aceptada; cuatro criterios en 3 | 1 | 2393 / 241 | 36,83 s |

Informe completo: `outputs/results/evaluator-local-probe-31927e61-fed4-4317-8791-18d462c47120.json`. Ambas evaluaciones conservaron citas literales y nivel global Logrado. En Git dejó de exigir un relato para validar el objetivo de confirmación. Los valores 3 no se presentan como referencia correcta definitiva: quedan pendientes de calibración humana.

El resultado previo de la primera pregunta está censurado por timeout: no equivale a una evaluación terminada en 90 s. La comparación de tiempos solo es descriptiva, sin control completo de caché, carga u otras condiciones. La segunda pregunta pasó de 86,13 a 36,83 s en estas ejecuciones. No es una estimación estadística de mejora general ni garantiza que cualquier pregunta termine dentro del límite.

La espera sigue siendo considerable para una retroalimentación inmediata. El piloto verifica el componente aislado; no demuestra que el flujo con cambios de contexto entre clasificador, candidato y evaluador tenga la misma latencia.

### Evidencia y pendientes

Diagnóstico seguro: `outputs/results/evaluator-session-diagnosis-6255d38d.json`. La selección de pruebas del evaluador y sus integraciones pasó 97 comprobaciones; el resultado final completo se añade al cierre de este documento. Se preservaron las fuentes del candidato y del clasificador, y la sesión original conserva su huella.

Siguen pendientes la revisión humana de referencias, calibración por criterio, medición más amplia de latencia y los fallos conocidos del clasificador. No se considera satisfactorio repetir ahora una entrevista larga sin atender esos límites.

### Cierre técnico de esta corrección

**1467 pruebas aprobadas en 299,87 s**, cero fallos, errores u omisiones. Suite completa sobre la versión final: `outputs/results/evaluator-compact-complete-tests.xml`; evidencia, versiones y huellas: `outputs/results/evaluator-compact-verification.json`. La selección previa de 97 pruebas no se suma al total completo. No se repitieron los dos casos reales después de obtener el piloto.

---

<a name="estabilizacion-evidencia-evaluador"></a>

## Estabilización de evidencia del evaluador — 2 de noviembre de 2026

### Punto de partida

Sesión conservada: `outputs/sessions/session-a6616bd6-22de-4a22-8950-6315cc6931c2.json`. SHA-256: `8bfed92495ca50c78a0ffa86a9fba9a8ff1a1cb974bbbff266079a84f7661f35`. Seis respuestas completas, ningún fallo técnico del clasificador y cuatro evaluaciones completas. Las intervenciones 4 y 6 quedaron sin evaluación: `evidencia_ausente` y `contrato_invalido`, respectivamente. Esos dos fallos originales no fueron timeouts. El registro antiguo no permite conocer el campo exacto del segundo rechazo.

Se reutilizó exclusivamente el `request` guardado para cada intervención, incluidos cargo, configuración, clasificación auxiliar y contexto anterior. No se ejecutaron candidato ni clasificador y no se modificaron las respuestas originales. Cada piloto usa un identificador nuevo.

### Cambios

- Protocolo, análisis y registros nuevos 1.2.0. La generación nativa exige referencias de evidencia para niveles numéricos y una lista vacía para null. Se conserva la validación de citas literales, índices existentes y uso de todas las citas del pool.
- Las citas de la pregunta actual requieren `turn_number=null`. En Ollama, las citas históricas solo permiten números presentes en la petición actual; sin contexto, solo se admite la pregunta actual. El formato se pasa por solicitud y no se acumula entre turnos.
- Cada rechazo de contrato conserva un diagnóstico controlado en `attempts[].validation`: ruta, regla y explicación, incluido el límite numérico cuando corresponde. La única reparación recibe ese diagnóstico. No se guardan ni reinyectan salidas rechazadas, valores sensibles o excepciones crudas.
- La selección de ramas al validar evita atribuir a la alternativa null un error de longitud de un criterio puntuado. Los diagnósticos se refieren al campo original de la salida compacta, antes de expandir las citas.
- La definición de criterio se comparte mediante `$defs`, evitando cuatro copias en el prompt. Las instrucciones explicitan los máximos de 120 caracteres para la razón general, 110 por criterio y 160 por cita. Una pregunta larga requiere un fragmento literal, sin recorte automático del programa.
- Se separa `evaluation_generation_schema()` del contrato estricto: el formato nativo conserva `minLength`/`maxLength` y omite únicamente el patrón `\S` para evitar que el conversor descarte esos límites. El contrato Python conserva el patrón y rechaza texto vacío o formado solo por espacios. No se amplían los máximos de longitud ni se aceptan citas inventadas.
- Los registros de evaluación 1.0.0/1.1.0 se leen con sus reglas y feedback anteriores. La versión de sesión sigue siendo 1.3.0. Pesos, umbrales, descriptores y referencias permanecen intactos.

Se mantienen 2048 tokens de salida, 90 segundos de espera de lectura, cero reintentos de transporte y una única reparación por JSON o contrato inválido. Un timeout no provoca otra generación automática. Se usa exclusivamente Ollama local con `gemma4:e4b` y temperatura 0.

### Comprobación inicial y ajuste motivado

Informe conservado: `outputs/results/evaluator-local-probe-0a2b74b6-8926-4d07-b9c3-82dffda3960d.json`.

| Intervención | Resultado inicial de la corrección | Generaciones | Tiempo |
|---|---|---:|---:|
| 4: «¿Qué sabes de informática?» | Timeout, sin valoración | 1 | 90,04 s |
| 6: reformulación sobre mantenimiento o funcionalidades nuevas | Dos rechazos por `/evidence/0/quote`, regla `maxLength` | 2 | 133,71 s |

La primera versión de la corrección repetía el esquema de criterio y tenía 9506 caracteres de sistema. El diagnóstico nuevo identificó el límite de cita en la intervención 6; no permite afirmar que ese fuera también el campo del rechazo histórico. Se compartió la definición y se explicitaron los límites: el sistema final tiene 8009 caracteres, frente a 8021 del protocolo 1.1.0 anterior. Son tamaños de texto, no una estimación de tokens o velocidad.

El segundo piloto comprueba una versión modificada por esas dos observaciones. Se conservan ambos informes; no se ocultan los fallos iniciales ni se repite una versión sin cambios buscando éxito.

### Diagnóstico del formato nativo

Segundo informe: `outputs/results/evaluator-local-probe-ec8aea23-1865-4998-bae7-e2d3ea660376.json`. La intervención 4 se recuperó al primer intento en 66,74 s. La 6 volvió a fallar dos veces por `/evidence/0/quote`, `maxLength`, límite 160, en 131,39 s. Recibió el máximo exacto en la reparación y aun así lo excedió.

El comportamiento coincide con una [incidencia del conversor de llama.cpp reportada también en Ollama](https://github.com/ggml-org/llama.cpp/issues/30749): combinar `pattern` y límites de longitud puede hacer que solo se aplique el patrón. El [código del conversor](https://github.com/ggml-org/llama.cpp/blob/master/common/json-schema-to-grammar.cpp) permite inspeccionar ese tratamiento. La atribución a esta instalación es una inferencia apoyada por los rechazos locales; no se inspeccionó su binario ni se actualizó Ollama. Por eso se aplica la adaptación en el formato de esta aplicación y se comprueba de nuevo.

El tercer piloto conserva el prompt de 8009 caracteres y cambia únicamente el formato nativo para evitar el conflicto. La validación local sigue usando todas las restricciones originales del contrato 1.2.0. Las tres comprobaciones corresponden a cambios concretos; se conservaron todos sus resultados.

### Piloto de la versión final

Informe: `outputs/results/evaluator-local-probe-cf251ffd-a6af-42f1-a966-0e40be21c5b1.json`. Ambos casos terminaron al primer intento, con cuatro criterios observados y citas literales verificadas. La fuente conserva su huella. No se repitieron los casos tras obtener este resultado.

| Intervención | Resultado original | Resultado final | Niveles P/E/C/N | Entrada/salida | Tiempo final |
|---|---|---|---|---:|---:|
| 4: informática | Sin valoración; evidencia ausente | Evaluada, En desarrollo | 2/1/2/3 | 2608 / 411 | 65,93 s |
| 6: mantenimiento o funcionalidades nuevas | Sin valoración; contrato inválido | Evaluada, Logrado | 3/3/3/3 | 2579 / 374 | 62,07 s |

La cita de la segunda pregunta es un fragmento contiguo de la fuente y cumple el máximo de 160 caracteres. Python no recortó ni reparó el contenido del modelo. Ambos registros tienen `validation=null` en su único intento válido.

Esto recupera técnicamente 2/2 casos conocidos, no mide precisión general. El resultado anterior del primer caso estaba censurado por timeout en el primer piloto y las condiciones de caché/carga no están controladas: no se atribuye una mejora general de velocidad. La espera de aproximadamente un minuto sigue siendo considerable y aquí se midió solo el evaluador, sin alternarlo con candidato y clasificador.

Se mantiene un problema semántico visible: en informática, la razón de enfoque afirma que existe un «objetivo explícito del turno», aunque `request.objective` es null. No se corrigen ni se presentan como referencia aprobada los niveles 2/1/2/3. Esta observación pasa a la calibración pendiente.

### Verificación técnica

La selección final pasó 109 pruebas: recuperación con campo/regla/límite, citas ausentes o excesivas, contexto no autorizado, una única reparación, rechazo de texto en blanco después de adaptar el formato, no exposición de valores rechazados, lectura de registros antiguos e integración con el candidato. Informe: `outputs/results/evaluator-evidence-final-focused-tests.xml`. No se suman las ejecuciones previas a ese total.

La suite completa final pasó **1517 pruebas en 300,45 s**, sin fallos, errores ni omisiones: `outputs/results/evaluator-evidence-full-tests.xml`. La versión de código comprobada conservó sus nueve huellas durante la suite; las doce fuentes protegidas conservaron sus huellas. Los dos `request` del piloto final coinciden exactamente con los originales y los registros vuelven a validar contrato, puntuación y feedback. Evidencia consolidada: `outputs/results/evaluator-evidence-verification.json`.

Hubo ocho generaciones locales en total entre las tres versiones comprobadas, incluidas las fallidas; dos corresponden a la versión final. No hubo llamadas a proveedores LLM externos ni lectura de configuración privada. La consulta de documentación pública del conversor no incluyó datos de la sesión.

### Pendientes que esta corrección no cierra

La validez de la cita demuestra procedencia, no que el nivel asignado sea pedagógicamente correcto. Siguen pendientes la revisión humana de las 40 propuestas del evaluador, la calibración semántica por criterio, la discrepancia de comunicación del clasificador y una medición más amplia de latencia. La exigencia de un episodio pasado ante una pregunta de hábitos sin objetivo explícito también requiere revisión semántica. No se modifica una referencia para mejorar métricas.

---

<a name="comparacion-regla-critica-evaluador"></a>

## Comparación y aprobación de regla crítica — 2 de noviembre de 2026

La comparación se preparó antes de la implementación, usando los niveles de la propuesta revisada 1.1.0. El usuario aprobó explícitamente tanto las 40 referencias como esta regla. Ya está implementada en la rúbrica 1.1.0; se conservaron pesos, porcentajes y archivos originales. [Implementación y calibración](#calibracion-evaluador-few-shot).

### Regla anterior y nueva regla aprobada

La regla anterior impedía Destacado si algún criterio tenía nivel 1, pero permitía Logrado. La nueva regla aprobada limita el global como máximo a En desarrollo cuando cualquier criterio está en 1. Los promedios y porcentajes se conservan; cambian la categoría visible y su explicación. No eleva resultados Inicial ni asigna global a evaluaciones parciales.

| Caso | Criterio en 1 | Promedio | Porcentaje | Global anterior | Global aprobado |
|---|---|---:|---:|---|---|
| E09 | pertinencia | 2.65 | 55.0 | Logrado | En desarrollo |
| E10 | pertinencia | 2.5 | 50.0 | Logrado | En desarrollo |
| E12 | neutralidad | 2.6 | 53.33 | Logrado | En desarrollo |

En esta propuesta cambian 3 de los 40 globales: E09 (color favorito), E10 (liderazgo ejecutivo obligatorio) y E12 (descalificación personal). E28 sigue Inicial; E33 sigue En desarrollo; E15/E36 continúan parciales, sin nivel global. Los otros 37 resultados mantienen su categoría.

E30 permanece Destacado con neutralidad 2: esta alternativa trata los defectos de nivel 1 y conserva los otros acuerdos. No se alteran umbrales para forzar un resultado.

### Decisión aprobada

El usuario aprobó las 40 referencias revisadas y adoptó el límite para nivel 1 antes de la calibración. La aprobación fue explícita tanto sobre contextos y valoraciones como sobre el cambio de política global.

La implementación está versionada y mantiene la lectura de sesiones anteriores según su configuración original. Los globales E09/E10/E12 se recalcularon manteniendo niveles y contextos por criterio. Los ensayos de la nueva política se describen en la guía de calibración.

---

<a name="calibracion-evaluador-few-shot"></a>

## Regla Crítica y Few-Shot del evaluador — 2 de noviembre de 2026

La continuación vigente añadió la separación explícita de Claridad/Neutralidad y evaluó doce casos nuevos fuera de los seis ejemplos. Resultados: Claridad 12/12 y Neutralidad 9/12; E11 continúa pendiente. La [calibración ampliada](#calibracion-ampliada-claridad-neutralidad) documenta los datos y la suite de 1810 pruebas. Los tamaños de prompt y resultados del piloto inicial que siguen son históricos.

### Aprobación y fuentes

El usuario aprobó explícitamente las 40 referencias revisadas 1.1.0 y sus contextos, la Regla Crítica de máximo En desarrollo ante cualquier criterio en 1 y el uso de las seis demostraciones propuestas. El conjunto activo es `data/reference_questions/evaluacion_calidad_aprobada.json`. Se preservaron sin cambios la propuesta original y la revisión aprobada como fuentes históricas. El registro de aprobación y sus huellas está en `outputs/results/evaluator-reference-approval-20261102.json`.

Los niveles y contextos aprobados no se modificaron. Los globales E09, E10 y E12 pasaron de Logrado a En desarrollo al aplicar la regla autorizada. La ponderación 35/30/20/15, los umbrales y las 160 justificaciones permanecen iguales. Los contextos son datos sintéticos de las referencias, no hechos añadidos al candidato.

### Implementación de la Regla Crítica

La rúbrica 1.1.0 usa `level_one_visible_cap="En desarrollo"`. La regla no puede desactivarse dentro de esa versión y se aplica también si el criterio de nivel 1 tiene peso cero. No cambia el promedio o porcentaje. Si el resultado ya es Inicial o En desarrollo, no se eleva. Un criterio insuficiente conserva la ausencia de global.

Los registros de evaluación nuevos usan 1.3.0; el protocolo interpretativo del LLM continúa en 1.2.0 y las sesiones en 1.3.0. Las rúbricas 1.0.0 guardadas en sesiones conservan su máximo Logrado y su explicación histórica. No se reescribieron sesiones. `config/evaluation.legacy-1.0.0.json` conserva los bytes de la configuración anterior.

### Seis demostraciones activas

| Caso | Propósito |
|---|---|
| E03 | Confirmación factual legítima, sin objetivo seleccionado |
| E05 | Hábitos sin inventar que se exige un episodio pasado |
| E07 | Misma pregunta habitual con objetivo explícito de episodio |
| E08 | Amplitud técnica sin inventar un objetivo de demostración |
| E12 | Descalificación con antecedente real en el contexto del caso |
| E15 | Referente ausente: claridad 1 y criterios insuficientes, sin global |

`config/evaluator_few_shot.json` fija IDs y huellas del corpus aprobado, salidas demostrativas, cargo y definición de rúbrica. `harness/evaluator_few_shot.py` comprueba aprobación, partición de desarrollo, niveles/razones aprobados, citas literales, formato y contexto de cada ejemplo. Las salidas demostrativas están en `data/reference_questions/evaluator_demonstrations.json`; son ejemplos de referencia aprobados, no respuestas generadas por un modelo durante la calibración.

Los ejemplos se añaden a las instrucciones; el mensaje de datos conserva exclusivamente el caso actual. No pasan a la memoria del candidato ni a `request.context_turns`. Seis ejemplos de desarrollo no equivalen a entrenar con los 40. Los diez de comprobación conocida permanecen fuera de las demostraciones.

Cada registro nuevo incluye `few_shot`: activación, IDs, huellas y motivo. Un cargo distinto o la rúbrica histórica desactivan ejemplos con motivo registrado. La opción `--no-evaluator-examples` permite comparar sin leer el corpus de demostraciones. Cambiar los descriptores exige una selección compatible; las variaciones de pesos o presupuestos no alteran por sí mismas los niveles demostrados.

### Uso y comparación reproducible

El inicio habitual sigue siendo:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.start_interview --evaluate
```

Para comparar el mismo inicio sin ejemplos del evaluador, añade `--no-evaluator-examples`. El clasificador conserva su propia selección y su propio interruptor.

La vista previa del piloto no crea clientes:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.calibrate_evaluator_few_shot --model gemma4:e4b --preview
```

Sin `--preview`, el piloto ejecuta exclusivamente Ollama local con el modelo indicado. Compara E05, E07 y E11 con/sin ejemplos, seis evaluaciones planificadas. E05/E07 son comprobaciones conocidas de imitación de las demostraciones; E11 es un caso de desarrollo fuera de la selección, para observar transferencia. Ninguno constituye prueba ciega. La entrada de cada pareja es idéntica y las expectativas del caso evaluado no se añaden a su mensaje de datos.

Se conserva temperatura 0, contexto 8192, salida máxima 2048, espera de lectura de 90 s y ninguna repetición de transporte. Solo JSON/contrato inválidos permiten la única reparación. El piloto se detiene en el primer fallo técnico terminal; guarda qué quedó sin ejecutar y las huellas de fuentes. No consulta candidato ni clasificador, no lee configuración privada y no usa API externa.

### Límites

El prompt base mantiene 8009 caracteres y con las seis demostraciones tiene 15855. Esto es tamaño de texto, no un conteo de tokens ni garantía de encaje para cualquier historial. El piloto mide los tokens reales que informe Ollama. Se conserva el rechazo explícito del servidor ante falta de contexto, sin truncamiento silencioso ni ampliación automática de capacidad.

La concordancia con las referencias es distinta de la mera aceptación del contrato. Se reportan niveles, cobertura, error ordinal, comparaciones completas, intentos y latencia. No se ajustan etiquetas para mejorar esas métricas. La validez educativa general y la latencia del flujo completo siguen requiriendo más evidencia.

### Resultado de la calibración inicial

En cuatro casos conocidos de desarrollo, el control coincidió completamente en 0/4 y Few-Shot en 3/4. Las coincidencias por criterio pasaron de 8/16 a 15/16. Los tres casos completos estaban incluidos en las demostraciones; E11, fuera de los seis, corrigió neutralidad pero conserva claridad 3 frente al 4 aprobado. No se presenta el resultado como precisión sobre preguntas nuevas.

Las ocho evaluaciones finales fueron válidas al primer intento. La incorporación de ejemplos añadió 1817 tokens de entrada en cada pareja. No se ejecutó ninguno de los diez casos de comprobación conocida. El [informe de pruebas](#pruebas-calibracion-evaluador-few-shot) conserva el primer ensayo fallido, el ajuste del formato y las métricas finales; la consolidación está en `outputs/results/evaluator-calibration-summary.json`.

---

<a name="pruebas-calibracion-evaluador-few-shot"></a>

## Calibración inicial del evaluador con seis demostraciones

### Implementación comprobada

El usuario aprobó las 40 referencias revisadas 1.1.0 y sus contextos, la Regla Crítica y las seis demostraciones. Se conservan preguntas, contextos y niveles por criterio; solo se recalcularon los tres globales autorizados. La rúbrica 1.1.0 limita el resultado como máximo a En desarrollo ante cualquier criterio en 1, sin cambiar el promedio o porcentaje. La configuración anterior conserva sus bytes y las sesiones antiguas su política.

Pasaron 400 pruebas dirigidas, incluidas las 256 combinaciones de niveles, peso cero para el criterio crítico, parciales, conservación de aritmética, aprobación y huellas de demostraciones, ausencia de casos reservados, lectura histórica y flujo A/B. Informe: `outputs/results/evaluator-calibration-final-focused-tests.xml`.

### Primer ensayo conservado

`outputs/results/evaluator-few-shot-ab-610b47e1-50a1-4dd4-8602-21997a2afcda.json` se detuvo al primer fallo técnico terminal. E05 obtuvo 3/3/3/3 sin ejemplos y coincidió con 3/3/4/4 usando Few-Shot. Después, E07 sin ejemplos generó dos veces una discrepancia con una clasificación inexistente. El diagnóstico fue `discrepancia_sin_clasificacion`; no se descartaron esos campos para aceptar el resultado.

Se corrigió el formato nativo para exigir `discrepancies=[]` cuando `request.classification` es null. La validación Python conserva su rechazo de discrepancias sin clasificación. El ajuste se aplica por igual al control y a Few-Shot. No cambió el prompt base, los ejemplos, los niveles esperados ni la política matemática. Se ejecutó después una comparación completa de esa nueva versión; no se repitió una versión idéntica buscando éxito.

### Comparación final

Informe de los primeros tres casos: `outputs/results/evaluator-few-shot-ab-0f7fe6ff-c596-4209-9f09-1a8fe9a03a23.json`. Se añadió un contraste específico de E08 para comprobar el problema observado previamente de penalizar una pregunta amplia con un objetivo no seleccionado. Sus informes son `question-evaluation-ef94fdaf-4b5b-46a9-8687-a5928e3cf23d.json` y `question-evaluation-b9f6aca4-3ea4-4399-b984-b0132fa28663.json`, en `outputs/results`.

Las ocho evaluaciones finales fueron aceptadas al primer intento, con el mismo modelo local `gemma4:e4b`, temperatura 0, contexto 8192, salida máxima 2048 y espera de lectura 90 s. No se ejecutaron candidato ni clasificador ni se consultó configuración privada. Cada pareja conserva exactamente la misma entrada; las expectativas del caso no entraron a su mensaje de datos. Los dos modos usan la nueva Regla Crítica.

P/E/C/N = pertinencia, adecuación metodológica, claridad y neutralidad.

| Caso | Uso en demostraciones | Referencia aprobada | Sin ejemplos | Con seis ejemplos |
|---|---|---|---|---|
| E05: hábitos, objetivo null | Sí | 3/3/4/4 | 3/3/3/3 | 3/3/4/4 |
| E07: mismos hábitos, objetivo explícito de episodio | Sí | 3/2/4/4 | 3/2/3/3 | 3/2/4/4 |
| E08: conocimientos amplios, objetivo null | Sí | 2/3/2/4 | 2/2/2/3 | 2/3/2/4 |
| E11: «¿Verdad que siempre pruebas todo antes de entregar?» | No | 3/2/4/2 | 3/2/3/3 | 3/2/3/2 |

Coincidencia completa: **0/4 sin ejemplos y 3/4 con Few-Shot**. Coincidencias de nivel por criterio: **8/16 y 15/16**, respectivamente. No hubo predicciones faltantes en la comparación final. Los tres casos que coincidieron completamente estaban en las demostraciones: esto comprueba imitación, no precisión general sobre preguntas nuevas. E11 es un caso de desarrollo conocido fuera de los seis ejemplos; mejoró neutralidad, pero no coincidió completamente.

En E05/E07 ambos modos ya distinguían correctamente enfoque 3 y 2. La mejora de coincidencia en esos casos fue en claridad y neutralidad. En E08, Few-Shot conservó pertinencia y claridad 2 y asignó enfoque 3, con una razón que reconoce que no hay objetivo explícito de prueba. Son entradas de referencia sin historial previo; no equivalen a volver a ejecutar el contexto completo de la sesión original.

### Discrepancia que continúa abierta

E11 conserva claridad 3 frente al 4 aprobado. La explicación del modelo atribuye la menor claridad a una forma «acusatoria y binaria», mezclando propiedades de neutralidad/forma con comprensión. Neutralidad sí pasó de 3 a 2 y se apoyó en «¿Verdad que...?». No se modificó el patrón humano para hacerlo coincidir con el modelo.

La cercanía del porcentaje agregado no sustituye el acuerdo por criterio: errores de signos opuestos pueden compensarse en la suma. El pendiente es separar claridad de inducción, descalificación y formato cerrado, y observarlo en más casos de desarrollo antes de usar comprobación conocida.

### Consumo y latencia observados

| Caso | Sin ejemplos | Con ejemplos | Tokens de entrada sin/con | Tokens de salida sin/con |
|---|---:|---:|---:|---:|
| E05 | 45,56 s | 40,31 s | 2229 / 4046 | 354 / 216 |
| E07 | 60,75 s | 54,97 s | 2239 / 4056 | 416 / 252 |
| E08 | 57,09 s | 45,07 s | 2226 / 4043 | 411 / 249 |
| E11 | 67,94 s | 60,17 s | 2236 / 4053 | 408 / 272 |

Las demostraciones añadieron 1817 tokens de entrada en cada pareja. Estas salidas usaron menos tokens con ejemplos, pero no se controlaron por completo caché o carga del equipo: los tiempos describen estas ejecuciones y no prueban una mejora general de velocidad. La espera sigue siendo considerable para retroalimentación inmediata. Se midió solo el evaluador, no la alternancia de los tres componentes ni un historial largo.

### Evidencia y alcance

Consolidación: `outputs/results/evaluator-calibration-summary.json`. Incluye informes de origen, huellas, registros completos, métricas y la discrepancia pendiente. Hubo 12 generaciones locales contando el primer ensayo detenido; ocho pertenecen a la versión final. No hubo llamadas LLM externas. Se mantuvieron las seis demostraciones aprobadas y ninguno de los diez casos de comprobación conocida se inyectó o se ejecutó para ajustar este piloto.

Se evaluaron cuatro de los treinta casos de desarrollo y ninguno de los diez de comprobación conocida. Las referencias están aprobadas; la calibración del conjunto completo y la validez educativa general siguen abiertas. La aprobación técnica de pruebas no convierte esta muestra pequeña en validación científica.

### Cierre técnico

La suite completa final pasó **1803 pruebas en 316,44 s**, sin fallos, errores u omisiones. Informe: `outputs/results/evaluator-calibration-full-tests.xml`. Las 400 pruebas dirigidas no se suman a ese total.

La evidencia consolidada está en `outputs/results/evaluator-calibration-verification.json`: código final congelado durante la comparación/regresión, dieciséis fuentes protegidas intactas, configuración histórica idéntica byte por byte, dos sesiones anteriores leídas con su rúbrica original y cero cambios de niveles/contextos aprobados. El bloque 10 queda completado; el bloque 11 conserva la calibración ampliada y la diferencia de claridad. Son 11 de 12 bloques implementados.

---

<a name="calibracion-ampliada-claridad-neutralidad"></a>

## Calibración ampliada: Claridad y Neutralidad — 2 de noviembre de 2026

**Estado posterior: aceptado para el MVP.** El usuario cerró y validó explícitamente el Bloque 11, aceptando las discrepancias documentadas como limitaciones de la configuración evaluada. Este informe conserva los resultados sin corregirlos retrospectivamente. [Acta de cierre](#cierre-mvp-evaluador).

### Cambio solicitado

Se incorporó literalmente al prompt del sistema:

> La Claridad evalúa estrictamente si la pregunta es lingüísticamente comprensible y tiene referentes claros. No reduzcas la Claridad si la pregunta es descalificadora, cerrada, inductiva o malintencionada; esos defectos se castigan exclusivamente en Neutralidad.

Una aclaración adicional conserva la coherencia con las referencias aprobadas: ser cerrada no implica por sí solo falta de neutralidad. Si se reduce Claridad, la razón debe identificar ambigüedad, referente ausente o dificultad concreta de comprensión. Los defectos independientes de otros criterios conservan sus propios descriptores.

El prompt previo está archivado byte por byte en `outputs/baselines/evaluator-before-clarity-separation-20261102.md`. No se cambiaron rúbrica, pesos, Regla Crítica, referencias, seis demostraciones ni contratos. La huella del prompt de cada registro identifica las nuevas instrucciones.

### Muestra fijada antes de obtener predicciones

Se seleccionaron doce casos de desarrollo distintos de los cuatro del piloto anterior y fuera de las seis demostraciones. E11 se repite aparte como comprobación del problema que motivó el ajuste. Son trece evaluaciones, no trece casos nuevos.

| Caso nuevo | Qué permite comprobar | Claridad/Neutralidad aprobadas |
|---|---|---|
| E01 | Episodio de depuración claro | 4/4 |
| E04 | Lista factual de herramientas | 4/4 |
| E09 | Comprensión de una pregunta irrelevante | 4/4 |
| E10 | Pregunta cerrada sobre exigencia impropia del cargo | 4/3 |
| E17 | Dos demandas y un antecedente poco delimitado | 3/4 |
| E18 | Acumulación y alcance poco organizado | 2/4 |
| E19 | Alternativas cerradas con referente disponible | 4/3 |
| E24 | Petición imperativa sin respuesta impuesta | 4/4 |
| E25 | Confirmación cerrada con clasificación auxiliar errónea | 4/4 |
| E26 | Experiencia de equipo con clasificación auxiliar errónea | 4/4 |
| E28 | Descalificación y relación imposible entre astrología y desempeño | 2/1 |
| E30 | Pregunta comprensible que presupone una revisión no confirmada | 4/2 |

E11 tiene referencia 4/2 en Claridad/Neutralidad. Antes del cambio, el modelo asignó 3/2 y justificó menor claridad por una forma «acusatoria y binaria». Su entrada se conserva para comparar ese caso concreto antes y después.

Los doce casos nuevos son nuevos respecto del piloto E05/E07/E08/E11. Son referencias conocidas y aprobadas, no casos ciegos ni necesariamente enunciados nunca vistos en sesiones anteriores. Ninguno de los diez casos de comprobación conocida se inyecta o se utiliza en este ajuste.

### Ejecución y controles

`scripts/calibrate_evaluator_clarity.py` fija la muestra y rechaza ejemplos Few-Shot, casos de comprobación conocida, repeticiones del piloto dentro del grupo nuevo o referencias pendientes. `--preview` no crea clientes. El proceso usa solo Ollama local, `gemma4:e4b`, temperatura 0, contexto 8192, salida máxima 2048 y espera de lectura de 90 segundos. No consulta candidato, clasificador, configuración privada ni proveedor externo.

Se guarda cada resultado antes de pasar al siguiente caso, incluidas las diferencias y los fallos. Solo se permite la reparación única de JSON/contrato prevista por el evaluador; los errores de transporte no se reintentan. Tras tres fallos técnicos terminales consecutivos se detiene el lote. `--resume` continúa exclusivamente los casos pendientes y comprueba modelo, selección, fuentes, prompt y registros ya guardados antes de crear un cliente.

El informe separa métricas de los doce casos nuevos de E11. Una ausencia no se convierte en acierto ni en error ordinal cero. Además de los niveles, conserva las razones de Claridad y Neutralidad para revisar si un desacuerdo es de anclaje o mezcla de criterios. Las razones no se reclasifican mediante palabras clave para alterar la puntuación.

Comandos:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m scripts.calibrate_evaluator_clarity --model gemma4:e4b --preview
.\.venv\Scripts\python.exe -X utf8 -m scripts.calibrate_evaluator_clarity --model gemma4:e4b
```

El segundo comando consulta el modelo local. El informe se guarda en `outputs/results/evaluator-clarity-expanded-<UUID>.json`.

### Verificación técnica previa

Pasaron 46 pruebas dirigidas: selección ajena a demostraciones y comprobación conocida, vista previa sin cliente, entradas sin expectativas filtradas, persistencia de trece casos, continuación sin repetir completados, rechazo de fuentes cambiadas, errores sin predicciones ficticias y regresión de la integración existente. Informe: `outputs/results/evaluator-clarity-focused-tests.xml`. Estas pruebas utilizan transporte simulado y no demuestran el comportamiento semántico del modelo.

### Resultados de los doce casos nuevos

Informe original: `outputs/results/evaluator-clarity-expanded-8818f677-14ed-4c76-bcb3-c703f29bed0a.json`. Los doce casos nuevos terminaron con análisis válido al primer intento. La muestra satisface el mínimo de diez sin contar E11 ni reutilizar las demostraciones.

| Caso | Claridad esperada/obtenida | Neutralidad esperada/obtenida | Coincidencia de los cuatro criterios |
|---|---|---|---|
| E01 | 4/4 | 4/4 | No |
| E04 | 4/4 | 4/4 | Sí |
| E09 | 4/4 | 4/4 | Sí |
| E10 | 4/4 | 3/4 | No |
| E17 | 3/3 | 4/4 | Sí |
| E18 | 2/2 | 4/4 | No |
| E19 | 4/4 | 3/4 | No |
| E24 | 4/4 | 4/4 | No |
| E25 | 4/4 | 4/4 | Sí |
| E26 | 4/4 | 4/4 | No |
| E28 | 2/2 | 1/1 | Sí |
| E30 | 4/4 | 2/4 | No |

Claridad coincide en **12/12**, Neutralidad en **9/12**, Pertinencia en **7/12** y Adecuación metodológica en **6/12**. Coinciden los cuatro criterios y el global en **5/12**. No hay predicciones faltantes en los doce casos nuevos. Estos resultados no son comparables como porcentaje antes/después con el piloto anterior: cambió la muestra y no se obtuvieron predicciones previas para estos doce casos.

Los controles conservaron claridad 3 en E17 y 2 en E18/E28: la instrucción no elevó indiscriminadamente todas las notas de claridad a 4. Las preguntas cerradas comprensibles E10/E19/E25 recibieron claridad 4. En E09, la irrelevancia se reflejó en pertinencia 1 sin reducir claridad.

### Revisión de las razones y diferencias

- E10/E19 reciben neutralidad 4 frente al 3 aprobado. Sus razones consideran ausencia de juicio o respuesta impuesta; no trasladan ese desacuerdo a claridad.
- E30 recibe neutralidad 4 frente al 2 aprobado. La pregunta presupone que pidió revisión, hecho que su contexto no confirma. El modelo no detectó ese defecto y se limitó a decir que no impone un juicio. Su claridad 4 coincide con la referencia.
- E17 coincide en claridad 3, pero la razón admite referentes claros y no explica bien qué falta para 4.
- E28 coincide en claridad 2 y neutralidad 1; ambas razones son genéricas y terminan de forma semánticamente incompleta. El acuerdo numérico no basta para acreditar su fundamento.

Estas son observaciones del asistente sobre las razones, no nuevas etiquetas humanas ni sustituciones del patrón aprobado. Se conservaron niveles y justificaciones originales de las referencias.

### E11: la discrepancia no queda resuelta

El primer E11 agotó la espera de lectura en 90,05 s, sin análisis ni notas. El resto del lote respondió con normalidad y, como se anunció antes de conocer su resultado, se hizo una sola comprobación adicional de E11 después del lote. Se mantuvieron 90 s, cero reintentos automáticos de transporte, mismo modelo, seis demostraciones y prompt. El primer fallo permanece en el informe original; el caso no se repitió mediante `--resume` ni se reemplazó su registro.

La comprobación adicional está en `outputs/results/question-evaluation-f2dafe39-f60d-4cc7-84c8-d20e272d7514.json`. Terminó al primer intento en 58,83 s y obtuvo **3/2/3/2**. La referencia sigue siendo **3/2/4/2**. Claridad permanece en 3 y su razón es únicamente «El uso de» (el texto termina ahí), incompleta; Neutralidad coincide en 2. El JSON es estructuralmente válido, pero esa razón no permite conocer el motivo de la nota de claridad. No se puede asegurar que la causa continúe siendo el tono, ni dar el caso por corregido.

La entrada de E11 coincide exactamente con la del piloto anterior; los ejemplos son los mismos y cambia la huella del prompt por las nuevas instrucciones. La observación anterior fue claridad 3 con referencia al tono/forma; ahora la nota no cambia y la explicación es insuficiente. No se atribuye el timeout a una causa concreta ni se presenta la diferencia de tiempos como prueba de rendimiento.

### Alcance y evidencia

Se hicieron **14 solicitudes locales**: trece del lote y una comprobación adicional. Trece devolvieron análisis; una agotó la espera. Los doce casos nuevos válidos tardaron entre 40,62 y 64,50 s. No hubo llamadas LLM externas, cambios de referencias o demostraciones ni uso de los diez casos de comprobación conocida.

Consolidación y observaciones por caso: `outputs/results/evaluator-clarity-expanded-summary.json`. La instrucción está aplicada y la muestra ampliada está evaluada. E11, las diferencias de neutralidad y la calidad de algunas razones se registraron durante la calibración y posteriormente se aceptaron como limitaciones del MVP al cerrar el Bloque 11. No se afirma separación universal ni validación científica con esta muestra conocida.

### Cierre de verificación

La suite completa pasó **1810 pruebas en 333,02 s**, sin fallos, errores ni omisiones: `outputs/results/evaluator-clarity-full-tests.xml`. Las 46 pruebas dirigidas no se suman a ese total. Se verificó la presencia literal de la instrucción en el sistema utilizado, los mismos seis ejemplos en todos los registros y las huellas de los archivos durante evaluación y regresión.

Cuarenta y dos fuentes previas permanecen intactas, incluidas referencias aprobadas, demostraciones, rúbrica, Regla Crítica, candidato, clasificador y sesiones anteriores. La única fuente previa modificada es el prompt autorizado; su versión anterior conserva los bytes originales en el archivo de respaldo. La versión comprobada conserva sus 45 huellas. Evidencia consolidada: `outputs/results/evaluator-clarity-expanded-verification.json`.
