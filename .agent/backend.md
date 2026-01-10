# Backend Development Guidelines - Django REST Framework

## Project Context

Este es un proyecto Django REST Framework (DRF) para AuditBrain, un sistema de gestión de auditorías.

## Tech Stack

- **Framework**: Django 4.x + Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT (SimpleJWT)
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

---

## DRF Best Practices

### Serializers

- Usar `ModelSerializer` para operaciones CRUD estándar
- Implementar `validate_<field>` para validaciones específicas de campo
- Usar `validate()` para validaciones cruzadas entre campos
- Definir explícitamente `read_only_fields` y `write_only_fields`
- Usar `SerializerMethodField` para campos computados
- Implementar `create()` y `update()` solo cuando sea necesario lógica personalizada

```python
class ExampleSerializer(serializers.ModelSerializer):
    computed_field = serializers.SerializerMethodField()

    class Meta:
        model = Example
        fields = ['id', 'name', 'computed_field']
        read_only_fields = ['id', 'created_at']

    def get_computed_field(self, obj):
        return obj.calculate_something()

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name too short")
        return value
```

### ViewSets & Views

- Usar `ModelViewSet` para CRUD completo
- Usar `@action` decorator para endpoints personalizados
- Implementar `get_queryset()` para filtrado dinámico
- Usar `get_serializer_class()` para diferentes serializers por acción
- Aplicar `permission_classes` apropiadamente

```python
class ExampleViewSet(viewsets.ModelViewSet):
    queryset = Example.objects.all()
    serializer_class = ExampleSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ExampleFilter

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(owner=self.request.user)
        return qs

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        instance = self.get_object()
        # Logic here
        return Response({'status': 'success'})
```

### Filtering & Pagination

- Usar `django-filter` para filtrado avanzado
- Configurar paginación global en settings
- Usar `SearchFilter` y `OrderingFilter` cuando aplique

```python
class ExampleFilter(django_filters.FilterSet):
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')

    class Meta:
        model = Example
        fields = ['status', 'type', 'created_after']
```

### Permissions

- Crear permisos personalizados cuando sea necesario
- Usar `has_permission` para permisos a nivel de vista
- Usar `has_object_permission` para permisos a nivel de objeto

```python
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
```

### Error Handling

- Usar `ValidationError` de DRF para errores de validación
- Implementar exception handlers personalizados si es necesario
- Retornar respuestas consistentes con códigos HTTP apropiados

### Testing

- Usar `APITestCase` para tests de API
- Usar `APIClient` para simular requests
- Testear serializers independientemente

---

## Code Style

### Naming Conventions

- **ViewSets**: `<Model>ViewSet`
- **Serializers**: `<Model>Serializer`, `<Model>CreateSerializer`, `<Model>ListSerializer`
- **Filters**: `<Model>Filter`
- **Permissions**: `Is<Condition>` o `Can<Action>`

### File Organization

```
app/
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── filters.py
├── permissions.py
├── signals.py
├── tasks.py (Celery)
└── tests/
    ├── test_models.py
    ├── test_serializers.py
    └── test_views.py
```

---

## Commit Guidelines

- Generar commits descriptivos después de cada cambio
- Usar conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Ejemplo: `feat(audits): add audit serializer and viewset`

---

## Translation

- Usar `django.utils.translation.gettext_lazy as _` para textos traducibles
- Aplicar en: labels, help_texts, error_messages
