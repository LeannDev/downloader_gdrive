import os
import subprocess
from decouple import config, Csv
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def main():
    # 1. Autenticación y conexión a Google Drive
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Abre el navegador para autenticarte
    drive = GoogleDrive(gauth)

    # 2. Especifica la ID de la carpeta en Google Drive que contiene los videos
    folder_id = config('FOLDER_ID')  # Reemplaza con el ID real de tu carpeta

    # 3. Define la ruta local donde se descargarán los videos
    download_folder = 'videos/downloads'
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # 4. Define la ruta para guardar los videos convertidos a 480p
    videos_480p_folder = 'videos/convert_480p'
    if not os.path.exists(videos_480p_folder):
        os.makedirs(videos_480p_folder)

    # 5. Lista los archivos en la carpeta de Drive
    file_list = drive.ListFile({
        'q': f"'{folder_id}' in parents and trashed=false"
    }).GetList()

    # 6. Procesa cada archivo: descarga, convierte, elimina de Drive y elimina el original local
    for file in file_list:
        file_title = file['title']
        print(f"Procesando: {file_title}")
        local_path = os.path.join(download_folder, file_title)

        try:
            # Descarga el archivo a la carpeta de descargas
            file.GetContentFile(local_path)
            if os.path.exists(local_path):
                print(f"Descargado: {local_path}")

                # Prepara el nombre y la ruta para el video convertido
                name, ext = os.path.splitext(file_title)
                converted_file_name = f"{name}_480p{ext}"
                converted_path = os.path.join(videos_480p_folder, converted_file_name)

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

                    # Elimina el archivo original descargado de la carpeta de descargas locales
                    try:
                        os.remove(local_path)
                        print(f"Eliminado del directorio local: {local_path}")
                    except Exception as e:
                        print(f"Error al eliminar el archivo local {local_path}: {e}")

                    # Elimina el archivo original de Google Drive
                    try:
                        file.Delete()
                        print(f"Eliminado de Google Drive: {file_title}")
                    except Exception as e:
                        print(f"Error al eliminar de Drive {file_title}: {e}")
                else:
                    error_message = result.stderr.decode()
                    print(f"Error en la conversión de {file_title}: {error_message}")
            else:
                print(f"Error: El archivo {file_title} no se descargó correctamente.")
        except Exception as e:
            print(f"Excepción al procesar {file_title}: {str(e)}")

if __name__ == "__main__":
    main()