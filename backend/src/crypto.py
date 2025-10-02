from cryptography.fernet import Fernet
from pathlib import Path
import os
import stat

def read_secret_key(filename: str) -> Fernet:
    """Creación de la llave Fernet

    Crea, si no existe, un archivo con la llave privada de encriptación y la 
    lee para entregarla. Implementa manejo seguro de archivos y permisos.

    :filename: nombre del archivo con la llave privada.
    :return: Objeto Fernet inicializado con la clave
    :raises: Exception si hay errores de archivo o permisos
    """
    try:
        secret_file = Path(filename)

        # Generar y guardar la clave de cifrado si no existe
        if not secret_file.exists():
            # Ensure parent directory exists
            secret_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate secure key with proper entropy
            key = Fernet.generate_key()
            
            try:
                with secret_file.open('wb') as f:
                    f.write(key)
                
                # Set restrictive permissions (owner read/write only)
                # This works on Unix-like systems
                if os.name != 'nt':  # Not Windows
                    os.chmod(secret_file, stat.S_IRUSR | stat.S_IWUSR)
                    
            except (OSError, IOError) as e:
                raise Exception(f"Failed to create secret key file: {str(e)}")

        # Validate file permissions before reading
        if os.name != 'nt':  # Not Windows
            file_stat = secret_file.stat()
            # Check if file is readable by others (security risk)
            if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
                raise Exception(f"Secret key file {filename} has insecure permissions")

        # Leer la clave de cifrado
        try:
            with secret_file.open('rb') as f:
                key = f.read()
                if len(key) == 0:
                    raise Exception("Secret key file is empty")
                return Fernet(key)
        except (OSError, IOError) as e:
            raise Exception(f"Failed to read secret key file: {str(e)}")
        except Exception as e:
            raise Exception(f"Invalid secret key format: {str(e)}")
            
    except Exception as e:
        raise Exception(f"Error in secret key management: {str(e)}")


def encrypt_data(plain_data: str, key: Fernet) -> bytes:
    """Encripta cadenas de texto

    :plain_data: Datos a encriptar como cadena de texto
    :key: Objeto Fernet para encriptar
    :return: Datos encriptados como bytes
    :raises: Exception si falla la encriptación
    """
    try:
        # Convert string to bytes before encryption
        data_bytes = plain_data.encode('utf-8')
        return key.encrypt(data_bytes)
    except Exception as e:
        raise Exception(f"Error during encryption: {str(e)}")


def decrypt_data(encrypted_data: bytes, key: Fernet) -> str:
    """Desencripta el contenido de la cadena de texto

    :encrypted_data: Datos encriptados como bytes
    :key: Objeto Fernet para desencriptar
    :return: Datos desencriptados como string
    :raises: Exception si falla la desencriptación
    """
    try:
        # Decrypt returns bytes, decode to string
        decrypted_bytes = key.decrypt(encrypted_data)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise Exception(f"Error during decryption: {str(e)}")
