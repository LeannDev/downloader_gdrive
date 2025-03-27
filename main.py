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

# Ruta base absoluta (donde está ubicado este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas absolutas
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.pickle')
DOWNLOADS_PATH = os.path.join(BASE_DIR, 'downloads', 'videos')
CONVERTED_PATH = os.path.join(BASE_DIR, 'downloads', 'converted')
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'gdrive.log')

# delete files
DELETE_DOWNLOADED_VIDEOS = True  # local files
DELETE_DRIVE_VIDEOS = True       # drive files

# Log de ejecución
try:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as log:
        log.write(">>> Script iniciado desde cron\n")
except Exception as e:
    print(f"Error al escribir en el log: {e}")

def authenticate_google_drive():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                scopes=SCOPES,
                redirect_uri='http://localhost'
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            print('Por favor, visita la siguiente URL para autorizar la aplicación:')
            print(auth_url)
            print('\nDespués de autorizar, copia el código de autorización y péguelo aquí.')
            auth_code = input('Ingresa el código de autorización: ')
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
    return creds

def list_mp4_files(service):
    results = service.files().list(
        q="mimeType='video/mp4'",
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    return results.get('files', [])

def get_unique_filename(download_path, file_name):
    full_path = os.path.join(download_path, file_name)
    if not os.path.exists(full_path):
        return full_path
    base_name, ext = os.path.splitext(file_name)
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{ext}"
        new_path = os.path.join(download_path, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def download_file(service, file_id, file_name, download_path):
    full_path = get_unique_filename(download_path, file_name)
    try:
        request = service.files().get_media(fileId=file_id)
        with open(full_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")
        print(f"Archivo guardado en: {full_path}")
        return full_path
    except Exception as e:
        print(f"Error al descargar {file_name}: {e}")
        return None

def convert_to_480p(input_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta de conversión creada: {output_folder}")
    file_name = os.path.basename(input_path)
    output_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + "_480p.mp4")
    command = [
        'ffmpeg',
        '-i', input_path,
        '-vf', 'scale=854:480',
        '-c:a', 'copy',
        output_path
    ]
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

def main(download_path, converted_path):
    os.makedirs(download_path, exist_ok=True)
    os.makedirs(converted_path, exist_ok=True)
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
                converted_path_output = convert_to_480p(downloaded_path, converted_path)
                if converted_path_output:
                    print(f'{file_name} convertido a 480p: {converted_path_output}')
                    if DELETE_DOWNLOADED_VIDEOS:
                        os.remove(downloaded_path)
                        print(f'Video original eliminado: {downloaded_path}')
                if DELETE_DRIVE_VIDEOS:
                    delete_file(service, file_id)
                    print(f'{file_name} deleted from Google Drive.')
            else:
                print(f'Error: No se pudo descargar {file_name}.')

if __name__ == '__main__':
    main(DOWNLOADS_PATH, CONVERTED_PATH)