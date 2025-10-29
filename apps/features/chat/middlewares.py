from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication Middleware for Channels.
    Accepts token via query string: ?token=...
    """

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        query_string = scope.get("query_string", b"").decode()
        token = None

        # get token from query string
        for param in query_string.split("&"):
            if param.startswith("token="):
                token = param.split("=")[1]
                break

        if token:
            try:
                jwt_auth = JWTAuthentication()
                # Validate token (sync to async)
                validated_token = await sync_to_async(jwt_auth.get_validated_token)(token)
                # Get user (sync to async)
                user = await sync_to_async(jwt_auth.get_user)(validated_token)
                scope["user"] = user
            except Exception as e:
                # Invalid token
                scope["user"] = AnonymousUser()
                print("JWT Middleware: Invalid token", e)

        return await super().__call__(scope, receive, send)
