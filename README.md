# Proyecto de Conversión de Videos desde Google Drive a 480p

Este proyecto automatiza la descarga de videos almacenados en una carpeta de Google Drive, la conversión de dichos videos a calidad 480p utilizando **ffmpeg** y la eliminación de los videos originales tanto de Google Drive como del directorio local de descargas. Los videos convertidos se guardan en una carpeta separada denominada **videos_480p**.

## Requisitos

- **Python 3.x**
- **PyDrive2**: Para la autenticación y manipulación de archivos en Google Drive.
- **ffmpeg**: Herramienta de línea de comandos para la conversión de video.
- **Credenciales OAuth 2.0**: Se necesita un archivo `client_secrets.json` configurado con las credenciales adecuadas desde Google Cloud Platform.

## Configuración de Credenciales OAuth 2.0

Para obtener las credenciales necesarias:

1. Accede a [Google Cloud Platform Console](https://console.cloud.google.com/).
2. Crea un nuevo proyecto o selecciona uno existente.
3. Habilita la **API de Google Drive** para tu proyecto.
4. En la sección de **Credenciales**, crea una nueva credencial OAuth 2.0 de tipo **Escritorio**.

> Si usas **Aplicación web**, en la configuración de la credencial, añade lo siguiente:
   - **Orígenes autorizados de JavaScript**:  
     - `http://localhost:8080` *(sin la barra "/" al final)*
   - **URI de redireccionamiento autorizados**:  
     - `http://localhost:8080/` *(con la barra "/" al final)*

> **Importante:**  
> Es crucial incluir la barra "/" al final del URI de redireccionamiento, ya que omitirla provocará un error en el proceso de autenticación.

Una vez configurado, descarga el archivo, renombralo `credentials.json` y colócalo en el directorio del proyecto.

## ¿Qué Hace el Código?

El script principal realiza los siguientes pasos:

1. **Autenticación en Google Drive:**  
   Se utiliza el archivo `credentials.json` para autenticar y acceder a la cuenta de Google Drive.

2. **Descarga de Videos:**  
   Accede a Google Drive y descarga todos los videos a un directorio local configurado.

3. **Conversión de Video:**  
   Utiliza **ffmpeg** para convertir cada video a calidad 480p manteniendo la relación de aspecto original. Los videos convertidos se guardan en la carpeta `videos_480p`.

4. **Eliminación de Archivos Originales:**  
   Si la conversión es exitosa, el script elimina el archivo original tanto de Google Drive como del directorio local de descargas.

## Uso

1. **Instalación de Dependencias:**  
   Asegúrate de tener instalados los siguientes paquetes:
```bash
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 requests
   pip install python-decouple
```

Además, instala **ffmpeg** y asegúrate de que esté en el PATH del sistema.

## Configuración del Proyecto:

- Coloca el archivo `credentials.json` en el directorio del proyecto.
- Edita el script para configurar:
- DOWNLOADS_PATH y CONVERTED_PATH

## Ejecución:

Ejecuta el script principal:

```bash
    python main.py
```

Se imprimira en consola un link para copiar en un navegador y autenticar. Esto devolvera una url con distintos parametros. Copia el parametro "code" y pegalo en la terminal

## Estructura del Proyecto

- main.py: Script principal que contiene la lógica para la descarga, conversión y eliminación de videos.
- credentials.json: Archivo de credenciales obtenido desde Google Cloud Platform.
- Carpetas locales:
    - `DOWNLOADS_PATH`: Carpeta donde se almacenan temporalmente los videos descargados.
    - `CONVERTED_PATH`: Carpeta donde se guardan los videos convertidos a 480p.