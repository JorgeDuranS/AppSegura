import json
import os
import psycopg2

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import (
    generate_password_hash as generate_phash,
    check_password_hash as check_phash
)

from crypto import (
    read_secret_key,
    encrypt_data,
    decrypt_data
)


# Carga de configuraciones a partir del archivo de variables de entorno
config = {
    **dotenv_values('.env'),
    **os.environ
}


# Declaración de la aplicación Flask
app = Flask(__name__,
    template_folder = config['TEMPLATE_FOLDER'],
    static_folder = config['STATIC_FOLDER'],
    static_url_path = '/static/',
)

app.secret_key = 'super_secret_key'


fernet_key = read_secret_key(config['SECRET_KEY_FILE'])

# Conectar a la base de datos PostgreSQL
conn = psycopg2.connect(
    dbname=config['POSTGRES_DB_NAME'],
    user=config['POSTGRES_USER'],
    password=config['POSTGRES_PASSWORD'],
    host=config['POSTGRES_DB_HOST']
)


@app.route('/', methods=['GET'])
def index():
    return render_template('html/index.html')


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
    
    user_phash = cur.fetchone()
    
    if user_phash and check_phash(user_phash[0], password):
        session['username'] = username
        return "Inicio de sesión exitoso"


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

    return "Credenciales incorrectas"


@app.route('/data', methods=['GET', 'POST'])
def save_data():
    
    if 'username' in session:
        username = session['username']

        if request.method == 'GET':
            cur = conn.cursor()
            cur.execute('''
                SELECT data
                FROM data
                WHERE username=%s
                ''', (username,)
            )

        
            data = decrypt_data(cur.fetchone()[0])

            return data

        if reqest.method == 'POST':

            data = request.form['data']
            encrypted_data = encrypt_data(data, fernet_key)

            cur = conn.cursor()
            cur.execute('''
                INSERT INTO data (username, data)
                VALUES (%s, %s)
                ''', (username, encrypted_data)
            )
    
            conn.commit()

            return "Datos guardados con éxito"

        return "El usuario no tiene datos guardados"
    
    return "Usuario no autenticado"


if __name__ == '__main__':
    app.run(debug=True)