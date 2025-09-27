-- Crear tabla de usuarios
CREATE TABLE users (
id SERIAL PRIMARY KEY,
username VARCHAR(50) UNIQUE NOT NULL,
password VARCHAR(100) NOT NULL
);

-- Crear tabla de datos cifrados
CREATE TABLE data (
id SERIAL PRIMARY KEY,
username VARCHAR(50) NOT NULL,
data BYTEA NOT NULL,
FOREIGN KEY (username) REFERENCES
users (username)
);

-- Alteración del tipo de datos del campo `password` en `users`
ALTER TABLE users
ALTER COLUMN password SET DATA TYPE VARCHAR(256)