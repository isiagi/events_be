import jwt
import requests
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

    def get_clerk_user_info(self, user_id):
        # print(f"Fetching user info for user ID: {user_id}")
        headers = {
            "Authorization": f"Bearer {settings.CLERK_API_KEY}"
        }
        url = f"{settings.CLERK_API_BASE_URL}/users/{user_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise AuthenticationFailed("Failed to fetch user info from Clerk")
        return response.json()

    def authenticate(self, request):

        # print("Incoming request headers:", dict(request.headers))

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            jwks_client = self.get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=settings.CLERK_ISSUER_URL,
                options={
                    "verify_signature": True,
                    "require_aud": False
                }
            )

            clerk_user_id = payload.get('sub')
            if not clerk_user_id:
                raise AuthenticationFailed('Invalid token payload')

            # 🔄 Fetch full user info from Clerk
            user_info = self.get_clerk_user_info(clerk_user_id)

            # print(f"User info: {user_info}")

            email = user_info.get('email_addresses', [{}])[0].get('email_address', '')
            first_name = user_info.get('first_name') or ''
            last_name = user_info.get('last_name') or ''
            user_image = user_info.get('image_url', '')


            # print(f"User ID: {clerk_user_id}")
            # print(f"User Email: {email}")
            # print(f"User Name: {first_name} {last_name}")
            # print(f"User Image: {user_image}")
            

            # 👤 Get or create the Django user
            user, _ = User.objects.get_or_create(
                username=clerk_user_id,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    # 'user_image': user_image
                }
            )

            # 🚀 Update the user's information
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            # user.user_image = user_image

            try:
                user.save()
            except Exception as e:
                print("Error saving user:", str(e))
                raise AuthenticationFailed("User creation failed")

            # print(f"User ID: {user.username}")
            # print(f"User Email: {user.email}")
            # print(f"User Name: {user.first_name} {user.last_name}")
            # print(f"User Image: {user.user_image}")

            request.auth_token = token
            return (user, None)

        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
