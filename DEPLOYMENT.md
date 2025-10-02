# Guía de Despliegue

Esta guía proporciona instrucciones detalladas para desplegar la aplicación web segura en diferentes entornos de producción.

## 🎯 Consideraciones Generales

### Requisitos de Producción

- **Sistema Operativo**: Linux (Ubuntu 20.04+ recomendado), Windows Server, o macOS
- **Python**: 3.8 o superior
- **Memoria RAM**: Mínimo 512MB, recomendado 1GB+
- **Almacenamiento**: Mínimo 1GB de espacio libre
- **Red**: Puerto 80/443 disponible para HTTP/HTTPS

### Diferencias entre Desarrollo y Producción

| Aspecto | Desarrollo | Producción |
|---------|------------|------------|
| Debug | Habilitado | Deshabilitado |
| HTTPS | Opcional | Obligatorio |
| Logs | Consola | Archivos |
| Base de datos | Local | Respaldada |
| Claves | Generadas | Configuradas |
| Monitoreo | Manual | Automatizado |

## 🐧 Despliegue en Linux (Ubuntu)

### 1. Preparación del Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y dependencias
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Crear usuario para la aplicación
sudo useradd -m -s /bin/bash webapp
sudo usermod -aG sudo webapp
```

### 2. Configuración de la Aplicación

```bash
# Cambiar a usuario webapp
sudo su - webapp

# Clonar repositorio
git clone <url-del-repositorio> /home/webapp/webapp-segura
cd /home/webapp/webapp-segura

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn  # Servidor WSGI para producción
```

### 3. Configuración de Producción

```bash
# Crear archivo de configuración
cat > backend/src/.env << EOF
DEBUG=False
SESSION_TIMEOUT=1800
MAX_LOGIN_ATTEMPTS=3
LOGIN_ATTEMPT_WINDOW=900
SESSION_COOKIE_SECURE=True
TEMPLATE_FOLDER=/home/webapp/webapp-segura/frontend/templates
STATIC_FOLDER=/home/webapp/webapp-segura/frontend/static
EOF

# Configurar permisos
chmod 600 backend/src/.env
chmod 755 /home/webapp/webapp-segura
```

### 4. Configuración de Gunicorn

```bash
# Crear archivo de configuración de Gunicorn
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "webapp"
group = "webapp"
tmp_upload_dir = None
errorlog = "/home/webapp/webapp-segura/logs/gunicorn_error.log"
accesslog = "/home/webapp/webapp-segura/logs/gunicorn_access.log"
loglevel = "info"
EOF

# Crear directorio de logs
mkdir -p logs
```

### 5. Configuración de Supervisor

```bash
# Crear configuración de supervisor (como root)
sudo cat > /etc/supervisor/conf.d/webapp-segura.conf << EOF
[program:webapp-segura]
command=/home/webapp/webapp-segura/venv/bin/gunicorn -c gunicorn.conf.py backend.src.app:app
directory=/home/webapp/webapp-segura
user=webapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/webapp/webapp-segura/logs/supervisor.log
environment=PATH="/home/webapp/webapp-segura/venv/bin"
EOF

# Recargar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start webapp-segura
```

### 6. Configuración de Nginx

```bash
# Crear configuración de Nginx
sudo cat > /etc/nginx/sites-available/webapp-segura << EOF
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Configuración SSL
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Configuración de archivos estáticos
    location /static/ {
        alias /home/webapp/webapp-segura/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Proxy a Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Logs
    access_log /var/log/nginx/webapp-segura_access.log;
    error_log /var/log/nginx/webapp-segura_error.log;
}
EOF

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/webapp-segura /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🪟 Despliegue en Windows Server

### 1. Preparación del Servidor

```powershell
# Instalar Python desde python.org
# Instalar IIS con CGI support
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-CGI

# Instalar Git
# Descargar desde git-scm.com
```

### 2. Configuración de la Aplicación

```powershell
# Clonar repositorio
git clone <url-del-repositorio> C:\inetpub\webapp-segura
cd C:\inetpub\webapp-segura

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install waitress  # Servidor WSGI para Windows
```

### 3. Configuración de IIS

```xml
<!-- web.config -->
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" 
           scriptProcessor="C:\inetpub\webapp-segura\venv\Scripts\python.exe|C:\inetpub\webapp-segura\backend\src\app.py" 
           resourceType="Unspecified" requireAccess="Script" />
    </handlers>
  </system.webServer>
</configuration>
```

### 4. Servicio de Windows

```powershell
# Crear script de servicio
@echo off
cd C:\inetpub\webapp-segura
venv\Scripts\python.exe -m waitress --host=127.0.0.1 --port=8000 backend.src.app:app
```



## 🔐 Configuración de SSL/TLS

### Certificado Let's Encrypt (Linux)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Configurar renovación automática
sudo crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Certificado Comercial

1. **Generar CSR**:
   ```bash
   openssl req -new -newkey rsa:2048 -nodes -keyout private.key -out certificate.csr
   ```

2. **Instalar certificado**:
   - Colocar archivos en `/etc/ssl/certs/`
   - Actualizar configuración de Nginx
   - Reiniciar servicios

## 💾 Backup y Restauración

### Script de Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/webapp/backups"
APP_DIR="/home/webapp/webapp-segura"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
cp $APP_DIR/backend/app.db $BACKUP_DIR/app_db_$DATE.db

# Backup de claves
cp $APP_DIR/backend/.secret.key $BACKUP_DIR/secret_key_$DATE.key

# Backup de configuración
cp $APP_DIR/backend/src/.env $BACKUP_DIR/env_$DATE.backup

# Comprimir logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz $APP_DIR/logs/

# Limpiar backups antiguos (mantener 30 días)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.key" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completado: $DATE"
```

### Automatizar Backups

```bash
# Agregar a crontab
crontab -e

# Backup diario a las 2:00 AM
0 2 * * * /home/webapp/backup.sh >> /home/webapp/backup.log 2>&1
```

### Restauración

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
APP_DIR="/home/webapp/webapp-segura"

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: $0 <archivo_backup.db>"
    exit 1
fi

# Detener aplicación
sudo supervisorctl stop webapp-segura

# Restaurar base de datos
cp $BACKUP_FILE $APP_DIR/backend/app.db

# Configurar permisos
chown webapp:webapp $APP_DIR/backend/app.db
chmod 644 $APP_DIR/backend/app.db

# Reiniciar aplicación
sudo supervisorctl start webapp-segura

echo "Restauración completada"
```

## 📊 Monitoreo y Logs

### Configuración de Logs

```python
# En config.py para producción
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/webapp.log', 
        maxBytes=10240000, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Monitoreo con Systemd

```bash
# Ver logs en tiempo real
sudo journalctl -u supervisor -f

# Ver estado del servicio
sudo systemctl status supervisor
```

### Métricas Básicas

```bash
# Script de monitoreo básico
#!/bin/bash
# monitor.sh

# Verificar que la aplicación responda
curl -f http://localhost:8000/ > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ALERT: Aplicación no responde"
    sudo supervisorctl restart webapp-segura
fi

# Verificar uso de disco
DISK_USAGE=$(df /home/webapp | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Uso de disco alto: $DISK_USAGE%"
fi

# Verificar logs de error
ERROR_COUNT=$(tail -100 /home/webapp/webapp-segura/logs/gunicorn_error.log | grep ERROR | wc -l)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "ALERT: Muchos errores en logs: $ERROR_COUNT"
fi
```

## 🔧 Mantenimiento

### Actualizaciones

```bash
#!/bin/bash
# update.sh

APP_DIR="/home/webapp/webapp-segura"
cd $APP_DIR

# Backup antes de actualizar
./backup.sh

# Detener aplicación
sudo supervisorctl stop webapp-segura

# Actualizar código
git pull origin main

# Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar aplicación
sudo supervisorctl start webapp-segura

echo "Actualización completada"
```

### Limpieza de Logs

```bash
#!/bin/bash
# cleanup.sh

LOG_DIR="/home/webapp/webapp-segura/logs"

# Comprimir logs antiguos
find $LOG_DIR -name "*.log" -mtime +7 -exec gzip {} \;

# Eliminar logs muy antiguos
find $LOG_DIR -name "*.gz" -mtime +30 -delete

# Limpiar logs de sistema
sudo journalctl --vacuum-time=30d
```

## 🚨 Solución de Problemas en Producción

### Problemas Comunes

#### 1. Aplicación no inicia
```bash
# Verificar logs
sudo supervisorctl tail webapp-segura stderr

# Verificar configuración
python backend/src/app.py  # En modo debug temporal
```

#### 2. Error 502 Bad Gateway
```bash
# Verificar que Gunicorn esté corriendo
sudo supervisorctl status webapp-segura

# Verificar configuración de Nginx
sudo nginx -t
```

#### 3. Base de datos corrupta
```bash
# Verificar integridad
sqlite3 backend/app.db "PRAGMA integrity_check;"

# Restaurar desde backup
./restore.sh /home/webapp/backups/app_db_YYYYMMDD_HHMMSS.db
```

#### 4. Certificado SSL expirado
```bash
# Verificar expiración
openssl x509 -in /etc/ssl/certs/certificate.crt -text -noout | grep "Not After"

# Renovar Let's Encrypt
sudo certbot renew
```

### Comandos Útiles

```bash
# Ver procesos de la aplicación
ps aux | grep gunicorn

# Ver conexiones de red
netstat -tlnp | grep :8000

# Ver uso de recursos
htop

# Ver logs en tiempo real
tail -f logs/gunicorn_access.log

# Reiniciar todos los servicios
sudo supervisorctl restart webapp-segura
sudo systemctl reload nginx
```

## 📋 Checklist de Despliegue

### Pre-despliegue
- [ ] Servidor configurado con requisitos mínimos
- [ ] Certificado SSL obtenido e instalado
- [ ] Backup de datos existentes (si aplica)
- [ ] Variables de entorno configuradas
- [ ] Firewall configurado (puertos 80, 443)

### Despliegue
- [ ] Código clonado y dependencias instaladas
- [ ] Base de datos inicializada
- [ ] Servicios configurados (Supervisor/Systemd)
- [ ] Proxy reverso configurado (Nginx/Apache)
- [ ] SSL/TLS configurado y funcionando

### Post-despliegue
- [ ] Aplicación accesible vía HTTPS
- [ ] Funcionalidad básica probada
- [ ] Logs configurados y funcionando
- [ ] Backups automatizados configurados
- [ ] Monitoreo básico implementado
- [ ] Documentación actualizada

## 🔒 Mejores Prácticas de Seguridad

### Configuración del Servidor
1. **Firewall**: Solo puertos necesarios abiertos
2. **Updates**: Sistema operativo actualizado
3. **Users**: Usuario dedicado sin privilegios sudo
4. **SSH**: Autenticación por clave, no por contraseña

### Aplicación
1. **HTTPS**: Obligatorio en producción
2. **Headers**: Configurar headers de seguridad
3. **Logs**: No registrar información sensible
4. **Secrets**: Variables de entorno, no en código

### Base de Datos
1. **Backups**: Automatizados y probados
2. **Permisos**: Solo la aplicación puede acceder
3. **Encriptación**: Datos sensibles encriptados
4. **Auditoría**: Logs de acceso habilitados