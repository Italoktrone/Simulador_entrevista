# Entorno de Python del proyecto

## Estado comprobado

El 30 de octubre de 2026 se creó `.venv` dentro del proyecto con Python **3.14.3**. Se instalaron las dependencias de `requirements.txt` en ese entorno y se verificó que `sys.prefix` es distinto de `sys.base_prefix`. La instalación se realizó en el entorno del proyecto, no en el Python global.

| Componente directo | Versión comprobada | Uso |
| --- | --- | --- |
| Python | 3.14.3 | Intérprete del proyecto |
| jsonschema | 4.26.0 | Validación estructural de los JSON |
| httpx | 0.28.1 | Comunicación HTTP con Ollama |
| pytest | 9.2.0 | Ejecución de las pruebas automatizadas |

`requirements.txt` fija las tres dependencias directas. Los paquetes auxiliares se instalaron automáticamente porque esas bibliotecas los necesitan. HTTPX se incorporó al comenzar la Etapa 5 y `pip check` volvió a confirmar que no hay dependencias incompatibles.

## Uso desde PowerShell

Trabajar desde la raíz del proyecto:

```powershell
Set-Location -LiteralPath 'C:\Users\franc\Downloads\Ejemplo_de_proyecto'
```

Se usa directamente `.\.venv\Scripts\python.exe`. No hace falta activar el entorno para ejecutar los comandos documentados ni modificar la configuración de ejecución de scripts de PowerShell.

Para comprobar el entorno ya creado:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; print('jsonschema:', version('jsonschema')); print('httpx:', version('httpx')); print('pytest:', version('pytest'))"
```

Resultado esperado:

```text
Python 3.14.3
No broken requirements found.
jsonschema: 4.26.0
httpx: 0.28.1
pytest: 9.2.0
```

Estos comandos comprueban el intérprete, las dependencias instaladas y sus versiones. No ejecutan todavía una entrevista ni una suite de pruebas.

## Recreación del entorno

Este procedimiento es para una copia del proyecto que todavía no tenga `.venv`; no es necesario repetirlo para la instalación ya comprobada. Requiere Python 3.14 instalado y conexión para descargar paquetes.

En PowerShell, desde la raíz del proyecto:

```powershell
py -3.14 -m venv .venv
Test-Path -LiteralPath '.venv\Scripts\python.exe'
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check --timeout 15 --retries 1 -r requirements.txt
```

La creación puede terminar sin mensajes. `Test-Path` debe mostrar `True`. La instalación debe terminar con un mensaje de paquetes instalados, o indicar que ya estaban satisfechos. Después se deben ejecutar las comprobaciones de la sección anterior.

Las versiones directas están fijadas; las versiones auxiliares podrían cambiar al resolver una instalación futura. El siguiente listado documenta lo realmente instalado en esta comprobación, sin afirmar que `requirements.txt` sea un bloqueo completo de todas las dependencias:

```text
anyio==4.15.1
attrs==26.1.0
certifi==2026.10.23
colorama==0.4.6
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
packaging==26.3
pluggy==1.7.0
Pygments==2.21.0
pytest==9.2.0
referencing==0.37.0
rpds-py==2026.9.1
typing_extensions==4.16.0
```

## Evidencia de verificación

- El ejecutable utilizado fue `C:\Users\franc\Downloads\Ejemplo_de_proyecto\.venv\Scripts\python.exe` y confirmó un entorno virtual activo por su ruta, sin activación de la terminal.
- `pip check` devolvió `No broken requirements found.`.
- `python -m pytest --version` devolvió `pytest 9.2.0`. Esto comprueba su disponibilidad; no equivale a haber ejecutado pruebas del proyecto.
- `Draft202012Validator.check_schema` aceptó los esquemas de candidato y puesto.
- `Draft202012Validator.validate` aceptó ambos JSON aprobados.
- Dos copias en memoria, cada una sin su identificador obligatorio, produjeron `ValidationError` por la regla `required`.
- Ambos JSON conservaron los contenidos y hashes documentados previamente. No se consultó un LLM.

Estas comprobaciones puntuales verifican el entorno y la aplicación básica de los esquemas desde Python. No implementan el módulo de carga ni resuelven las comprobaciones semánticas de fechas, identificadores y referencias pendientes.

El usuario confirmó en su PowerShell las versiones de Python, `jsonschema` y `pytest`, junto con la salida satisfactoria de `pip check`. Después se implementó el validador estructural compartido y se ejecutaron sus primeras 22 pruebas con éxito; véase [el registro de pruebas unitarias](../tests/unit/README.md).

## Incidencias y correcciones

La primera ejecución de `py -3.14 -m venv .venv` no pudo acceder al lanzador de Python desde el entorno restringido de la herramienta. Se repitió con el permiso correspondiente y terminó correctamente.

La primera descarga de dependencias no pudo resolver el servidor de paquetes (`getaddrinfo failed`). Se repitió con el permiso de conexión y la instalación terminó correctamente. No fue un error de los JSON ni una incompatibilidad de las versiones elegidas.

## Errores habituales al repetir los comandos

- Si PowerShell no encuentra `.\.venv\Scripts\python.exe`, comprobar la carpeta con `Get-Location` y la existencia del ejecutable con `Test-Path`. Si falta el entorno, seguir el procedimiento de recreación.
- Si aparece `No module named jsonschema` o `No module named pytest`, utilizar el ejecutable de `.venv` y repetir la instalación desde `requirements.txt` en ese entorno.
- Si falla la descarga, conservar el mensaje completo y comprobar la conexión antes de cambiar versiones o instalar otras herramientas.

## Referencias consultadas

- [Documentación oficial de venv](https://docs.python.org/3/library/venv.html).
- [jsonschema 4.26.0 en PyPI](https://pypi.org/project/jsonschema/4.26.0/).
- [pytest 9.2.0 en PyPI](https://pypi.org/project/pytest/9.2.0/).
- [HTTPX 0.28.1 en PyPI](https://pypi.org/project/httpx/0.28.1/).
