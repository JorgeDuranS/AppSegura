import json
import psycopg2

from cryptography.fernet import Fernet
from flask import Flask, request, jsonify, session
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'

secret_file_name = 'secret.key'
secret_file = Path(secret_file_name)

# Generar y guardar la clave de cifrado
if not(secret_file.exists()):
    key = Fernet.generate_key()
    with open(secret_file_name, 'wb') as key_file:
        key_file.write(key)

# Leer la clave de cifrado
with open(secret_file_name, 'rb') as key_file:
    key = key_file.read()
    f = Fernet(key)

# Conectar a la base de datos PostgreSQL
conn = psycopg2.connect(
    dbname='app',
    user='app',
    password='s3Cur3P4ssW0rD',
    host='localhost'
)

# Diccionario ficticio de usuarios
users = {
    'admin': generate_password_hash('password')
}


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    password_hash = generate_password_hash(password)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (username, password)
        VALUES (%s, %s)
    ''', (username, password_hash)
    )
    conn.commit()
    return "Usuario registrado con éxito"


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    cur = conn.cursor()
    cur.execute('''
        SELECT password
        FROM users
        WHERE username=%s
    ''', (username,)
    )
    
    user_password_hash = cur.fetchone()
    
    if user_password_hash and check_password_hash(user_password_hash[0],password):
        session['username'] = username
        return "Inicio de sesión exitoso"

    return "Credenciales incorrectas"


@app.route('/data', methods=['POST'])
def save_data():
    if 'username' in session:
        data = request.form['data']
        encrypted_data = f.encrypt(data.encode())
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO data (username, data)
            VALUES (%s, %s)
        ''', (session['username'], encrypted_data)
        )
    
        conn.commit()

        return "Datos guardados con éxito"
    
    return "Usuario no autenticado"


if __name__ == '__main__':
    app.run(debug=True)