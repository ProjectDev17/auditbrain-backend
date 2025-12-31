from rest_framework_nested import routers
from .views import AuditViewSet, AuditEventViewSet

# Router principal
router = routers.DefaultRouter()
router.register(r'audits', AuditViewSet, basename='audit')

# Nested router para eventos
audits_router = routers.NestedDefaultRouter(router, r'audits', lookup='audit')
audits_router.register(r'events', AuditEventViewSet, basename='audit-events')

urlpatterns = router.urls + audits_router.urls
