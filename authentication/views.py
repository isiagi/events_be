from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .auth import ClerkAuthentication

# Create your views here.

class VerifyTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [ClerkAuthentication]

    def post(self, request):
        try:
            # The authentication class will verify the token
            if hasattr(request.user, 'clerk_id'):
                return Response({
                    'valid': True,
                    'clerk_id': request.user.clerk_id
                })
            return Response({
                'valid': False
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
