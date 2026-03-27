import json
from channels.generic.websocket import AsyncWebsocketConsumer

class UserConsumer(AsyncWebsocketConsumer):
    """
    Este "Consumidor" es como un controlador que escucha las conexiones de WebSockets. 
    Se encarga de notificar en tiempo real cuando un usuario es creado.
    """
    async def connect(self):
        # Creamos una sala o grupo común para todos los usuarios interesados en actualizaciones
        self.room_group_name = 'user_notifications'

        # Unirse al grupo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo al desconectarse
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Este método recibe el evento del servidor y lo envía al Frontend (React)
    async def user_created_notification(self, event):
        message = event['message']
        user_data = event['user_data']

        # Enviar mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user.created',
            'message': message,
            'user': user_data
        }))
