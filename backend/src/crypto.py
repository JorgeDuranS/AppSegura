from cryptography.fernet import Fernet
from pathlib import Path

def read_secret_key(filename: str) -> Fernet:
    """Creación de la llave Fernet

    Crea, si no existe, un archivo con la llave privada de encriptación y la 
    lee para entregarla.

    :filename: nombre del archivo con la llave privada.
    """

    secret_file = Path(filename)

    # Generar y guardar la clave de cifrado
    if not(secret_file.exists()):
        with secret_file.open('wb') as f:
            f.write(Fernet.generate_key())

    # Leer la clave de cifrado
    with secret_file.open('rb') as f:
        key = f.read()
        return Fernet(key)


def encrypt_data(plain_data: str, key: Fernet) -> str:
    """Encripta cadenas de texto

    :plain_data: Datos a encriptar como cadena de texto
    :key: Objeto Fernet para encriptar
    """

    return key.encrypt(plain_data.decode('utf-8'))


def decrypt_data(encrypted_data: str, key: Fernet) -> str:
    """Desencripta el contenido de la cadena de texto

    :encrypted_data: Cadena de texto encriptada
    :key: Objeto Fernet para desencriptar
    """

    return key.decrypt(encrypted_data).encode('utf-8')
