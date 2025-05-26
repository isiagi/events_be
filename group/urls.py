from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, debug_auth

router = DefaultRouter()
router.register(r'groups', GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('debug-auth/', debug_auth, name='debug-auth'),
]