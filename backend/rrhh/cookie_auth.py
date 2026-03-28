from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    Extiende JWTAuthentication para leer el Access Token desde la Cookie HttpOnly
    en lugar del header 'Authorization: Bearer <token>'.
    
    Prioridad:
      1. Cookie 'access_token' (navegador con HttpOnly)
      2. Header 'Authorization: Bearer <token>' (clientes externos / Postman)
    """

    def authenticate(self, request):
        # 1. Intentar leer desde la cookie HttpOnly
        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)

        if raw_token:
            try:
                validated_token = self.get_validated_token(raw_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception:
                # Si la cookie existe pero el token es inválido/expirado,
                # no caemos al header — dejamos que el interceptor de frontend
                # maneje el refresh. Retornamos None para que DRF devuelva 401.
                return None

        # 2. Fallback: leer desde el header Authorization (para APIs externas)
        return super().authenticate(request)
