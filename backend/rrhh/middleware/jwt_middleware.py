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
            # Buscar 'access_token' dentro de la cadena de cookies
            for cookie in cookie_str.split("; "):
                if cookie.startswith("access_token="):
                    token = cookie.split("=")[1]
                    break

        # 2. Alternativa: Headers 'Authorization: Bearer <token>' (Clients externos)
        if not token and b"authorization" in headers:
            auth_header = headers[b"authorization"].decode("utf-8")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if token:
            try:
                # Validar el token usando rest_framework_simplejwt
                access_token_obj = AccessToken(token)
                user_id = access_token_obj['user_id']
                scope['user'] = await get_user(user_id)
            except Exception as e:
                print(f"Error de autenticación JWT en WebSocket: {e}")
                scope['user'] = AnonymousUser()
        else:
            # Si no hay token en headers, inicializamos como Anónimo.
            # El Consumidor podrá autenticar al usuario después si recibe un mensaje 'authenticate'.
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
