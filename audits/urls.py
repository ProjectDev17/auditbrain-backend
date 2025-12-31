from rest_framework.routers import DefaultRouter
from .views import AuditViewSet

router = DefaultRouter()
router.register(r'audits', AuditViewSet, basename='audit')

urlpatterns = router.urls
