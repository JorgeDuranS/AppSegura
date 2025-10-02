# Mejores Prácticas de Seguridad

Esta guía proporciona las mejores prácticas de seguridad implementadas en la aplicación web segura y recomendaciones para mantener un entorno seguro.

## 🔒 Características de Seguridad Implementadas

### 1. Autenticación y Autorización

#### Hash de Contraseñas
- **Algoritmo**: PBKDF2 con SHA-256 (Werkzeug)
- **Salt**: Generado automáticamente por usuario
- **Iteraciones**: 260,000 (por defecto de Werkzeug)

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Generar hash
password_hash = generate_password_hash(password)

# Verificar contraseña
is_valid = check_password_hash(password_hash, password)
```

#### Gestión de Sesiones
- **Cookies HTTPOnly**: Previene acceso desde JavaScript
- **Secure Flag**: Solo transmisión por HTTPS en producción
- **SameSite**: Protección contra CSRF
- **Timeout**: Expiración automática de sesiones

```python
app.config.update({
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': not DEBUG,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': timedelta(seconds=3600)
})
```

### 2. Protección CSRF

#### Tokens CSRF
- **Generación**: Token único por sesión
- **Validación**: Verificación en todas las operaciones POST
- **Expiración**: Mismo tiempo que la sesión

```python
from flask_wtf.csrf import CSRFProtect, validate_csrf

csrf = CSRFProtect(app)

# Validación manual
validate_csrf(request.form.get('csrf_token'))
```

### 3. Rate Limiting

#### Protección contra Fuerza Bruta
- **Límite**: 5 intentos por IP cada 15 minutos
- **Ventana**: 900 segundos (15 minutos)
- **Almacenamiento**: En memoria (producción: Redis recomendado)

```python
def is_rate_limited(ip_address: str) -> bool:
    current_time = time.time()
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    
    # Limpiar intentos antiguos
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address]
        if current_time - attempt_time < LOGIN_ATTEMPT_WINDOW
    ]
    
    return len(login_attempts[ip_address]) >= MAX_LOGIN_ATTEMPTS
```

### 4. Encriptación de Datos

#### Fernet (AES 128)
- **Algoritmo**: AES 128 en modo CBC
- **Autenticación**: HMAC SHA-256
- **Clave**: 32 bytes generados aleatoriamente

```python
from cryptography.fernet import Fernet

def encrypt_data(data: str, key: bytes) -> bytes:
    fernet = Fernet(key)
    return fernet.encrypt(data.encode('utf-8'))

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode('utf-8')
```

### 5. Validación y Sanitización

#### Validación de Entrada
- **Username**: 3-50 caracteres alfanuméricos
- **Password**: Mínimo 8 caracteres, mayúsculas, minúsculas, números
- **Data**: Máximo 10,000 caracteres

```python
def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, "El nombre de usuario es requerido"
    
    if len(username) < 3 or len(username) > 50:
        return False, "El nombre de usuario debe tener entre 3 y 50 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números y guiones bajos"
    
    return True, ""
```

#### Sanitización
```python
import html
import re

def sanitize_input(data: str) -> str:
    if not data:
        return ""
    
    # Escapar HTML
    data = html.escape(data)
    
    # Remover caracteres de control
    data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)
    
    # Normalizar espacios
    data = ' '.join(data.split())
    
    return data.strip()
```

### 6. Headers de Seguridad

#### Headers HTTP Seguros
```python
@app.after_request
def after_request(response):
    # Prevenir MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevenir clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Protección XSS
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Política de referrer
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy
    if not DEBUG:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    
    return response
```

## 🛡️ Configuración de Seguridad

### 1. Variables de Entorno Seguras

```env
# Configuración de producción
DEBUG=False
SESSION_TIMEOUT=1800
MAX_LOGIN_ATTEMPTS=3
LOGIN_ATTEMPT_WINDOW=900

# Configuración de cookies
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Configuración CSRF
WTF_CSRF_TIME_LIMIT=1800
WTF_CSRF_SSL_STRICT=True
```

### 2. Generación de Claves Seguras

```python
import secrets
import os

def generate_secret_key() -> bytes:
    """Generar clave secreta criptográficamente segura"""
    return secrets.token_bytes(32)

def save_secret_key(key: bytes, filepath: str):
    """Guardar clave con permisos seguros"""
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Escribir clave
    with open(filepath, 'wb') as f:
        f.write(key)
    
    # Configurar permisos (solo propietario)
    if os.name != 'nt':  # No Windows
        os.chmod(filepath, 0o600)
```

### 3. Configuración de Base de Datos Segura

```python
def get_db_connection():
    """Conexión segura a base de datos"""
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=30.0,
        isolation_level=None,  # Autocommit mode
        check_same_thread=False
    )
    
    # Habilitar claves foráneas
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Configurar journal mode para mejor concurrencia
    conn.execute("PRAGMA journal_mode = WAL")
    
    return conn
```

## 🔍 Auditoría y Logging

### 1. Logging de Seguridad

```python
import logging

# Configurar logger de seguridad
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('logs/security.log')
security_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# Eventos a registrar
def log_security_event(event_type: str, details: dict):
    security_logger.info(f"{event_type}: {details}")

# Ejemplos de uso
log_security_event("LOGIN_ATTEMPT", {
    "username": username,
    "ip": get_client_ip(),
    "success": False,
    "reason": "invalid_password"
})

log_security_event("RATE_LIMIT", {
    "ip": get_client_ip(),
    "attempts": len(login_attempts[ip])
})
```

### 2. Eventos de Seguridad a Monitorear

#### Autenticación
- Intentos de login exitosos/fallidos
- Bloqueos por rate limiting
- Creación de nuevos usuarios
- Cambios de contraseña

#### Acceso a Datos
- Acceso a datos de usuario
- Modificación de datos
- Intentos de acceso no autorizados

#### Errores de Seguridad
- Tokens CSRF inválidos
- Violaciones de validación
- Errores de encriptación/desencriptación

### 3. Script de Análisis de Logs

```bash
#!/bin/bash
# analyze_security_logs.sh

LOG_FILE="logs/security.log"
REPORT_FILE="security_report_$(date +%Y%m%d).txt"

echo "=== REPORTE DE SEGURIDAD ===" > $REPORT_FILE
echo "Fecha: $(date)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Intentos de login fallidos
echo "=== INTENTOS DE LOGIN FALLIDOS ===" >> $REPORT_FILE
grep "LOGIN_ATTEMPT.*success.*False" $LOG_FILE | tail -20 >> $REPORT_FILE
echo "" >> $REPORT_FILE

# IPs bloqueadas por rate limiting
echo "=== RATE LIMITING ===" >> $REPORT_FILE
grep "RATE_LIMIT" $LOG_FILE | tail -10 >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Errores CSRF
echo "=== ERRORES CSRF ===" >> $REPORT_FILE
grep "CSRF" $LOG_FILE | tail -10 >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "Reporte generado: $REPORT_FILE"
```

## 🚨 Detección de Amenazas

### 1. Indicadores de Compromiso

#### Patrones Sospechosos
- Múltiples intentos de login desde la misma IP
- Intentos de acceso a rutas no existentes
- Patrones de inyección SQL en parámetros
- Intentos de bypass de autenticación

```python
def detect_suspicious_activity(request_data: dict) -> list:
    """Detectar actividad sospechosa"""
    alerts = []
    
    # Detectar intentos de inyección SQL
    sql_patterns = [
        r"union\s+select", r"drop\s+table", r"insert\s+into",
        r"delete\s+from", r"update\s+set", r"exec\s*\("
    ]
    
    for field, value in request_data.items():
        if isinstance(value, str):
            for pattern in sql_patterns:
                if re.search(pattern, value.lower()):
                    alerts.append(f"Posible inyección SQL en {field}: {value[:50]}")
    
    return alerts
```

### 2. Sistema de Alertas

```python
def send_security_alert(alert_type: str, details: dict):
    """Enviar alerta de seguridad"""
    message = f"ALERTA DE SEGURIDAD: {alert_type}\n"
    message += f"Detalles: {details}\n"
    message += f"Timestamp: {datetime.now()}\n"
    
    # En producción: enviar email, Slack, etc.
    logger.critical(message)
    
    # Ejemplo de integración con email
    # send_email(
    #     to="security@company.com",
    #     subject=f"Security Alert: {alert_type}",
    #     body=message
    # )
```

## 🔧 Hardening del Sistema

### 1. Configuración del Servidor Web

#### Nginx
```nginx
server {
    # Ocultar versión de Nginx
    server_tokens off;
    
    # Límites de rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 2. Configuración del Sistema Operativo

#### Linux
```bash
# Configurar firewall
ufw enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS

# Configurar fail2ban
apt install fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true
EOF

# Configurar actualizaciones automáticas
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

### 3. Permisos de Archivos

```bash
#!/bin/bash
# secure_permissions.sh

APP_DIR="/path/to/webapp-segura"
APP_USER="webapp"

# Configurar propietario
chown -R $APP_USER:$APP_USER $APP_DIR

# Permisos de directorios
find $APP_DIR -type d -exec chmod 755 {} \;

# Permisos de archivos
find $APP_DIR -type f -exec chmod 644 {} \;

# Archivos ejecutables
chmod 755 $APP_DIR/backend/src/app.py

# Archivos sensibles
chmod 600 $APP_DIR/backend/.secret.key
chmod 600 $APP_DIR/backend/src/.env
chmod 600 $APP_DIR/backend/app.db

# Directorio de logs
chmod 750 $APP_DIR/logs
```

## 🔄 Mantenimiento de Seguridad

### 1. Actualizaciones

```bash
#!/bin/bash
# security_updates.sh

# Actualizar dependencias Python
pip list --outdated
pip install --upgrade -r requirements.txt

# Verificar vulnerabilidades conocidas
pip audit

# Actualizar sistema operativo
apt update && apt upgrade -y

# Verificar configuración de seguridad
./security_check.sh
```

### 2. Rotación de Claves

```bash
#!/bin/bash
# rotate_keys.sh

BACKUP_DIR="key_backups"
KEY_FILE="backend/.secret.key"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear backup de clave actual
mkdir -p $BACKUP_DIR
cp $KEY_FILE $BACKUP_DIR/secret_key_$DATE.backup

# Generar nueva clave
python3 -c "
import secrets
with open('$KEY_FILE', 'wb') as f:
    f.write(secrets.token_bytes(32))
"

# Configurar permisos
chmod 600 $KEY_FILE

echo "Clave rotada exitosamente. Backup en: $BACKUP_DIR/secret_key_$DATE.backup"
echo "IMPORTANTE: Reinicia la aplicación para usar la nueva clave"
```

### 3. Auditoría de Seguridad

```bash
#!/bin/bash
# security_audit.sh

echo "=== AUDITORÍA DE SEGURIDAD ==="

# Verificar permisos de archivos
echo "Verificando permisos..."
find . -name "*.key" -not -perm 600 -ls
find . -name ".env" -not -perm 600 -ls

# Verificar configuración SSL
echo "Verificando SSL..."
openssl s509 -in /etc/ssl/certs/certificate.crt -text -noout | grep "Not After"

# Verificar logs de seguridad
echo "Verificando logs..."
grep -i "error\|warning\|alert" logs/security.log | tail -10

# Verificar actualizaciones pendientes
echo "Verificando actualizaciones..."
pip list --outdated

echo "Auditoría completada"
```

## 📋 Checklist de Seguridad

### Configuración Inicial
- [ ] Claves secretas generadas aleatoriamente
- [ ] Permisos de archivos configurados correctamente
- [ ] HTTPS habilitado en producción
- [ ] Headers de seguridad configurados
- [ ] Rate limiting implementado

### Autenticación
- [ ] Hash de contraseñas con salt
- [ ] Validación de fortaleza de contraseñas
- [ ] Protección contra fuerza bruta
- [ ] Gestión segura de sesiones
- [ ] Logout seguro implementado

### Datos
- [ ] Encriptación de datos sensibles
- [ ] Validación y sanitización de entrada
- [ ] Protección contra inyección SQL
- [ ] Backup de datos encriptados
- [ ] Acceso a datos auditado

### Monitoreo
- [ ] Logging de eventos de seguridad
- [ ] Alertas automáticas configuradas
- [ ] Monitoreo de intentos de intrusión
- [ ] Análisis regular de logs
- [ ] Plan de respuesta a incidentes

### Mantenimiento
- [ ] Actualizaciones regulares de dependencias
- [ ] Rotación periódica de claves
- [ ] Auditorías de seguridad programadas
- [ ] Pruebas de penetración periódicas
- [ ] Documentación de seguridad actualizada

## 🚨 Respuesta a Incidentes

### 1. Plan de Respuesta

```bash
#!/bin/bash
# incident_response.sh

echo "=== RESPUESTA A INCIDENTE DE SEGURIDAD ==="
echo "1. Identificar y contener la amenaza"
echo "2. Evaluar el alcance del compromiso"
echo "3. Preservar evidencia"
echo "4. Erradicar la amenaza"
echo "5. Recuperar sistemas"
echo "6. Documentar lecciones aprendidas"

read -p "¿Tipo de incidente? (breach/malware/dos/other): " incident_type
read -p "¿Descripción breve?: " description

# Crear directorio de evidencia
EVIDENCE_DIR="incident_$(date +%Y%m%d_%H%M%S)"
mkdir -p $EVIDENCE_DIR

# Recopilar logs
cp logs/*.log $EVIDENCE_DIR/
cp /var/log/nginx/*.log $EVIDENCE_DIR/

# Crear snapshot de base de datos
cp backend/app.db $EVIDENCE_DIR/

# Documentar incidente
cat > $EVIDENCE_DIR/incident_report.txt << EOF
REPORTE DE INCIDENTE DE SEGURIDAD
Fecha: $(date)
Tipo: $incident_type
Descripción: $description
Investigador: $(whoami)

ACCIONES TOMADAS:
- Evidencia preservada en $EVIDENCE_DIR
- Logs recopilados
- Base de datos respaldada

PRÓXIMOS PASOS:
- Análisis forense de logs
- Evaluación de impacto
- Implementación de contramedidas
EOF

echo "Evidencia recopilada en: $EVIDENCE_DIR"
```

### 2. Contactos de Emergencia

```bash
# emergency_contacts.sh

echo "=== CONTACTOS DE EMERGENCIA ==="
echo "Administrador del Sistema: admin@company.com"
echo "Equipo de Seguridad: security@company.com"
echo "Soporte Técnico: support@company.com"
echo "Gerencia: management@company.com"
```

Esta guía de seguridad debe revisarse y actualizarse regularmente para mantener la aplicación protegida contra las amenazas más recientes.