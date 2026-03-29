import os
import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Middleware personalizado para autenticar usuarios mediante JWT (SimpleJWT) en WebSockets.
    Prioriza headers (Authorization: Bearer <token>) si el cliente lo permite.
    Si no, el consumidor debe manejar la autenticación en el primer mensaje.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        token = None

        # 1. Priorizar Cookies (Navegador, Seguridad Máxima)
        headers = dict(scope.get("headers", []))
        if b"cookie" in headers:
            cookie_str = headers[b"cookie"].decode("utf-8")
            for cookie in cookie_str.split("; "):
                if cookie.startswith("access_token="):
                    token = cookie.split("=", 1)[1]
                    break

        # 2. Query param ?token=<jwt> (fallback para HTTP donde las cookies no viajan cross-origin)
        if not token:
            query_string = scope.get("query_string", b"").decode("utf-8")
            for param in query_string.split("&"):
                if param.startswith("token="):
                    token = param.split("=", 1)[1]
                    from urllib.parse import unquote
                    token = unquote(token)
                    break

        # 3. Header 'Authorization: Bearer <token>' (Clientes externos / REST)
        if not token and b"authorization" in headers:
            auth_header = headers[b"authorization"].decode("utf-8")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

        if token:
            try:
                access_token_obj = AccessToken(token)
                user_id = access_token_obj['user_id']
                scope['user'] = await get_user(user_id)
            except Exception as e:
                print(f"Error de autenticación JWT en WebSocket: {e}")
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
