# Perfiles ficticios

El primer perfil es [candidato_junior.json](candidato_junior.json): Nicolás Vera Soto, identificado como `cand-001`, con fecha fija de referencia del escenario `2026-10-20`. El usuario aceptó la propuesta con esa única corrección de fecha.

El archivo contiene el perfil interno completo. Sus antecedentes y evidencias son ficticios; no representan mediciones reales del programa. El currículum público se genera desde esta fuente mediante `CandidateProfile.to_public_resume()`, sin mantener una copia manual.

Las fechas de formación y experiencia usan meses (`AAAA-MM`) para conservar la precisión de los antecedentes aprobados. La fecha de referencia del escenario usa un día concreto (`AAAA-MM-DD`) y es independiente de la fecha de ejecución del programa.

El contrato está en [candidate.schema.json](../../schemas/candidate.schema.json) y se aplica con [schema_validator.py](../../harness/schema_validator.py). [json_loader.py](../../harness/json_loader.py) lee los archivos y [profile.py](../../harness/profile.py) valida y protege al candidato y deriva su CV. [harness/application/cli.py](../../harness/application/cli.py) lo presenta como texto. [interview_config.py](../../harness/interview_config.py) carga también configuración y puesto y comprueba sus referencias con `candidate_id` y `target_job_id`. La oferta permanece en [desarrollador_junior.json](../jobs/desarrollador_junior.json). La combinación se comprueba en [tests/integration](../../tests/integration/README.md). Todavía no hay entrevista ejecutable.

## Evidencia de comprobación inicial

El 30 de octubre de 2026 se ejecutó una comprobación puntual de lectura UTF-8 estricta, sintaxis JSON, campos previstos, identidad, fecha de referencia, cronología, identificadores, referencias internas y conservación del contenido durante la comprobación. Resultado final: **13 comprobaciones satisfactorias**, con salida de ejecución correcta. No se ejecutaron pruebas de pytest ni consultas a un LLM.

La primera ejecución de la comprobación se detuvo al incluir un periodo nulo: la práctica no contiene cambios de jornada y el recorrido intentaba tratarlos como si existieran. Se corrigió únicamente el recorrido de comprobación para seleccionar los cargos con esos periodos. El JSON no necesitó cambios; la ejecución completa posterior fue satisfactoria.

SHA-256 del perfil comprobado:

```text
6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3
```

Este resultado corresponde al archivo y las comprobaciones descritas. La comparación del hash no demuestra consistencia semántica de respuestas futuras del modelo ni integridad durante una entrevista que todavía no se ha implementado.

El usuario confirmó que, al leer `scenario_reference_date` desde su PowerShell, obtuvo `2026-10-20` sin errores. Esta confirmación verifica esa lectura en su equipo; todavía no corresponde a la ejecución de una entrevista.

## Contrato estructural del candidato

El esquema usa JSON Schema 2020-12 y exige los 24 campos principales del perfil. Comprueba tipos, textos no vacíos, listas y duplicados exactos, campos adicionales y estructuras anidadas. Mantiene la versión de formato `1.0.0` y exige que el escenario sea ficticio. No fija el nombre, el identificador concreto o la fecha de referencia del primer candidato; esos antecedentes permanecen en el archivo de datos aprobado.

Los proyectos profesionales requieren referencias a una experiencia y un cargo; los académicos requieren formación, tamaño del equipo y resultado. Se rechaza mezclar las referencias académicas y laborales en un mismo proyecto. Los cargos pueden detallar responsabilidades directamente o mediante periodos de jornada. Cada logro debe referenciar al menos un proyecto o situación; las competencias, fortalezas y áreas de mejora deben incluir referencias a situaciones. Los estudios de posgrado y las certificaciones son listas de textos que pueden estar vacías.

El 30 de octubre de 2026 se ejecutó una comprobación puntual con `Test-Json` de PowerShell **7.6.5**, sin instalar paquetes ni ejecutar Python. Los ejemplos se generaron en memoria sin modificar el perfil original.

| Grupo de casos | Cantidad | Resultado observado |
| --- | ---: | --- |
| Perfiles estructuralmente válidos | 4 | Aceptados |
| Variantes con errores de estructura o sintaxis | 76 | Rechazadas |
| Límites que requerirán reglas de Python | 4 | Aceptados por el esquema, como se esperaba |

Los casos de aceptación incluyeron el perfil aprobado, otro nombre e identificador, un cargo con responsabilidades sin periodos de jornada y la ausencia de una nota opcional. Los rechazos incluyeron la ausencia de cada uno de los 24 campos principales, valores de tipos incorrectos, textos vacíos, referencias mal formadas, listas repetidas y estructuras incompletas o incompatibles de proyectos y experiencias.

Los cuatro límites comprobados fueron:

- Una referencia `S9999`, con formato válido pero sin situación existente.
- Dos proyectos distintos con el mismo identificador.
- Estudios con el mes de inicio posterior al de término.
- Una fecha con forma `AAAA-MM-DD` pero día inexistente: `2026-02-31`.

Estos ejemplos no se consideran antecedentes válidos del candidato. Demostraron que validar la estructura no basta para validar relaciones, unicidad de identificadores, cronología o calendario. Actualmente `validate_profile_data` rechaza esos cuatro casos y comprueba los vínculos internos. `load_interview_setup` comprueba además las referencias con el archivo externo del puesto y la configuración.

Total: **84 casos con el resultado esperado**, incluidos los cuatro límites documentados. No se ejecutaron pruebas de `pytest`, validación con `jsonschema` ni consultas a un LLM. El perfil, el puesto y el esquema del puesto conservaron sus hashes anteriores.

SHA-256 del esquema del candidato comprobado:

```text
0629F2B1FAE7D824A252DC7E395791F420DE62A003D4DF5DAC316C34D26CF20F
```

## Reglas de coherencia implementadas

El 30 de octubre de 2026 se incorporó `validate_profile_data(profile, schema)`. Se validan primero los campos mediante el esquema y después las relaciones estructuradas, sin leer archivos ni modificar entradas. El resultado es `None` si se cumplen las reglas o un error con ruta y tipo de problema.

Los intervalos mensuales incluyen ambos extremos; se comparan con el mes fijo del escenario, no con la fecha actual. Las jornadas de un cargo, si están declaradas, deben cubrir todo su periodo sin huecos ni solapamientos. No se rechaza por defecto estudiar y trabajar simultáneamente. Los proyectos deben pertenecer a un cargo o formación existentes y desarrollarse dentro de su periodo. Los identificadores de los registros deben ser únicos y sus referencias deben existir y corresponder a los registros declarados.

El conjunto completo terminó con **95 passed in 6.87s**: 40 nuevas pruebas unitarias del perfil, una nueva prueba de integración y los 54 casos anteriores. La prueba de integración conserva los bytes del perfil y su hash original `6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3`. Véase [el registro de pruebas unitarias](../../tests/unit/README.md).

Estas reglas no verifican automáticamente el significado de los relatos ni garantizan consistencia de respuestas futuras del modelo. No se ha implementado todavía una entrevista.

## Carga protegida e integridad

`load_profile(path)` lee el perfil y su esquema, aplica las reglas estructurales y de coherencia y devuelve `CandidateProfile`. Conserva el contenido como una cadena interna inmutable, excluida de su representación de diagnóstico. El acceso mediante `to_dict()` devuelve una copia nueva; cambiarla no modifica la instantánea ni el archivo.

La huella `source_sha256` se calcula sobre los mismos bytes que se interpretaron, mediante la utilidad `load_json_with_bytes`. Se conserva la ruta absoluta del original y se vuelve a comprobar su huella al terminar la carga. `assert_source_unchanged()` permite repetir la comprobación; comunica cambios, eliminación o imposibilidad de lectura con `ProfileIntegrityError`. El futuro controlador deberá utilizarla también al terminar la entrevista.

El 30 de octubre de 2026 el conjunto completo terminó con **116 passed in 10.97s**. Los 18 casos de protección y las dos nuevas comprobaciones del lector usan copias temporales o simulaciones; la cuarta prueba de integración confirma el perfil aprobado y su hash original. No se cambió el JSON del candidato ni se añadieron dependencias.

La huella detecta cambios de bytes, incluidos cambios de formato. No impide ediciones externas ni garantiza corrección semántica de respuestas del modelo. Todavía no se ha implementado una entrevista ni se ha probado esa comprobación durante una conversación.

## Currículum resumido generado

`to_public_resume()` selecciona explícitamente nombre, resumen profesional, formación, cargos con sus periodos y responsabilidades, áreas técnicas, herramientas y proyectos con aportes personales. Incluye `candidate_id` como referencia pública, pero el formato de consola no lo imprime. No se copian relatos, logros y evidencias internas, competencias internas, fortalezas, mejoras, motivación, personalidad, límites de experiencia o notas de equipo y autoridad. La selección se aplica también a cada objeto anidado; el alcance detallado de conocimientos y los límites de contribuciones tampoco forman parte del CV.

La presentación obtiene esa vista pública desde la instantánea y no accede al archivo. La fuente permanece única: los datos no se duplican manualmente en otro JSON. Cambiar una copia del CV no modifica la instantánea ni las siguientes vistas.

El conjunto completo terminó el 30 de octubre de 2026 con **136 passed in 15.11s**. Las 19 pruebas unitarias nuevas comprueban la proyección y su presentación; la quinta prueba de integración conserva el contenido y la huella del candidato original. No se añadieron dependencias ni se consultó un LLM. La selección por campos no analiza el significado de los textos profesionales autorizados; los antecedentes siguen requiriendo revisión humana.
