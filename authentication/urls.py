from django.urls import path
from .views import VerifyTokenView

urlpatterns = [
    path('verify/', VerifyTokenView.as_view(), name='verify-token'),
] 