import os
import pickle
import subprocess
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Si modificas estos scopes, borra el archivo token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                scopes=SCOPES,
                redirect_uri='http://localhost'  # Usa el mismo redirect_uri que está en credentials.json
            )
            # Genera la URL de autorización y la imprime en la consola
            auth_url, _ = flow.authorization_url(prompt='consent')
            print('Por favor, visita la siguiente URL para autorizar la aplicación:')
            print(auth_url)
            print('\nDespués de autorizar, copia el código de autorización y péguelo aquí.')

            # Solicita el código de autorización manualmente
            auth_code = input('Ingresa el código de autorización: ')
            # Intercambia el código de autorización por un token de acceso
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            # Guarda las credenciales para futuras ejecuciones
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    return creds

def list_mp4_files(service):
    results = service.files().list(
        q="mimeType='video/mp4'",
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items

def get_unique_filename(download_path, file_name):
    # Verifica si el archivo ya existe
    full_path = os.path.join(download_path, file_name)
    if not os.path.exists(full_path):
        return full_path
    
    # Si existe, agrega un sufijo único
    base_name, ext = os.path.splitext(file_name)
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{ext}"
        new_path = os.path.join(download_path, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def download_file(service, file_id, file_name, download_path):
    # Obtiene un nombre de archivo único
    full_path = get_unique_filename(download_path, file_name)
    
    try:
        # Descarga el archivo
        request = service.files().get_media(fileId=file_id)
        with open(full_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")
        print(f"Archivo guardado en: {full_path}")
        return full_path
    except Exception as e:
        print(f"Error al descargar {file_name}: {e}")
        return None

def convert_to_480p(input_path, output_folder):
    # Crea la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta de conversión creada: {output_folder}")

    # Crea la ruta de salida para el video convertido
    file_name = os.path.basename(input_path)
    output_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + "_480p.mp4")
    
    # Comando de ffmpeg para convertir a 480p
    command = [
        'ffmpeg',
        '-i', input_path,          # Archivo de entrada
        '-vf', 'scale=854:480',   # Escala a 480p (854x480)
        '-c:a', 'copy',           # Copia el audio sin cambios
        output_path               # Archivo de salida
    ]
    
    # Ejecuta el comando
    try:
        subprocess.run(command, check=True)
        print(f"Video convertido a 480p: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error al convertir el video: {e}")
        return None

def delete_file(service, file_id):
    service.files().delete(fileId=file_id).execute()
    print(f"File {file_id} deleted.")

def main(download_path):
    # Verifica si la carpeta de descarga existe, si no, la crea
    if not os.path.exists(download_path):
        os.makedirs(download_path)
        print(f"Carpeta de descarga creada: {download_path}")

    # Carpeta para los videos convertidos
    converted_folder = os.path.join(download_path, "converted")

    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)

    mp4_files = list_mp4_files(service)
    if not mp4_files:
        print('No MP4 files found.')
    else:
        for item in mp4_files:
            file_id = item['id']
            file_name = item['name']
            print(f'Downloading {file_name}...')
            downloaded_path = download_file(service, file_id, file_name, download_path)
            if downloaded_path:
                print(f'{file_name} downloaded.')
                
                # Convertir el video a 480p
                converted_path = convert_to_480p(downloaded_path, converted_folder)
                if converted_path:
                    print(f'{file_name} convertido a 480p: {converted_path}')
                    
                    # Eliminar el video original después de la conversión
                    os.remove(downloaded_path)
                    print(f'Video original eliminado: {downloaded_path}')
                
                delete_file(service, file_id)
                print(f'{file_name} deleted from Google Drive.')
            else:
                print(f'Error: No se pudo descargar {file_name}.')

if __name__ == '__main__':
    # Especifica la carpeta de descarga
    download_folder = "downloads"  # Cambia esto por la ruta que desees
    main(download_folder)