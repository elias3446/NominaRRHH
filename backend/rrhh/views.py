from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from rest_framework.response import Response

class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Inicia sesión y coloca los tokens en Cookies HttpOnly/Secure/SameSite.
    Soporta 'remember' para persistencia prolongada.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        remember = request.data.get('remember', False)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            # Si NO se marca 'Recordar', la cookie expira al cerrar el navegador (Session Cookie)
            # de lo contrario, usa el tiempo de vida definido en settings.
            access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()) if remember else None
            refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()) if remember else None

            # Colocar Access Token en Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                max_age=access_max_age,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            # Colocar Refresh Token en Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=refresh_token,
                max_age=refresh_max_age,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            # Actualizar last_sign_in_at y notificar WS
            email = request.data.get('email')
            if email:
                try:
                    from django.utils import timezone
                    from rrhh.models import CustomUser
                    from asgiref.sync import async_to_sync
                    from channels.layers import get_channel_layer
                    
                    user = CustomUser.objects.get(email=email)
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
                    
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'user_{user.id}',
                        {
                            'type': 'user_created_notification',
                            'message': 'Nuevo inicio de sesión detectado.',
                            'user_data': {
                                'email': user.email,
                                'last_sign_in_at': user.last_login.isoformat()
                            }
                        }
                    )
                except Exception as e:
                    print(f"Error actualizando last_login: {e}")
                    
        return response

class CookieTokenRefreshView(TokenRefreshView):
    """
    Renueva el Access Token usando el Refresh Token de la Cookie.
    """
    def post(self, request, *args, **kwargs):
        # Extraer el refresh token de la cookie y pasarlo como data mutable
        refresh_token_from_cookie = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token_from_cookie and 'refresh' not in request.data:
            # request.data puede ser inmutable (QueryDict), creamos copia mutable
            from rest_framework.request import Request
            request._full_data = {'refresh': refresh_token_from_cookie}
            
        response = super().post(request, *args, **kwargs)

        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            if refresh_token:
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                    value=refresh_token,
                    max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
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
            # Validación directa contra la base de datos: si no hay usuarios, este será el administrador
            from rrhh.models import CustomUser
            is_first_user = CustomUser.objects.count() == 0
            
            user = serializer.save()
            
            if is_first_user:
                user.role = 'service_role'
                user.is_super_admin = True
                user.save()
            
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
                max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            # Set Refresh Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=str(refresh),
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            from django.utils import timezone
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Notificar al cliente conectado sobre el inicio de sesión
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{user.id}',
                {
                    'type': 'user_created_notification',
                    'message': 'Bienvenido a NominaRRHH.',
                    'user_data': {
                        'email': user.email,
                        'last_sign_in_at': user.last_login.isoformat()
                    }
                }
            )
            
            # Set Refresh Cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=str(refresh),
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            
            return response
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.permissions import IsAuthenticated

class UserMeView(APIView):
    """
    Retorna los datos del usuario actual si está autenticado.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
        })
