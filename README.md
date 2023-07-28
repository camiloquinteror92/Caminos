# Caminos 

# Aplicación Flask para Generar Informes a partir de Consultas a un Servicio REST de ArcGIS

## Descripción

Esta es una aplicación web desarrollada con Flask que permite generar informes a partir de consultas a un servicio REST de ArcGIS. La aplicación utiliza el módulo `requests` para realizar solicitudes HTTP a un servicio web de ArcGIS y obtener datos geoespaciales.

El servicio REST de ArcGIS proporciona información sobre diferentes capas (layers) con atributos asociados a entidades geográficas. La aplicación permite realizar búsquedas utilizando diferentes criterios, como nombre de departamentos, municipios, veredas, organizaciones y otros campos.

Una vez que se obtienen los datos, la aplicación genera informes en formato HTML que muestran los atributos de las entidades geográficas que cumplen con los criterios de búsqueda. Además, la aplicación permite descargar todos los informes generados en un archivo ZIP.

## Requisitos

- Python 3.x
- Flask
- Flask-Session
- Jinja2
- requests

## Instalación

1. Clona o descarga los archivos de este repositorio en tu computadora.

2. Instala las dependencias utilizando pip:

pip install Flask Flask-Session Jinja2 requests


## Configuración

Antes de ejecutar la aplicación, asegúrate de configurar los siguientes parámetros en el código:

- `base_url`: La URL del servicio REST de ArcGIS que proporciona los datos geoespaciales.
- `username`: Nombre de usuario para acceder al servicio REST de ArcGIS.
- `password`: Contraseña del usuario para acceder al servicio REST de ArcGIS.

## Ejecución

Para iniciar la aplicación, ejecuta el archivo `app.py` en la terminal:

python app.py

Una vez que la aplicación esté en ejecución, accede a ella en tu navegador web a través de la URL `http://localhost:5000/`.

## Uso

1. En la página de inicio, puedes seleccionar diferentes criterios de búsqueda, como departamento, municipio, vereda, organización, etc.

2. Haz clic en el botón "Buscar" para obtener los resultados que cumplan con los criterios de búsqueda seleccionados.

3. La aplicación mostrará una lista de resultados coincidentes en forma de enlaces. Haz clic en cualquiera de los enlaces para ver el informe detallado de esa entidad geoespacial.

4. Si deseas generar informes para todos los resultados, selecciona los criterios de búsqueda adecuados y haz clic en el botón "Generar Informes". Los informes se generarán en formato HTML y se empaquetarán en un archivo ZIP que se puede descargar haciendo clic en el enlace proporcionado.


## Notas

- La aplicación utiliza el módulo `requests` para realizar solicitudes HTTP al servicio REST de ArcGIS. Asegúrate de tener una conexión a Internet activa para utilizar la aplicación correctamente.

- Los informes generados en formato HTML se guardarán en un directorio temporal y se eliminarán una vez que se descarguen en un archivo ZIP. Si deseas conservar los informes individuales, asegúrate de moverlos a otra ubicación antes de generar nuevos informes.


