# AuditBrain Backend

Backend API para gestión de auditorías construida con Django, Django Rest Framework, PostgreSQL y MongoDB.

## Requisitos

- Docker y Docker Compose
- Python 3.8+ (para desarrollo local)

## Configuración Rápida (Docker)

1. Clonar el repositorio.
2. Levantar los servicios:
   ```bash
   docker-compose up -d
   ```
3. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```
4. Crear superusuario:
   ```bash
   python manage.py createsuperuser
   ```
5. Iniciar servidor:
   ```bash
   python manage.py runserver
   ```
6. La API estará disponible en `http://localhost:8000/api/audits/`.

## Configuración Local (Sin Docker)

Si prefieres correrlo localmente sin Docker:

1. Crear entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   pip install -r requirements.txt
   ```
2. Configurar base de datos:
   - Edita `auditbrain/settings.py` y comenta la configuración de PostgreSQL.
   - Descomenta la configuración de SQLite.
3. Correr migraciones:
   ```bash
   python manage.py migrate
   ```
4. Correr servidor:
   ```bash
   python manage.py runserver
   ```

## Arquitectura

- **Core App**: Contiene modelos abstractos (`AuditableModel`) y servicios comunes (`MongoLogService`).
- **Audits App**: Contiene la lógica de negocio de auditorías.
- **Logging**:
  - Se utiliza **MongoDB** para almacenar logs de auditoría (Create, Update, Delete).
  - La lógica está desacoplada mediante Señales (`signals.py`) y un servicio dedicado.
  - El usuario actual se captura mediante un Middleware (`RequestUserMiddleware`) y `threading.local`.

## Testing

Para ejecutar los tests unitarios:

```bash
python manage.py test audits
```

Los tests verifican la creación de auditorías, el soft-delete y la correcta invocación del servicio de logging (mockeado).

## Verificación de MongoDB

Para verificar que MongoDB está funcionando:

```bash
python test_mongo_connection.py
```

Para ver los logs en MongoDB:

```bash
docker exec -it auditbrain_mongo mongosh
use auditbrain_logs
db.audit_logs.find().pretty()
```

## Documentación API

Se incluye una colección de Postman (`AuditBrain.postman_collection.json`) para probar los endpoints:

- `GET /api/audits/` - Listar auditorías
- `POST /api/audits/` - Crear auditoría
- `GET /api/audits/{id}/` - Obtener detalle
- `PATCH /api/audits/{id}/` - Actualizar auditoría
- `DELETE /api/audits/{id}/` - Eliminar (soft delete)

## Admin Panel

Acceder a `http://localhost:8000/admin/` con las credenciales del superusuario para gestionar auditorías desde la interfaz administrativa.

## Decisiones Técnicas

Ver `TECHNICAL_DECISIONS.md` para detalles sobre la arquitectura y decisiones de diseño.
