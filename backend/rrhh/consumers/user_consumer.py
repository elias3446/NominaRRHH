import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class UserConsumer(AsyncWebsocketConsumer):
    """
    Consumidor de notificaciones en tiempo real.
    Ahora soporta autenticación segura vía mensaje interno para evitar tokens en la URL.
    """
    async def connect(self):
        # Aceptamos la conexión inicialmente (como Anónimo si no hay header)
        self.room_group_name = 'user_notifications'
        self.private_group_name = None
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Si el middleware detectó un usuario por Header, lo suscribimos de una vez
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            await self.subscribe_to_user_events(user)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')

            if msg_type == 'authenticate':
                token = data.get('token')
                await self.handle_manual_auth(token)
        except Exception as e:
            print(f"Error procesando mensaje WS: {e}")

    async def handle_manual_auth(self, token):
        if not token:
            return

        try:
            # Validar token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = await self.get_user(user_id)
            
            if user and not user.is_anonymous:
                self.scope['user'] = user
                await self.subscribe_to_user_events(user)
                await self.send(text_data=json.dumps({
                    'type': 'auth_success',
                    'message': f'Autenticado como {user.email}'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'auth_error',
                'message': 'Token inválido o expirado'
            }))

    async def subscribe_to_user_events(self, user):
        """Une al usuario a sus canales de notificaciones correspondientes."""
        
        # 1. Canal Privado Individual (user_{id})
        new_private_group = f'user_{user.id}'
        if self.private_group_name != new_private_group:
            if self.private_group_name:
                await self.channel_layer.group_discard(self.private_group_name, self.channel_name)
            
            self.private_group_name = new_private_group
            await self.channel_layer.group_add(
                self.private_group_name,
                self.channel_name
            )
            print(f"Suscripción exitosa a notificaciones privadas: {user.email}")

        # 2. Canal de Administradores (Solo si es Staff/Admin)
        if user.is_staff:
            await self.channel_layer.group_add(
                'admin_notifications',
                self.channel_name
            )
            print(f"Suscripción exitosa a canal de ADMINISTRADORES: {user.email}")

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        # Salir de grupos
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.private_group_name:
            await self.channel_layer.group_discard(self.private_group_name, self.channel_name)

    # Notificación enviada desde Django
    async def user_created_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user.created',
            'message': event['message'],
            'user': event['user_data']
        }))

    async def force_logout(self, event):
        """Cierra la sesión del usuario inmediatamente ante borrado o baneo."""
        await self.send(text_data=json.dumps({
            'type': 'force_logout',
            'message': event['message']
        }))
        # Cerramos el socket con código de política de violación o simplemente cerrar.
        await self.close(code=4003) 
