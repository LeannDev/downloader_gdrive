import os
import pickle
import subprocess
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Ruta base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'gdrive.log')

DELETE_DOWNLOADED_VIDEOS = True
DELETE_DRIVE_VIDEOS = True

def authenticate_google_drive(account_id):
    creds = None
    token_path = os.path.join(BASE_DIR, f'token_{account_id}.pickle')
    credentials_path = os.path.join(BASE_DIR, f'credentials_{account_id}.json')

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                scopes=SCOPES,
                redirect_uri='http://localhost'
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'[Cuenta {account_id}] Visita esta URL para autorizar:')
            print(auth_url)
            auth_code = input('Pega el código de autorización aquí: ')
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
    return creds

def get_dynamic_paths(account_id, date_ref):
    year = str(date_ref.year)
    month = f"{date_ref.month:02d}"
    day = f"{date_ref.day:02d}"

    videos_path = os.path.join(BASE_DIR, 'downloads', 'videos', account_id, year, month, day)
    converted_path = os.path.join(BASE_DIR, 'downloads', 'converted', account_id, year, month, day)

    os.makedirs(videos_path, exist_ok=True)
    os.makedirs(converted_path, exist_ok=True)

    return videos_path, converted_path

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
    print(f"Archivo {file_id} eliminado de Google Drive.")

def process_account(account_id):
    print(f"\n=== Procesando cuenta: {account_id} ===")
    
    # Fijar la fecha UNA SOLA VEZ por cuenta
    now = datetime.now()
    downloads_path, converted_path = get_dynamic_paths(account_id, now)

    creds = authenticate_google_drive(account_id)
    service = build('drive', 'v3', credentials=creds)

    mp4_files = list_mp4_files(service)
    if not mp4_files:
        print('No se encontraron archivos MP4.')
        return

    for item in mp4_files:
        file_id = item['id']
        file_name = item['name']
        print(f'Descargando {file_name}...')
        downloaded_path = download_file(service, file_id, file_name, downloads_path)
        if downloaded_path:
            converted = convert_to_480p(downloaded_path, converted_path)
            if converted and DELETE_DOWNLOADED_VIDEOS:
                os.remove(downloaded_path)
            if DELETE_DRIVE_VIDEOS:
                delete_file(service, file_id)

def main():
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as log:
            log.write(">>> Script iniciado\n")
    except Exception as e:
        print(f"Error al escribir en el log: {e}")

    # Lista de cuentas
    cuentas = [
        'ciifa.faa@gmail.com',
        'leanenueva@gmail.com',
        # Agrega más cuentas aquí
    ]

    for cuenta in cuentas:
        try:
            process_account(cuenta)
        except Exception as e:
            print(f"Error procesando {cuenta}: {e}")

if __name__ == '__main__':
    main()

