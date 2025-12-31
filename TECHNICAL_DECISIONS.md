# Decisiones Técnicas - AuditBrain Backend

## Arquitectura

### Modelos Abstractos (DRY Principle)

Se implementaron tres modelos abstractos en `core/models.py`:

- **TimeStampedModel**: Añade `created_at` y `updated_at` automáticamente.
- **SoftDeleteModel**: Implementa borrado lógico con `deleted` y `deleted_by`.
- **AuditableModel**: Combina ambos y añade `created_by` y `updated_by`.

**Ventaja**: Cualquier modelo futuro puede heredar de `AuditableModel` y obtener toda la funcionalidad de auditoría sin duplicar código.

### Captura de Usuario (Thread-Local Pattern)

Se utilizó un middleware (`RequestUserMiddleware`) que almacena el usuario actual en `threading.local`, permitiendo acceso global sin pasar el usuario explícitamente en cada método.

**Alternativas consideradas**:

- Pasar `user` en cada llamada a `save()` → Verboso y propenso a errores.
- Usar `CurrentUserDefault` de DRF → Solo funciona en serializers, no en señales.

### Logging Desacoplado (MongoDB)

Se implementó un servicio Singleton (`MongoLogService`) que:

- Se conecta a MongoDB de forma lazy.
- Maneja errores de conexión gracefully (log warning, no crash).
- Es invocado desde señales (`post_save`, `post_delete`) para mantener la lógica de negocio limpia.

**Por qué señales**: Permiten interceptar operaciones de modelo sin modificar el código de negocio. Alternativa sería sobrescribir `save()` en cada modelo, pero es menos mantenible.

### Soft Delete

El método `delete()` de `SoftDeleteModel` marca `deleted=True` en lugar de eliminar el registro. El ViewSet filtra por `deleted=False` por defecto.

**Ventaja**: Permite auditoría completa y recuperación de datos.

## Decisiones de Testing

### Mocking de Usuario

Los tests mockean `get_current_user` en **dos lugares**:

- `core.models.get_current_user` (para el método `save()`)
- `audits.signals.get_current_user` (para las señales)

Esto es necesario porque Python importa funciones por referencia, y cada módulo tiene su propia copia.

### Base de Datos de Test

Django crea automáticamente una base de datos temporal para tests, garantizando aislamiento.

## Configuración de Entorno

### Docker Compose

Se definieron dos servicios:

- **db**: PostgreSQL 15 (base transaccional)
- **mongo**: MongoDB 6.0 (logs de auditoría)

### Variables de Entorno

Se usa `python-dotenv` para cargar `.env`, con fallbacks seguros en `settings.py`.

## Mejoras Futuras

- Implementar autenticación JWT con `djangorestframework-simplejwt`.
- Añadir filtros avanzados con `django-filter`.
- Implementar paginación cursor para grandes volúmenes.
- Añadir índices en MongoDB para queries de logs por `resource_id` y `timestamp`.
