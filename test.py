from auth import authenticate_headless, complete_authentication

# Intenta autenticarse en modo headless
gauth, auth_url = authenticate_headless()

if auth_url:
    # Aquí enviarías la URL por email, log o notificación
    print("Por favor, autoriza la aplicación visitando la siguiente URL:")
    print(auth_url)
    # Luego, una vez que recibas el código de autorización, completarlo:
    auth_code = input("Introduce el código de autorización: ")
    gauth = complete_authentication(gauth, auth_code)
else:
    print("Credenciales cargadas correctamente, autenticación completada.")
