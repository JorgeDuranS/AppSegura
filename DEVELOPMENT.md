# Guía de Desarrollo

Esta guía proporciona información detallada para desarrolladores que deseen contribuir o modificar la aplicación web segura.

## 🏗️ Configuración del Entorno de Desarrollo

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git

### Configuración Inicial

1. **Clonar y configurar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd webapp-segura
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # Activar entorno virtual
   # Windows:
   venv\Scripts\activate
   
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Instalar dependencias de desarrollo**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8  # Herramientas de desarrollo
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example backend/src/.env
   ```

5. **Inicializar base de datos de desarrollo**
   ```bash
   python backend/src/app.py
   # La base de datos se crea automáticamente en el primer inicio
   ```

## 🏛️ Arquitectura de la Aplicación

### Estructura de Directorios

```
webapp-segura/
├── backend/                    # Lógica del servidor
│   ├── src/
│   │   ├── app.py             # Aplicación Flask principal
│   │   ├── config.py          # Configuración centralizada
│   │   ├── crypto.py          # Funciones de encriptación
│   │   ├── database.py        # Capa de acceso a datos
│   │   └── validation.py      # Validación y sanitización
│   ├── .secret.key           # Clave de encriptación (auto-generada)
│   └── app.db                # Base de datos SQLite
├── frontend/                  # Interfaz de usuario
│   ├── templates/            # Plantillas Jinja2
│   │   ├── base.html         # Plantilla base
│   │   ├── login.html        # Página de login
│   │   ├── register.html     # Página de registro
│   │   └── data.html         # Página de datos
│   └── static/               # Archivos estáticos
├── database/                 # Scripts de base de datos
│   ├── sqlite_schema.sql     # Schema SQLite
│   └── migrate_to_sqlite.py  # Script de migración
└── docs/                     # Documentación adicional
```

### Componentes Principales

#### 1. Aplicación Flask (app.py)
- **Rutas de autenticación**: `/login`, `/register`, `/logout`
- **Rutas de datos**: `/api/data` (GET/POST)
- **Rutas de páginas**: `/`, `/data`
- **Middleware de seguridad**: Headers, CSRF, rate limiting

#### 2. Capa de Base de Datos (database.py)
- **Conexiones**: Context managers para SQLite
- **Operaciones CRUD**: Usuarios y datos
- **Manejo de errores**: Excepciones personalizadas

#### 3. Criptografía (crypto.py)
- **Encriptación**: Fernet (AES 128)
- **Gestión de claves**: Generación y lectura segura
- **Validación**: Verificación de integridad

#### 4. Validación (validation.py)
- **Sanitización**: Limpieza de entrada
- **Validación**: Formatos y longitudes
- **Seguridad**: Prevención de inyecciones

## 🔧 Configuración de Desarrollo

### Variables de Entorno

Crea un archivo `.env` en `backend/src/` con:

```env
# Configuración de desarrollo
DEBUG=True
TESTING=False

# Configuración de sesión
SESSION_TIMEOUT=3600
SESSION_COOKIE_NAME=dev_session

# Configuración de seguridad
MAX_LOGIN_ATTEMPTS=5
LOGIN_ATTEMPT_WINDOW=900

# Rutas de archivos
TEMPLATE_FOLDER=../../frontend/templates
STATIC_FOLDER=../../frontend/static
```

### Configuración de Base de Datos

La aplicación usa SQLite por defecto. Para desarrollo:

1. **Base de datos de desarrollo**: `backend/app.db`
2. **Base de datos de pruebas**: Se crea en memoria durante tests
3. **Schema**: Definido en `database/sqlite_schema.sql`

### Modo Debug

Para habilitar el modo debug:

```python
# En config.py
self.DEBUG = True
```

Esto habilita:
- Recarga automática de código
- Mensajes de error detallados
- Deshabilitación de algunas restricciones de seguridad

## 🧪 Testing

### Estructura de Tests

```
tests/
├── test_app.py           # Tests de rutas y endpoints
├── test_database.py      # Tests de operaciones de BD
├── test_crypto.py        # Tests de encriptación
├── test_validation.py    # Tests de validación
└── conftest.py          # Configuración de pytest
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests con cobertura
pytest --cov=backend/src

# Tests específicos
pytest tests/test_app.py

# Tests en modo verbose
pytest -v
```

### Escribir Tests

Ejemplo de test para endpoint:

```python
def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'TestPass123',
        'csrf_token': get_csrf_token(client)
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
```

## 🔍 Debugging

### Logging

La aplicación usa el módulo `logging` de Python:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Mensaje informativo")
logger.warning("Mensaje de advertencia")
logger.error("Mensaje de error")
```

### Configuración de Logs

```python
# En app.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Debug con VS Code

Configuración en `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask App",
            "type": "python",
            "request": "launch",
            "program": "backend/src/app.py",
            "env": {
                "FLASK_ENV": "development"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

## 🔒 Consideraciones de Seguridad en Desarrollo

### Claves y Secretos

1. **Nunca commitear claves**: Usar `.gitignore`
2. **Claves de desarrollo**: Diferentes a producción
3. **Rotación**: Cambiar claves regularmente

### Base de Datos

1. **Datos de prueba**: No usar datos reales
2. **Backups**: Respaldar antes de cambios importantes
3. **Migraciones**: Probar en entorno de desarrollo primero

### Dependencias

1. **Actualizaciones**: Revisar vulnerabilidades regularmente
2. **Versiones**: Fijar versiones en `requirements.txt`
3. **Auditoría**: Usar `pip audit` para verificar seguridad

## 🚀 Flujo de Desarrollo

### 1. Configuración de Rama

```bash
git checkout -b feature/nueva-funcionalidad
```

### 2. Desarrollo

1. Escribir tests primero (TDD)
2. Implementar funcionalidad
3. Ejecutar tests localmente
4. Verificar estilo de código

### 3. Verificación

```bash
# Ejecutar tests
pytest

# Verificar estilo
flake8 backend/src/

# Formatear código
black backend/src/
```

### 4. Commit y Push

```bash
git add .
git commit -m "feat: agregar nueva funcionalidad"
git push origin feature/nueva-funcionalidad
```

### 5. Pull Request

1. Crear PR en GitHub/GitLab
2. Revisar código
3. Ejecutar tests en CI/CD
4. Merge a main

## 🛠️ Herramientas de Desarrollo

### Recomendadas

1. **Editor**: VS Code con extensiones Python
2. **Linting**: flake8, pylint
3. **Formateo**: black, isort
4. **Testing**: pytest, coverage
5. **Debug**: pdb, VS Code debugger

### Extensiones VS Code

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "bradlc.vscode-tailwindcss"
    ]
}
```

## 📊 Monitoreo y Métricas

### Logs de Desarrollo

Los logs se muestran en consola durante desarrollo:

```bash
python backend/src/app.py
# 2024-01-01 12:00:00 - app - INFO - Database initialized successfully
# 2024-01-01 12:00:01 - app - INFO - Server starting on 127.0.0.1:5000
```

### Métricas Básicas

- Tiempo de respuesta de endpoints
- Número de usuarios registrados
- Intentos de login fallidos
- Errores de base de datos

## 🔄 Contribución

### Estándares de Código

1. **PEP 8**: Seguir estándares de Python
2. **Docstrings**: Documentar funciones y clases
3. **Type hints**: Usar anotaciones de tipo
4. **Tests**: Cobertura mínima del 80%

### Proceso de Revisión

1. **Code review**: Al menos un revisor
2. **Tests**: Todos los tests deben pasar
3. **Documentación**: Actualizar si es necesario
4. **Changelog**: Documentar cambios importantes

### Reportar Bugs

1. **Issue template**: Usar plantilla de GitHub
2. **Reproducción**: Pasos claros para reproducir
3. **Logs**: Incluir logs relevantes
4. **Entorno**: Especificar versiones y OS