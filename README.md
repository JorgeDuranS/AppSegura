# Aplicación Web Segura

Una aplicación web segura desarrollada durante el bootcamp de Talento Tech Ciberseguridad Intermedio. Esta aplicación permite a los usuarios registrarse, iniciar sesión y almacenar datos de forma segura utilizando encriptación.

## 🚀 Características

- **Autenticación segura**: Sistema de registro e inicio de sesión con hash de contraseñas
- **Encriptación de datos**: Todos los datos del usuario se almacenan encriptados usando Fernet (AES 128)
- **Base de datos SQLite**: Base de datos local sin dependencias externas
- **Interfaz moderna**: UI responsive con Tailwind CSS
- **Protección CSRF**: Tokens de seguridad para prevenir ataques CSRF
- **Rate limiting**: Protección contra ataques de fuerza bruta
- **Validación de entrada**: Sanitización y validación de todos los datos de entrada
- **Logging de seguridad**: Registro de eventos de seguridad importantes
- **Headers de seguridad**: Configuración de headers HTTP seguros

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Sistema operativo: Windows, macOS, o Linux

## 🛠️ Instalación

### Instalación Rápida (5 minutos)

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/JorgeDuranS/AppSegura.git
   cd AppSegura
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # En Windows:
   venv/Scripts/activate
   
   # En macOS/Linux:
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   # Método recomendado (con inicialización automática)
   python start_app.py
   
   # O método tradicional
   python backend/src/app.py
   ```

## 🔧 Solución de Problemas

### Error de Clave de Encriptación

Si encuentras errores relacionados con `Fernet key must be 32 url-safe base64-encoded bytes`, ejecuta:

```bash
# Inicializar componentes manualmente
python backend/src/init_app.py

# Luego ejecutar la aplicación
python backend/src/app.py
   python backend/src/app.py
   ```

5. **Abrir en el navegador**
   ```
   http://127.0.0.1:5000
   ```

¡Listo! La aplicación estará funcionando en menos de 5 minutos.

### Configuración Adicional (Opcional)

La aplicación funciona con configuración por defecto, pero puedes personalizar algunos aspectos:

1. **Crear archivo de configuración** (opcional)
   ```bash
   cp .env.example backend/src/.env
   ```

2. **Editar configuración** en `backend/src/.env`:
   ```env
   SESSION_TIMEOUT=3600
   MAX_LOGIN_ATTEMPTS=5
   LOGIN_ATTEMPT_WINDOW=900
   ```

## 🏗️ Estructura del Proyecto

```
webapp-segura/
├── backend/
│   ├── src/
│   │   ├── app.py              # Aplicación Flask principal
│   │   ├── config.py           # Configuración de la aplicación
│   │   ├── crypto.py           # Funciones de encriptación
│   │   ├── database.py         # Operaciones de base de datos
│   │   └── validation.py       # Validación de entrada
│   ├── .secret.key            # Clave secreta (generada automáticamente)
│   └── app.db                 # Base de datos SQLite (creada automáticamente)
├── frontend/
│   ├── templates/             # Plantillas HTML
│   └── static/               # Archivos estáticos (CSS, JS)
├── requirements.txt          # Dependencias Python
└── README.md                # Este archivo
```

## 🔌 API Endpoints

### Autenticación

#### POST /login
Iniciar sesión de usuario.

**Parámetros:**
- `username` (string): Nombre de usuario (3-50 caracteres, alfanumérico)
- `password` (string): Contraseña del usuario
- `csrf_token` (string): Token CSRF

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "message": "Inicio de sesión exitoso",
  "redirect": "/data"
}
```

**Errores:**
- `400`: Datos inválidos o token CSRF inválido
- `401`: Credenciales incorrectas
- `429`: Demasiados intentos de inicio de sesión

#### POST /register
Registrar nuevo usuario.

**Parámetros:**
- `username` (string): Nombre de usuario único (3-50 caracteres)
- `password` (string): Contraseña (mínimo 8 caracteres, debe incluir mayúsculas, minúsculas y números)
- `confirm-password` (string): Confirmación de contraseña
- `terms` (string): Aceptación de términos ("on")
- `csrf_token` (string): Token CSRF

**Respuesta exitosa (201):**
```json
{
  "success": true,
  "message": "Usuario registrado con éxito",
  "redirect": "/login"
}
```

**Errores:**
- `400`: Datos inválidos
- `409`: Usuario ya existe

#### POST /logout
Cerrar sesión de usuario.

**Parámetros:**
- `csrf_token` (string): Token CSRF (opcional para GET)

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "message": "Sesión cerrada correctamente",
  "redirect": "/"
}
```

### Gestión de Datos

#### GET /api/data
Obtener datos del usuario autenticado.

**Headers requeridos:**
- Cookie de sesión válida

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "data": "datos del usuario desencriptados"
}
```

**Sin datos (200):**
```json
{
  "success": true,
  "data": null,
  "message": "El usuario no tiene datos guardados"
}
```

**Errores:**
- `401`: Usuario no autenticado

#### POST /api/data
Guardar datos del usuario autenticado.

**Parámetros:**
- `data` (string): Datos a guardar (máximo 10,000 caracteres)
- `csrf_token` (string): Token CSRF

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "message": "Datos guardados con éxito"
}
```

**Errores:**
- `400`: Datos inválidos o token CSRF inválido
- `401`: Usuario no autenticado

### Páginas Web

- `GET /` - Página principal (redirige a /data si está autenticado)
- `GET /login` - Página de inicio de sesión
- `GET /register` - Página de registro
- `GET /data` - Página de gestión de datos (requiere autenticación)

## 🔒 Seguridad

### Características de Seguridad Implementadas

1. **Encriptación de datos**: Fernet (AES 128) para datos sensibles
2. **Hash de contraseñas**: Werkzeug PBKDF2 con salt
3. **Protección CSRF**: Tokens únicos por sesión
4. **Rate limiting**: Máximo 5 intentos de login por IP cada 15 minutos
5. **Validación de entrada**: Sanitización de todos los inputs
6. **Headers de seguridad**: X-Frame-Options, CSP, etc.
7. **Gestión segura de sesiones**: Cookies HTTPOnly, SameSite
8. **Logging de seguridad**: Registro de eventos importantes

### Configuración de Seguridad

- **Timeout de sesión**: 1 hora por defecto
- **Longitud mínima de contraseña**: 8 caracteres
- **Requisitos de contraseña**: Mayúsculas, minúsculas, números
- **Longitud máxima de datos**: 10,000 caracteres

## 🧪 Uso de la Aplicación

### 1. Registro de Usuario
1. Navega a `/register`
2. Completa el formulario con:
   - Nombre de usuario (3-50 caracteres alfanuméricos)
   - Contraseña segura (mínimo 8 caracteres)
   - Confirmación de contraseña
   - Aceptación de términos
3. Haz clic en "Registrarse"

### 2. Inicio de Sesión
1. Navega a `/login`
2. Ingresa tu nombre de usuario y contraseña
3. Haz clic en "Iniciar Sesión"

### 3. Gestión de Datos
1. Una vez autenticado, serás redirigido a `/data`
2. Puedes:
   - Ver tus datos guardados
   - Editar y guardar nuevos datos
   - Los datos se encriptan automáticamente

### 4. Cerrar Sesión
1. Haz clic en "Cerrar Sesión" en cualquier página
2. Serás redirigido a la página principal

## 🐛 Solución de Problemas

### Problemas Comunes

#### Error: "No se puede conectar a la base de datos"
**Solución:**
1. Verifica que el directorio `backend/` tenga permisos de escritura
2. La base de datos se crea automáticamente en el primer inicio

#### Error: "Token CSRF inválido"
**Solución:**
1. Recarga la página para obtener un nuevo token
2. Asegúrate de que las cookies estén habilitadas

#### Error: "Demasiados intentos de inicio de sesión"
**Solución:**
1. Espera 15 minutos antes de intentar nuevamente
2. Verifica que estés usando las credenciales correctas

#### Error: "Error interno del servidor"
**Solución:**
1. Revisa los logs en la consola donde ejecutas la aplicación
2. Verifica que todas las dependencias estén instaladas correctamente
3. Asegúrate de estar usando Python 3.8 o superior

#### La aplicación no inicia
**Solución:**
1. Verifica que el entorno virtual esté activado
2. Reinstala las dependencias: `pip install -r requirements.txt`
3. Verifica que el puerto 5000 no esté en uso

#### Problemas de permisos en Windows
**Solución:**
1. Ejecuta la terminal como administrador
2. O cambia los permisos de la carpeta del proyecto

### Logs y Debugging

Los logs de la aplicación se muestran en la consola. Para más información:

1. **Logs de seguridad**: Se registran intentos de login, errores CSRF, etc.
2. **Logs de base de datos**: Errores de conexión y operaciones
3. **Logs de aplicación**: Errores generales y eventos importantes

### Verificación de Instalación

Para verificar que todo funciona correctamente:

1. **Verificar dependencias:**
   ```bash
   pip list
   ```

2. **Verificar base de datos:**
   - Debe crearse automáticamente en `backend/app.db`

3. **Verificar clave secreta:**
   - Debe crearse automáticamente en `backend/.secret.key`

4. **Probar endpoints:**
   - Navega a `http://127.0.0.1:5000`
   - Registra un usuario de prueba
   - Inicia sesión y guarda algunos datos

## 📞 Soporte

Si encuentras problemas no cubiertos en esta documentación:

1. Revisa los logs de la aplicación en la consola
2. Verifica que cumples con todos los requisitos del sistema
3. Asegúrate de seguir exactamente los pasos de instalación
4. Consulta la documentación de desarrollo para más detalles técnicos

## 📄 Licencia

Este proyecto está licenciado bajo los términos especificados en el archivo LICENSE.
