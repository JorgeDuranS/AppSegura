# Guía de Base de Datos

Esta guía proporciona información detallada sobre la gestión de la base de datos SQLite, incluyendo procedimientos de backup, restauración y mantenimiento.

## 🗄️ Estructura de la Base de Datos

### Schema SQLite

La aplicación utiliza SQLite con el siguiente schema:

```sql
-- Tabla de usuarios
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de datos del usuario
CREATE TABLE data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users (username)
);

-- Índices para optimización
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_data_username ON data(username);
```

### Ubicación de Archivos

- **Base de datos principal**: `backend/app.db`
- **Clave de encriptación**: `backend/.secret.key`
- **Schema SQL**: `database/sqlite_schema.sql`
- **Scripts de migración**: `database/migrate_to_sqlite.py`

## 💾 Procedimientos de Backup

### 1. Backup Manual

#### Backup Básico
```bash
# Copiar archivo de base de datos
cp backend/app.db backup/app_$(date +%Y%m%d_%H%M%S).db

# Copiar clave de encriptación
cp backend/.secret.key backup/secret_$(date +%Y%m%d_%H%M%S).key
```

#### Backup con SQLite Dump
```bash
# Crear dump SQL
sqlite3 backend/app.db .dump > backup/dump_$(date +%Y%m%d_%H%M%S).sql

# Comprimir dump
gzip backup/dump_$(date +%Y%m%d_%H%M%S).sql
```

#### Backup Completo con Script
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="backup"
DB_FILE="backend/app.db"
KEY_FILE="backend/.secret.key"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backup si no existe
mkdir -p $BACKUP_DIR

echo "Iniciando backup de base de datos..."

# Verificar que la base de datos existe
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Base de datos no encontrada en $DB_FILE"
    exit 1
fi

# Backup de archivo de base de datos
echo "Copiando archivo de base de datos..."
cp "$DB_FILE" "$BACKUP_DIR/app_db_$DATE.db"

# Backup de clave de encriptación
if [ -f "$KEY_FILE" ]; then
    echo "Copiando clave de encriptación..."
    cp "$KEY_FILE" "$BACKUP_DIR/secret_key_$DATE.key"
fi

# Crear dump SQL
echo "Creando dump SQL..."
sqlite3 "$DB_FILE" .dump > "$BACKUP_DIR/dump_$DATE.sql"

# Comprimir dump
echo "Comprimiendo dump..."
gzip "$BACKUP_DIR/dump_$DATE.sql"

# Verificar integridad de la base de datos
echo "Verificando integridad..."
INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "ADVERTENCIA: Problemas de integridad detectados: $INTEGRITY"
else
    echo "Integridad verificada: OK"
fi

# Mostrar estadísticas
echo "Estadísticas del backup:"
echo "- Archivo DB: $(ls -lh $BACKUP_DIR/app_db_$DATE.db | awk '{print $5}')"
echo "- Dump comprimido: $(ls -lh $BACKUP_DIR/dump_$DATE.sql.gz | awk '{print $5}')"

# Contar registros
USER_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM users;")
DATA_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM data;")
echo "- Usuarios: $USER_COUNT"
echo "- Registros de datos: $DATA_COUNT"

echo "Backup completado exitosamente: $DATE"
```

### 2. Backup Automatizado

#### Configuración con Cron (Linux/macOS)
```bash
# Editar crontab
crontab -e

# Backup diario a las 2:00 AM
0 2 * * * /path/to/webapp-segura/backup_database.sh >> /path/to/webapp-segura/backup.log 2>&1

# Backup cada 6 horas
0 */6 * * * /path/to/webapp-segura/backup_database.sh >> /path/to/webapp-segura/backup.log 2>&1
```

#### Script de Backup con Rotación
```bash
#!/bin/bash
# backup_with_rotation.sh

BACKUP_DIR="backup"
DB_FILE="backend/app.db"
KEY_FILE="backend/.secret.key"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Realizar backup
cp "$DB_FILE" "$BACKUP_DIR/app_db_$DATE.db"
cp "$KEY_FILE" "$BACKUP_DIR/secret_key_$DATE.key"

# Limpiar backups antiguos
find $BACKUP_DIR -name "app_db_*.db" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "secret_key_*.key" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "dump_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup con rotación completado: $DATE"
```

#### Configuración en Windows (Task Scheduler)
```batch
@echo off
REM backup_database.bat

set BACKUP_DIR=backup
set DB_FILE=backend\app.db
set KEY_FILE=backend\.secret.key
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

copy "%DB_FILE%" "%BACKUP_DIR%\app_db_%DATE%.db"
copy "%KEY_FILE%" "%BACKUP_DIR%\secret_key_%DATE%.key"

echo Backup completado: %DATE%
```

## 🔄 Procedimientos de Restauración

### 1. Restauración desde Archivo de Base de Datos

```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1
DB_FILE="backend/app.db"
KEY_FILE="backend/.secret.key"

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: $0 <archivo_backup.db> [archivo_clave.key]"
    echo "Ejemplo: $0 backup/app_db_20240101_120000.db backup/secret_key_20240101_120000.key"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Archivo de backup no encontrado: $BACKUP_FILE"
    exit 1
fi

echo "Iniciando restauración de base de datos..."

# Crear backup del estado actual antes de restaurar
if [ -f "$DB_FILE" ]; then
    echo "Creando backup del estado actual..."
    cp "$DB_FILE" "$DB_FILE.before_restore_$(date +%Y%m%d_%H%M%S)"
fi

# Detener la aplicación si está corriendo
echo "Deteniendo aplicación..."
pkill -f "python.*app.py" 2>/dev/null || true

# Restaurar base de datos
echo "Restaurando base de datos desde $BACKUP_FILE..."
cp "$BACKUP_FILE" "$DB_FILE"

# Restaurar clave si se proporciona
if [ -n "$2" ] && [ -f "$2" ]; then
    echo "Restaurando clave de encriptación..."
    cp "$2" "$KEY_FILE"
fi

# Verificar integridad
echo "Verificando integridad de la base de datos restaurada..."
INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "ERROR: Problemas de integridad en la base de datos restaurada: $INTEGRITY"
    exit 1
else
    echo "Integridad verificada: OK"
fi

# Mostrar estadísticas
USER_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM users;")
DATA_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM data;")
echo "Base de datos restaurada:"
echo "- Usuarios: $USER_COUNT"
echo "- Registros de datos: $DATA_COUNT"

echo "Restauración completada exitosamente"
echo "Puedes reiniciar la aplicación ahora"
```

### 2. Restauración desde Dump SQL

```bash
#!/bin/bash
# restore_from_dump.sh

DUMP_FILE=$1
DB_FILE="backend/app.db"

if [ -z "$DUMP_FILE" ]; then
    echo "Uso: $0 <archivo_dump.sql>"
    exit 1
fi

# Descomprimir si es necesario
if [[ "$DUMP_FILE" == *.gz ]]; then
    echo "Descomprimiendo dump..."
    gunzip -c "$DUMP_FILE" > temp_dump.sql
    DUMP_FILE="temp_dump.sql"
fi

if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: Archivo dump no encontrado: $DUMP_FILE"
    exit 1
fi

echo "Restaurando desde dump SQL..."

# Backup del estado actual
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$DB_FILE.before_restore_$(date +%Y%m%d_%H%M%S)"
fi

# Detener aplicación
pkill -f "python.*app.py" 2>/dev/null || true

# Eliminar base de datos actual
rm -f "$DB_FILE"

# Restaurar desde dump
sqlite3 "$DB_FILE" < "$DUMP_FILE"

# Limpiar archivo temporal
if [ -f "temp_dump.sql" ]; then
    rm temp_dump.sql
fi

echo "Restauración desde dump completada"
```

## 🔧 Mantenimiento de Base de Datos

### 1. Verificación de Integridad

```bash
#!/bin/bash
# check_integrity.sh

DB_FILE="backend/app.db"

echo "Verificando integridad de la base de datos..."

# Verificación básica
INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
echo "Integridad: $INTEGRITY"

# Verificación de claves foráneas
FOREIGN_KEYS=$(sqlite3 "$DB_FILE" "PRAGMA foreign_key_check;")
if [ -z "$FOREIGN_KEYS" ]; then
    echo "Claves foráneas: OK"
else
    echo "Problemas con claves foráneas:"
    echo "$FOREIGN_KEYS"
fi

# Estadísticas de la base de datos
echo ""
echo "Estadísticas:"
sqlite3 "$DB_FILE" "
SELECT 'Usuarios: ' || COUNT(*) FROM users;
SELECT 'Datos: ' || COUNT(*) FROM data;
SELECT 'Tamaño DB: ' || (page_count * page_size) || ' bytes' FROM pragma_page_count(), pragma_page_size();
"
```

### 2. Optimización de Base de Datos

```bash
#!/bin/bash
# optimize_database.sh

DB_FILE="backend/app.db"

echo "Optimizando base de datos..."

# Crear backup antes de optimizar
cp "$DB_FILE" "$DB_FILE.before_optimize_$(date +%Y%m%d_%H%M%S)"

# Ejecutar VACUUM para compactar
echo "Ejecutando VACUUM..."
sqlite3 "$DB_FILE" "VACUUM;"

# Analizar estadísticas
echo "Analizando estadísticas..."
sqlite3 "$DB_FILE" "ANALYZE;"

# Reindexar
echo "Reindexando..."
sqlite3 "$DB_FILE" "REINDEX;"

echo "Optimización completada"
```

### 3. Limpieza de Datos

```bash
#!/bin/bash
# cleanup_database.sh

DB_FILE="backend/app.db"

echo "Limpiando datos antiguos..."

# Eliminar datos de usuarios inactivos (ejemplo: sin datos guardados hace más de 1 año)
sqlite3 "$DB_FILE" "
DELETE FROM users 
WHERE username NOT IN (
    SELECT DISTINCT username 
    FROM data 
    WHERE created_at > datetime('now', '-1 year')
) 
AND created_at < datetime('now', '-1 year');
"

# Mostrar estadísticas después de limpieza
echo "Estadísticas después de limpieza:"
sqlite3 "$DB_FILE" "
SELECT 'Usuarios restantes: ' || COUNT(*) FROM users;
SELECT 'Datos restantes: ' || COUNT(*) FROM data;
"
```

## 📊 Monitoreo de Base de Datos

### 1. Script de Monitoreo

```bash
#!/bin/bash
# monitor_database.sh

DB_FILE="backend/app.db"
LOG_FILE="database_monitor.log"

# Función para log con timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Verificar que la base de datos existe
if [ ! -f "$DB_FILE" ]; then
    log_message "ERROR: Base de datos no encontrada"
    exit 1
fi

# Verificar integridad
INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    log_message "ERROR: Problemas de integridad: $INTEGRITY"
fi

# Verificar tamaño de base de datos
DB_SIZE=$(stat -f%z "$DB_FILE" 2>/dev/null || stat -c%s "$DB_FILE" 2>/dev/null)
if [ $DB_SIZE -gt 1073741824 ]; then  # 1GB
    log_message "WARNING: Base de datos grande: $DB_SIZE bytes"
fi

# Verificar número de usuarios
USER_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM users;")
log_message "INFO: Usuarios activos: $USER_COUNT"

# Verificar conexiones (si la aplicación está corriendo)
CONNECTIONS=$(lsof "$DB_FILE" 2>/dev/null | wc -l)
if [ $CONNECTIONS -gt 5 ]; then
    log_message "WARNING: Muchas conexiones abiertas: $CONNECTIONS"
fi

log_message "INFO: Monitoreo completado"
```

### 2. Alertas Automáticas

```bash
#!/bin/bash
# database_alerts.sh

DB_FILE="backend/app.db"
ALERT_EMAIL="admin@example.com"

# Verificar integridad
INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "ALERTA: Problemas de integridad en base de datos" | mail -s "DB Alert" $ALERT_EMAIL
fi

# Verificar espacio en disco
DISK_USAGE=$(df $(dirname "$DB_FILE") | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "ALERTA: Poco espacio en disco: $DISK_USAGE%" | mail -s "Disk Alert" $ALERT_EMAIL
fi
```

## 🔒 Seguridad de Base de Datos

### 1. Permisos de Archivos

```bash
# Configurar permisos seguros
chmod 600 backend/app.db          # Solo propietario puede leer/escribir
chmod 600 backend/.secret.key     # Solo propietario puede leer/escribir
chmod 700 backup/                 # Solo propietario puede acceder al directorio
```

### 2. Encriptación de Backups

```bash
#!/bin/bash
# encrypted_backup.sh

BACKUP_FILE="backup/app_db_$(date +%Y%m%d_%H%M%S).db"
ENCRYPTED_FILE="$BACKUP_FILE.gpg"

# Crear backup
cp backend/app.db "$BACKUP_FILE"

# Encriptar backup
gpg --symmetric --cipher-algo AES256 --output "$ENCRYPTED_FILE" "$BACKUP_FILE"

# Eliminar backup sin encriptar
rm "$BACKUP_FILE"

echo "Backup encriptado creado: $ENCRYPTED_FILE"
```

### 3. Verificación de Acceso

```bash
#!/bin/bash
# check_access.sh

DB_FILE="backend/app.db"

# Verificar permisos
PERMS=$(stat -f%Mp%Lp "$DB_FILE" 2>/dev/null || stat -c%a "$DB_FILE" 2>/dev/null)
if [ "$PERMS" != "600" ]; then
    echo "WARNING: Permisos incorrectos en base de datos: $PERMS"
fi

# Verificar propietario
OWNER=$(stat -f%Su "$DB_FILE" 2>/dev/null || stat -c%U "$DB_FILE" 2>/dev/null)
echo "Propietario de la base de datos: $OWNER"
```

## 🚨 Recuperación de Desastres

### 1. Plan de Recuperación

```bash
#!/bin/bash
# disaster_recovery.sh

echo "=== PLAN DE RECUPERACIÓN DE DESASTRES ==="
echo "1. Detener aplicación"
echo "2. Evaluar daño en base de datos"
echo "3. Restaurar desde backup más reciente"
echo "4. Verificar integridad"
echo "5. Reiniciar aplicación"
echo "6. Verificar funcionalidad"

read -p "¿Continuar con recuperación? (y/N): " confirm
if [ "$confirm" != "y" ]; then
    exit 0
fi

# Detener aplicación
echo "Deteniendo aplicación..."
pkill -f "python.*app.py"

# Encontrar backup más reciente
LATEST_BACKUP=$(ls -t backup/app_db_*.db | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No se encontraron backups"
    exit 1
fi

echo "Restaurando desde: $LATEST_BACKUP"
./restore_database.sh "$LATEST_BACKUP"

echo "Recuperación completada"
```

### 2. Procedimiento de Emergencia

```bash
#!/bin/bash
# emergency_procedure.sh

DB_FILE="backend/app.db"
EMERGENCY_BACKUP="emergency_backup_$(date +%Y%m%d_%H%M%S).db"

echo "=== PROCEDIMIENTO DE EMERGENCIA ==="

# Crear backup de emergencia del estado actual
if [ -f "$DB_FILE" ]; then
    echo "Creando backup de emergencia..."
    cp "$DB_FILE" "$EMERGENCY_BACKUP"
fi

# Intentar reparar base de datos
echo "Intentando reparar base de datos..."
sqlite3 "$DB_FILE" "
.recover
.exit
"

# Verificar reparación
INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
if [ "$INTEGRITY" = "ok" ]; then
    echo "Reparación exitosa"
else
    echo "Reparación falló, restaurando desde backup..."
    LATEST_BACKUP=$(ls -t backup/app_db_*.db | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" "$DB_FILE"
    fi
fi

echo "Procedimiento de emergencia completado"
```

## 📋 Checklist de Mantenimiento

### Diario
- [ ] Verificar que los backups automáticos se ejecuten
- [ ] Revisar logs de errores de base de datos
- [ ] Verificar espacio en disco disponible

### Semanal
- [ ] Ejecutar verificación de integridad
- [ ] Revisar tamaño de base de datos
- [ ] Limpiar logs antiguos

### Mensual
- [ ] Optimizar base de datos (VACUUM, ANALYZE)
- [ ] Probar procedimiento de restauración
- [ ] Revisar y limpiar backups antiguos
- [ ] Actualizar scripts de mantenimiento

### Trimestral
- [ ] Revisar plan de recuperación de desastres
- [ ] Probar recuperación completa desde backup
- [ ] Revisar permisos y seguridad
- [ ] Documentar cambios y mejoras