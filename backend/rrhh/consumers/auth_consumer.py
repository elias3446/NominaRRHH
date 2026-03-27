import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from channels.db import database_sync_to_async

User = get_user_model()

class AuthConsumer(AsyncWebsocketConsumer):
    """
    Fábrica de Identidad vía WebSockets (Login/Logout estilo Supabase).
    Permite iniciar sesión, revocar tokens y autenticar sesiones existentes.
    """
    async def connect(self):
        # Aceptamos la conexión abierta, el usuario debe identificarse después
        await self.accept()
        
        # Si el middleware detectó un usuario por Header, lo guardamos
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            print(f"Sesión Auth reactivada vía Header: {user.email}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')

            if msg_type == 'login':
                await self.handle_login(data)
            elif msg_type == 'authenticate':
                await self.handle_manual_auth(data.get('token'))
            elif msg_type == 'logout':
                await self.handle_logout(data)
            elif msg_type == 'get_session':
                await self.handle_get_session()
        except Exception as e:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': f'Error procesando mensaje: {str(e)}'
            }))

    async def handle_manual_auth(self, token):
        """Identifica al usuario usando un token de acceso válido."""
        if not token:
            return

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = await self.get_user_by_id(user_id)
            
            if user:
                self.scope['user'] = user
                await self.send(text_data=json.dumps({
                    'status': 'success',
                    'type': 'auth_response',
                    'message': f'Sesión autenticada para {user.email}',
                    'user': {'id': str(user.id), 'email': user.email}
                }))
        except Exception:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'type': 'auth_response',
                'message': 'Token de sesión inválido o expirado'
            }))

    async def handle_get_session(self):
        """Devuelve el usuario actual en la sesión del socket."""
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            await self.send(text_data=json.dumps({
                'status': 'success',
                'type': 'session_data',
                'user': {'id': str(user.id), 'email': user.email}
            }))
        else:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'type': 'session_data',
                'message': 'No hay sesión activa'
            }))

    async def handle_login(self, data):
        email = data.get('email')
        password = data.get('password')

        user = await self.authenticate_user(email, password)
        if user:
            self.scope['user'] = user # Guardar en el socket
            tokens = await self.get_tokens_for_user(user)
            await self.send(text_data=json.dumps({
                'status': 'success',
                'type': 'login_response',
                'message': 'Inicio de sesión exitoso',
                'auth_data': tokens,
                'user': {'id': str(user.id), 'email': user.email}
            }))
        else:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'type': 'login_response',
                'message': 'Credenciales de Swissport incorrectas'
            }))

    async def handle_logout(self, data):
        refresh_token = data.get('refresh')
        if not refresh_token:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Se requiere un Refresh Token para cerrar sesión'
            }))
            return

        success = await self.blacklist_token(refresh_token)
        if success:
            self.scope['user'] = None
            await self.send(text_data=json.dumps({
                'status': 'success',
                'type': 'logout_response',
                'message': 'Sesión cerrada correctamente.'
            }))
        else:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Token inválido o ya revocado'
            }))

    @database_sync_to_async
    def authenticate_user(self, email, password):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @database_sync_to_async
    def blacklist_token(self, refresh_token):
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return True
        except Exception:
            return False
