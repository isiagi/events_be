# authentication.py
import jwt
from jwt.jwks_client import PyJWKClient
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from functools import lru_cache

class ClerkAuthentication(authentication.BaseAuthentication):
    @lru_cache(maxsize=1)
    def get_jwks_client(self):
        return PyJWKClient(settings.CLERK_JWKS_URL)

    def authenticate(self, request):
        # Extract the JWT from the Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Get cached JWKS client
            jwks_client = self.get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Verify the JWT - Remove audience requirement since it's missing
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=settings.CLERK_ISSUER_URL,
                options={
                    "verify_signature": True,
                    "require_aud": False  # Don't require the audience claim
                }
            )

            print(f"Payload: {payload}")
            
            # Extract user information
            clerk_user_id = payload.get('sub')
            if not clerk_user_id:
                raise AuthenticationFailed('Invalid token payload')
            
            # Get or create a user in Django's system
            user, _ = User.objects.get_or_create(
                username=clerk_user_id,
                defaults={
                    'email': payload.get('email', ''),
                    'first_name': payload.get('given_name', ''),
                    'last_name': payload.get('family_name', '')
                }
            )
            
            # Store the raw token in request for potential use in views
            request.auth_token = token
            
            return (user, None)
            
        except jwt.InvalidTokenError as e:
            print(f"Invalid token error: {str(e)}")
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            print(f"Authentication exception: {str(e)}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')