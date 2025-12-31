from rest_framework_nested import routers
from .views import AuditViewSet, AuditEventViewSet, EvidenceViewSet

# Router principal
router = routers.DefaultRouter()
router.register(r'audits', AuditViewSet, basename='audit')

# Nested router para eventos
audits_router = routers.NestedDefaultRouter(router, r'audits', lookup='audit')
audits_router.register(r'events', AuditEventViewSet, basename='audit-events')
audits_router.register(r'evidences', EvidenceViewSet, basename='audit-evidences')

urlpatterns = router.urls + audits_router.urls
