from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIConversationViewSet

router = DefaultRouter()
router.register(r'ai-conversations', AIConversationViewSet, basename='ai-conversation')

urlpatterns = router.urls
