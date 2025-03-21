from pydrive2.auth import GoogleAuth
import os

def authenticate_headless(credentials_file="mycreds.txt"):
    gauth = GoogleAuth()

    # Cargar configuración desde settings.yaml automáticamente
    gauth.LoadClientConfigFile("settings.yaml")

    # Cargar credenciales guardadas si existen
    if os.path.exists(credentials_file):
        gauth.LoadCredentialsFile(credentials_file)

    # Si no hay credenciales o han expirado, autenticación manual (solo la primera vez)
    if gauth.credentials is None or gauth.access_token_expired:
        gauth.CommandLineAuth()  # Genera una URL para autenticarse manualmente la primera vez
        gauth.SaveCredentialsFile(credentials_file)  # Guarda credenciales
        return gauth, None

    return gauth, None

def complete_authentication(gauth, auth_code, credentials_file="mycreds.txt"):
    try:
        gauth.Auth(auth_code)  # Verifica el código de autenticación
        gauth.SaveCredentialsFile(credentials_file)
        return gauth
    except Exception as e:
        print(f"Error al autenticar: {e}")
        return None
