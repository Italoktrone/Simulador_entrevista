# Configuraciones de entrevista

[basica.json](basica.json) es la primera configuración del escenario, con formato `1.0.0`. Se valida mediante [interview_config.schema.json](../../schemas/interview_config.schema.json). [interview_config.py](../../harness/interview_config.py) ya carga y valida la configuración, el candidato y el puesto, y comprueba que sus referencias coincidan.

## Opciones iniciales

| Campo | Valor o propósito |
| --- | --- |
| `config_id` | `entrevista-basica-001`, identificador de esta configuración reutilizable. |
| `candidate_id` | Referencia a `cand-001`; no copia sus antecedentes. |
| `job_id` | Referencia a `puesto-dev-junior-001`; las competencias permanecen en el archivo del puesto. |
| `modality` | `laboral_general`. |
| `approach` | `mixto`, para admitir preguntas conductuales e hipotéticas. |
| `preferred_question_styles` | Abiertas, cerradas y directivas. |
| `max_questions` | 20. |

Se eligió una combinación general y mixta para la primera entrevista. Los estilos representan preferencias; no clasifican las preguntas, no determinan su calidad y no producen puntuaciones. La configuración no contiene rúbrica, evaluación ni ajustes del proveedor LLM.

`config_id` identifica una plantilla y puede reutilizarse. No es el identificador único de sesión: el controlador genera uno distinto para cada ejecución. La fecha de referencia se conserva en el candidato, sin duplicarla aquí.

## Contrato y comprobaciones

El esquema exige ocho campos y rechaza campos adicionales. Representa tres modalidades (`laboral_general`, `tecnica`, `por_competencias`), tres enfoques (`conductual`, `situacional`, `mixto`) y combinaciones no vacías de estilos (`abierta`, `cerrada`, `directiva`), sin elementos repetidos. El máximo de preguntas debe ser un entero entre 1 y 20; no admite booleanos ni valores superiores a 20.

Estas opciones describen configuración válida, no evaluadores ejecutables. `InterviewRuntime` ya aplica el contador y finalización en la consola; el archivo por sí mismo no los implementa. Se cuenta cada pregunta válida enviada, incluso si falla la respuesta, y se excluyen comandos y entradas vacías.

Las 40 pruebas de [test_interview_config_schema.py](../../tests/unit/test_interview_config_schema.py) comprueban opciones, límites y valores incorrectos. También documentan un límite del esquema: `cand-999` tiene formato válido aunque no corresponda al perfil cargado. El cargador de configuración añade ahora esa comprobación y rechaza la discrepancia.

Se añadió al validador común únicamente un mensaje en español para la regla `maximum`, ahora necesaria para explicar un límite superior a 20. El conjunto completo terminó el 30 de octubre de 2026 con **176 passed in 14.08s**: 171 pruebas unitarias y cinco de integración. No se añadieron dependencias ni se consultó un LLM.

Una comprobación puntual confirmó que los identificadores del archivo básico coinciden con el candidato, su puesto objetivo y el puesto aprobado. La regla de carga descrita a continuación implementa esa comprobación en el programa.

## Carga integrada del escenario

`load_interview_setup(config_path=..., candidate_path=..., job_path=...)` usa los tres archivos iniciales como valores predeterminados y permite otras rutas. Los valores predeterminados se ubican respecto del módulo, sin depender de la carpeta actual. No busca archivos ni construye rutas a partir de identificadores.

Valida primero la configuración, carga el candidato con sus reglas e integridad, valida el puesto y comprueba tres relaciones: `config.candidate_id` con el candidato cargado, `config.job_id` con el puesto cargado, y `candidate.target_job_id` con ese mismo puesto. Al terminar vuelve a comprobar la huella del candidato.

Las discrepancias generan `InterviewConfigError` con ruta del documento/campo, regla y mensaje en español. Los errores de lectura, estructura, coherencia o integridad conservan las excepciones de sus módulos.

El resultado es un `InterviewSetup` inmutable: `candidate` contiene el perfil protegido; `config_dict()` y `job_dict()` devuelven copias independientes de las instantáneas. Las ediciones externas de configuración o puesto no cambian el escenario ya preparado; una carga nueva utiliza los nuevos contenidos. El cargador no crea conversaciones o contadores. La consola utiliza `InterviewRuntime` para el envío, el límite y los turnos completos en memoria; el registro añade un identificador propio, fechas e intentos. El guardado del historial sigue pendiente.

Las 21 pruebas de [test_interview_config.py](../../tests/unit/test_interview_config.py) cubren referencias incorrectas, otros identificadores coherentes, documentos ausentes o inválidos, copias y cargas independientes, cambios externos, otra carpeta actual y cambios del candidato durante la preparación. La nueva prueba de integración confirma referencias y competencias, preservando los tres archivos aprobados.

El usuario confirmó la unidad anterior con **176 passed in 8.27s**. El conjunto posterior terminó con **198 passed in 8.34s**: 192 pruebas unitarias y seis de integración. No se añadieron dependencias ni se consultó un LLM. La coincidencia de identificadores no demuestra que el candidato cumpla todos los requisitos del puesto.

## Evidencia de archivos

SHA-256 de la configuración comprobada:

```text
A9E1A5B95802F1B0E404BA3B4344919F4FC2CB97E54528A6DC76B8D1F95109BD
```

SHA-256 del esquema comprobado:

```text
622741D6C1C955F319FE2D3205FED65B99422C87E48C497B2E45E58D439C715A
```
