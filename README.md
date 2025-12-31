# AuditBrain Backend

Backend API para gestión de auditorías construida con Django, Django Rest Framework, PostgreSQL y MongoDB.

## Requisitos

- Docker y Docker Compose
- Python 3.8+ (opcional si se corre localmente sin Docker)

## Configuración Rápida (Docker)

1. Clonar el repositorio.
2. Crear un archivo `.env` basado en el ejemplo o dejar que Docker use los defaults.
3. Levantar los servicios:
   ```bash
   docker-compose up --build
   ```
4. La API estará disponible en `http://localhost:8000/api/audits/`.

## Configuración Local (Sin Docker)

Si Docker falla o prefieres correrlo localmente:

1. Crear entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   pip install -r requirements.txt
   ```
2. Configurar base de datos:
   - Por defecto, el proyecto está configurado para usar **SQLite** para facilitar pruebas rápidas.
   - Para usar PostgreSQL, descomenta la configuración en `auditbrain/settings.py` y asegura tener las variables de entorno configuradas.
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

## Documentación API

Se incluye una colección de Postman (`AuditBrain.postman_collection.json`) para probar los endpoints:

- `GET /api/audits/`
- `POST /api/audits/`
- `GET /api/audits/{id}/`
- `PATCH /api/audits/{id}/`
- `DELETE /api/audits/{id}/`
