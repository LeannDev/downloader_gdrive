import os
import subprocess
from decouple import config, Csv
from datetime import datetime
from pydrive2.drive import GoogleDrive
from auth import authenticate_headless, complete_authentication

def main():
    # 1. Autenticación y conexión a Google Drive usando funciones de auth.py
    # 1. Autenticación y conexión a Google Drive usando funciones de auth.py
    gauth, _ = authenticate_headless()  # Ya no necesitamos auth_url ni auth_code
    drive = GoogleDrive(gauth)

    # 2. Especifica la ID de la carpeta en Google Drive que contiene los videos (raíz en este caso)
    folder_id = 'root'

    # 3. Define la ruta local donde se descargarán los videos
    today = datetime.today()
    download_folder = 'videos/downloads'
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # 4. Define la ruta para guardar los videos convertidos a 480p
    videos_480p_folder = today.strftime("%Y/%m/%d")
    if not os.path.exists(videos_480p_folder):
        os.makedirs(videos_480p_folder)

    # 5. Lista los archivos en la carpeta de Drive (en la raíz)
    file_list = drive.ListFile({
        'q': f"'{folder_id}' in parents and trashed=false"
    }).GetList()

    # 6. Procesa cada archivo: descarga, convierte a 480p y elimina el archivo original localmente
    for file in file_list:
        file_title = file['title']
        
        # Verifica que el archivo sea .mp4
        if not file_title.lower().endswith('.mp4'):
            print(f"Saltando {file_title} (no es un archivo .mp4)")
            continue

        # Prepara el nombre y la ruta para el video convertido
        name, ext = os.path.splitext(file_title)
        converted_file_name = f"{name}_480p{ext}"
        converted_path = os.path.join(videos_480p_folder, converted_file_name)

        # Si ya existe el video convertido, se salta el procesamiento
        if os.path.exists(converted_path):
            print(f"Saltando {file_title} porque {converted_path} ya existe.")
            continue

        print(f"Procesando: {file_title}")
        local_path = os.path.join(download_folder, file_title)
        
        try:
            # Descarga el archivo a la carpeta de descargas
            file.GetContentFile(local_path)
            if os.path.exists(local_path):
                print(f"Descargado: {local_path}")
                
                # Ejecuta ffmpeg para convertir el video a 480p, manteniendo la relación de aspecto
                command = [
                    'ffmpeg', '-i', local_path,
                    '-vf', 'scale=-2:480',
                    '-c:a', 'copy',
                    converted_path
                ]
                print(f"Convirtiendo {file_title} a 480p...")
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if result.returncode == 0:
                    print(f"Conversión exitosa: {converted_path}")
                    
                    # Elimina el archivo original descargado de la carpeta local
                    try:
                        os.remove(local_path)
                        print(f"Eliminado del directorio local: {local_path}")
                    except Exception as e:
                        print(f"Error al eliminar el archivo local {local_path}: {e}")
                    
                    # Si se requiere eliminar también de Google Drive, se puede descomentar:
                    #try:
                    #    file.Delete()
                    #    print(f"Eliminado de Google Drive: {file_title}")
                    #except Exception as e:
                    #    print(f"Error al eliminar de Drive {file_title}: {e}")
                else:
                    error_message = result.stderr.decode()
                    print(f"Error en la conversión de {file_title}: {error_message}")
            else:
                print(f"Error: El archivo {file_title} no se descargó correctamente.")
        except Exception as e:
            print(f"Excepción al procesar {file_title}: {str(e)}")

if __name__ == "__main__":
    main()
