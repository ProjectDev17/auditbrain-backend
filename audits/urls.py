from rest_framework_nested import routers
from .views import AuditViewSet, AuditEventViewSet, EvidenceViewSet, GlobalAuditEventViewSet, GlobalEvidenceViewSet, AuditEvidenceViewSet, AuditTypeViewSet
from authentication.views import UserViewSet, GroupViewSet, PermissionViewSet

# Router principal
router = routers.DefaultRouter()
router.register(r'audits', AuditViewSet, basename='audit')
router.register(r'audit-types', AuditTypeViewSet, basename='audit-type')
router.register(r'events', GlobalAuditEventViewSet, basename='global-events')
router.register(r'evidences', GlobalEvidenceViewSet, basename='global-evidences')
router.register(r'audit-evidences', AuditEvidenceViewSet, basename='audit-evidence')
router.register(r'users', UserViewSet, basename='user')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'permissions', PermissionViewSet, basename='permission')

# Nested router para eventos
audits_router = routers.NestedDefaultRouter(router, r'audits', lookup='audit')
audits_router.register(r'events', AuditEventViewSet, basename='audit-events')
audits_router.register(r'evidences', EvidenceViewSet, basename='audit-evidences')

urlpatterns = router.urls + audits_router.urls
