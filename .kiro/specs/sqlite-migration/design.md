# Design Document

## Overview

Esta migración transformará la aplicación web segura de una arquitectura basada en PostgreSQL/Docker a una solución más simple usando SQLite. El diseño se enfoca en mantener la funcionalidad de seguridad existente mientras se mejora la robustez del código, se añade una interfaz moderna con Tailwind CSS, y se simplifica el proceso de despliegue.

## Architecture

### Current vs New Architecture

**Actual:**
```
Flask App → PostgreSQL (Docker) → Adminer (Docker)
```

**Nueva:**
```
Flask App → SQLite (local file) → Web Interface (Tailwind CSS)
```

### Key Changes
- Reemplazo de `psycopg2` con `sqlite3` (built-in Python)
- Eliminación de Docker y servicios externos
- Mejora del manejo de errores y validación
- Interfaz moderna con Tailwind CSS
- Documentación completa de instalación

## Components and Interfaces

### 1. Database Layer (`database/`)
- **SQLite Database**: `app.db` - archivo local de base de datos
- **Schema Migration**: Script para crear tablas automáticamente
- **Connection Management**: Context managers para manejo seguro de conexiones

### 2. Backend Layer (`backend/src/`)
- **app.py**: Aplicación Flask principal con rutas mejoradas
- **crypto.py**: Módulo de encriptación corregido
- **database.py**: Nuevo módulo para operaciones de base de datos
- **config.py**: Configuración centralizada y segura

### 3. Frontend Layer (`frontend/`)
- **Templates**: HTML con Tailwind CSS integrado
- **Static Assets**: CSS y JS organizados
- **Responsive Design**: Compatible con móviles y desktop

### 4. Configuration & Documentation
- **requirements.txt**: Dependencias Python
- **README.md**: Instrucciones completas de instalación
- **.env.example**: Plantilla de configuración

## Data Models

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Table
```sql
CREATE TABLE data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users (username)
);
```

### Key Changes from PostgreSQL:
- `SERIAL` → `INTEGER PRIMARY KEY AUTOINCREMENT`
- `BYTEA` → `BLOB`
- Añadidos timestamps para auditoría

## Error Handling

### Database Operations
```python
def with_db_connection(func):
    """Decorator para manejo seguro de conexiones DB"""
    def wrapper(*args, **kwargs):
        try:
            with sqlite3.connect('app.db') as conn:
                return func(conn, *args, **kwargs)
        except sqlite3.Error as e:
            app.logger.error(f"Database error: {e}")
            return None, str(e)
    return wrapper
```

### API Error Responses
- **400 Bad Request**: Datos de entrada inválidos
- **401 Unauthorized**: Usuario no autenticado
- **409 Conflict**: Usuario ya existe
- **500 Internal Server Error**: Errores del servidor

### Frontend Error Display
- Mensajes de error estilizados con Tailwind
- Validación de formularios en tiempo real
- Feedback visual para operaciones exitosas

## Testing Strategy

### Unit Tests
- **Database Operations**: Pruebas con base de datos en memoria
- **Crypto Functions**: Validación de encriptación/desencriptación
- **Route Handlers**: Pruebas de endpoints con datos mock

### Integration Tests
- **User Registration Flow**: Registro completo de usuario
- **Login/Logout Flow**: Autenticación completa
- **Data Save/Retrieve**: Flujo completo de datos encriptados

### Manual Testing Checklist
- Responsive design en diferentes dispositivos
- Funcionalidad sin JavaScript habilitado
- Manejo de errores de red
- Performance con datos grandes

## Security Considerations

### Encryption
- Mantener Fernet para encriptación simétrica
- Generar claves únicas por instalación
- Almacenamiento seguro de claves

### Session Management
- Secret key generada aleatoriamente
- Sessions con timeout apropiado
- Validación de sesión en cada request protegido

### Input Validation
- Sanitización de datos de entrada
- Validación de longitud de campos
- Protección contra SQL injection (usando parámetros)

## Performance Optimizations

### Database
- Índices en campos de búsqueda frecuente
- Connection pooling para múltiples requests
- Lazy loading de datos grandes

### Frontend
- Tailwind CSS via CDN para desarrollo
- Minificación de assets en producción
- Caching de recursos estáticos

## Deployment Strategy

### Development Setup
1. Clone repository
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python backend/src/app.py`

### Production Considerations
- Use environment variables for sensitive config
- Enable HTTPS
- Configure proper logging
- Database backups strategy

## Migration Path

### Phase 1: Database Migration
1. Create SQLite schema
2. Update database connection code
3. Test basic CRUD operations

### Phase 2: Code Improvements
1. Fix encryption/decryption bugs
2. Add proper error handling
3. Implement input validation

### Phase 3: Frontend Enhancement
1. Integrate Tailwind CSS
2. Create responsive templates
3. Add user feedback mechanisms

### Phase 4: Documentation & Testing
1. Create comprehensive README
2. Add requirements.txt
3. Test complete installation process