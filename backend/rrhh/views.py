from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from rest_framework.response import Response

class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Inicia sesión y coloca los tokens en Cookies HttpOnly/Secure/SameSite.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            # Colocar Access Token en Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            # Colocar Refresh Token en Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=refresh_token,
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            # (Opcional) Limpiar los tokens del JSON de respuesta para mayor "purismo" de cookies
            # del response.data['access']
            # del response.data['refresh']
            
        return response

class CookieTokenRefreshView(TokenRefreshView):
    """
    Renueva el Access Token usando el Refresh Token de la Cookie.
    """
    def post(self, request, *args, **kwargs):
        # Si no viene token en el body, lo buscamos en cookies
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token:
            request.data['refresh'] = refresh_token
            
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
        return response

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

class CookieLogoutView(APIView):
    """
    Cierra la sesión persistente:
    1. Invalida el Refresh Token en la base de datos (Blacklist).
    2. Borra las Cookies del navegador.
    """
    def post(self, request):
        response = Response({"status": "success", "message": "Sesión cerrada correctamente"})
        
        # 1. Obtener y Blacklist el Refresh Token
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass # El token ya estaba en blacklist o era inválido
        
        # 2. Borrar las Cookies del navegador enviándolas vacías y caducadas
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        
        return response

from rrhh.serializers import UserRegistrationSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny

class UserRegistrationView(APIView):
    """
    Registra un nuevo usuario y, si es exitoso, inicia sesión automáticamente (Cookies).
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generar Tokens para inicio de sesión inmediato
            refresh = RefreshToken.for_user(user)
            
            # Crear Respuesta con Cookies
            response = Response({
                "status": "success", 
                "message": "Usuario registrado exitosamente e inicio de sesión automático",
                "user": {"id": str(user.id), "email": user.email}
            }, status=status.HTTP_201_CREATED)
            
            # Set Access Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=str(refresh.access_token),
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            # Set Refresh Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=str(refresh),
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            return response
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
