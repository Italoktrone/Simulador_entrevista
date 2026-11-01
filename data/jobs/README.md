# Puestos ficticios

[desarrollador_junior.json](desarrollador_junior.json) contiene la descripción aprobada del puesto `puesto-dev-junior-001`, Desarrollador de Software Junior en la organización ficticia Aplicaciones Nexo.

Los campos separan responsabilidades, requisitos, competencias que se pueden explorar y expectativas del nivel junior. El candidato lo referencia mediante `target_job_id`; este archivo no copia sus antecedentes internos. Las competencias son datos descriptivos, sin rúbrica, puntuaciones ni evaluación implementada.

El formato de puesto es `1.0.0`. Su contrato está en [job.schema.json](../../schemas/job.schema.json), basado en JSON Schema 2020-12. [json_loader.py](../../harness/json_loader.py) y [schema_validator.py](../../harness/schema_validator.py) leen y validan el documento. [interview_config.py](../../harness/interview_config.py) comprueba sus vínculos con configuración y candidato y conserva una instantánea con acceso mediante copias. La entrevista sigue pendiente. Las comprobaciones históricas siguientes son puntuales; las pruebas actuales están en [tests/unit](../../tests/unit/README.md) y [tests/integration](../../tests/integration/README.md).

El usuario confirmó en su PowerShell la lectura del identificador, cargo, organización y las seis competencias, sin errores.

## Verificación inicial

El 30 de octubre de 2026 se ejecutaron **11 comprobaciones satisfactorias**: lectura UTF-8 estricta y sintaxis JSON; campos previstos; versión y naturaleza ficticia; coincidencia del identificador con el perfil; cargo, organización y resumen; cinco responsabilidades; cuatro requisitos; seis competencias; nivel inicial y cuatro capacidades no exigidas; conservación de la fecha de referencia; integridad del candidato respecto del hash anterior e integridad del puesto durante la comprobación.

La ejecución finalizó sin errores. El perfil original mantuvo el hash `6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3`.

SHA-256 del puesto comprobado:

```text
40C16AEEB4D41BE7FC0EFF3D8237178C883CAD294E9D04F96C4D4F9B81455F77
```

No se ejecutaron pruebas de pytest, entrevistas ni consultas a un LLM. Los hashes verifican contenidos de archivos; no garantizan la corrección semántica de respuestas futuras.

## Contrato estructural del puesto

El esquema requiere los diez campos actuales, admite la versión de formato `1.0.0`, exige que el escenario sea ficticio y rechaza campos adicionales, incluidos los del objeto `seniority_expectations`. Los textos deben contener al menos un carácter que no sea espacio en blanco; las listas deben tener textos no vacíos y sin duplicados exactos. `job_id` debe comenzar por `puesto-` y contener segmentos de letras minúsculas o números separados por guiones, sin espacios.

El esquema permite otros nombres, organizaciones y cantidades de elementos en las listas, siempre que sean estructuralmente válidos. No comprueba que el contenido sea semánticamente adecuado para un cargo junior ni que el identificador coincida con la referencia del candidato; esas relaciones necesitarán reglas de Python. Tampoco evalúa las competencias ni las preguntas.

Se verificó el contrato el 30 de octubre de 2026 mediante `Test-Json` de PowerShell **7.6.5**, sin instalar paquetes ni ejecutar Python. Resultado: **60 casos satisfactorios**, de los cuales dos fueron aceptados y 58 rechazados como se esperaba. Los ejemplos inválidos se construyeron en memoria; no se guardaron sobre los datos originales.

| Grupo de casos | Cantidad |
| --- | ---: |
| Puesto aprobado y otro puesto válido | 2 |
| Ausencia de campos obligatorios, principales o anidados | 12 |
| Identificadores incorrectos | 5 |
| Versión incorrecta o de tipo inválido | 2 |
| Indicador ficticio falso o de tipo inválido | 3 |
| Textos vacíos, en blanco o de tipo inválido | 13 |
| Listas vacías, duplicadas o con tipos incorrectos | 17 |
| Campos adicionales principales o anidados | 2 |
| Estructuras raíz o anidadas incorrectas y JSON mal formado | 4 |

Ambos JSON originales conservaron sus hashes respecto de las verificaciones anteriores. Esta verificación no se ha ejecutado con `jsonschema` ni con `pytest`; se hará cuando preparemos el entorno de Python.

SHA-256 del esquema comprobado:

```text
02C293A4CCB9791E3681A45FEB99B8A1F0BA94201E3EDB8BCD2BB6F68039C1D3
```

Referencias consultadas: [JSON Schema Validation 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation) y [documentación de validación de python-jsonschema](https://python-jsonschema.readthedocs.io/en/stable/validate/).
