# Proyecto Inicial IWG400

Main branch: no se toca hasta que toda la app este funcional

Develop branch: se usara para testear los featuresy posteriormente integrarlos a main, arreglar posibles conflictos de archivos


# Instrucciones de arranque:

1) tener descargado Python (ver. 3.14) y Git (ver. mas reciente)

2) bajarse la rama "develop" del repositorio a tu computador(git clone "web_url" o vincula como desees)

3) Activa el entorno virtual(venv) en tu terminal, comando en terminal: ".\.venv\Scripts\Activate" (para windows con PowerShell) o "source .venv/bin/activate" para Linux.

4) descarga las dependencias de requirements.txt (comando en terminal: "pip install -r requirements.txt")

5) crear la estructura de la base de datos (comando en terminal: "py manage.py migrate")

6) Correr el servidor (comando en terminal: "py manage.py runserver")

7) Listo! c:

## Datos de pH de agua potable

El mapa usa como respaldo local la planilla SISS de junio de 2026, disponible en
[`apps/mapa/data/siss_agua_potable_202606.xlsx`](apps/mapa/data/siss_agua_potable_202606.xlsx).
Su extracción de las 400 filas del parámetro pH y la trazabilidad están en
[`apps/mapa/data/siss_ph_202606.json`](apps/mapa/data/siss_ph_202606.json). La fuente
mensual reporta autocontroles de las concesionarias; no son mediciones puntuales
en las estaciones de aire. El mapa calcula la media simple de los servicios con
valor numérico y región geocodificada, y muestra el periodo y el conteo. En esta
captura 106 de 176 servicios con pH numérico tuvieron una coincidencia geográfica
unívoca; los demás se excluyen y no se les asigna una región.

La región de cada estación de aire proviene de los metadatos de SINCA. Las
regiones de servicios se asociaron únicamente por coincidencias exactas y
unívocas en GeoNames y OpenStreetMap Nominatim; las fuentes, fecha y método están
registrados en el JSON. Si el mismo nombre aparece en más de una región, queda
sin asignar.
