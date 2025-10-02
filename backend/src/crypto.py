from cryptography.fernet import Fernet
from pathlib import Path
import os
import stat

def read_secret_key(filename: str) -> Fernet:
    """Creación de la llave Fernet

    Crea, si no existe, un archivo con la llave privada de encriptación y la 
    lee para entregarla. Implementa manejo seguro de archivos y permisos.
    Incluye validación y recuperación automática de archivos corruptos.

    :filename: nombre del archivo con la llave privada.
    :return: Objeto Fernet inicializado con la clave
    :raises: Exception si hay errores de archivo o permisos
    """
    secret_file = Path(filename)
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            # Ensure parent directory exists
            secret_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and is valid
            key_needs_creation = True
            
            if secret_file.exists():
                try:
                    # Try to read and validate existing key
                    with secret_file.open('rb') as f:
                        existing_key = f.read()
                    
                    # Validate key format and length
                    if len(existing_key) > 0:
                        # Test if it's a valid Fernet key
                        test_fernet = Fernet(existing_key)
                        # Test encryption/decryption to ensure key works
                        test_data = b"test"
                        encrypted = test_fernet.encrypt(test_data)
                        decrypted = test_fernet.decrypt(encrypted)
                        
                        if decrypted == test_data:
                            key_needs_creation = False
                            print(f"INFO: Using existing valid secret key from {filename}")
                            return test_fernet
                        
                except Exception as e:
                    print(f"WARNING: Existing key file is invalid ({str(e)}), will recreate")
                    key_needs_creation = True
            
            # Create new key if needed
            if key_needs_creation:
                print(f"INFO: Creating new secret key at {filename}")
                
                # Remove corrupted file if it exists
                if secret_file.exists():
                    try:
                        secret_file.unlink()
                    except Exception as e:
                        print(f"WARNING: Could not remove corrupted key file: {e}")
                
                # Generate new secure key
                new_key = Fernet.generate_key()
                
                # Write key to file with proper error handling
                try:
                    with secret_file.open('wb') as f:
                        f.write(new_key)
                        f.flush()  # Ensure data is written to disk
                        os.fsync(f.fileno())  # Force write to disk
                    
                    # Set restrictive permissions (Unix/Linux only)
                    if os.name != 'nt':  # Not Windows
                        os.chmod(secret_file, stat.S_IRUSR | stat.S_IWUSR)
                    
                    # Verify the file was written correctly
                    with secret_file.open('rb') as f:
                        verify_key = f.read()
                    
                    if verify_key != new_key:
                        raise Exception("Key verification failed after writing")
                    
                    print(f"SUCCESS: Secret key created and verified at {filename}")
                    return Fernet(new_key)
                    
                except (OSError, IOError) as e:
                    if attempt < max_attempts - 1:
                        print(f"RETRY: Failed to create key file (attempt {attempt + 1}): {e}")
                        continue
                    else:
                        raise Exception(f"Failed to create secret key file after {max_attempts} attempts: {str(e)}")
                        
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"RETRY: Key management error (attempt {attempt + 1}): {e}")
                continue
            else:
                raise Exception(f"Error in secret key management after {max_attempts} attempts: {str(e)}")
    
    # This should never be reached, but just in case
    raise Exception("Unexpected error in key management")


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
