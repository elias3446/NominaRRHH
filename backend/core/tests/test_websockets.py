import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from core.asgi import application
from asgiref.sync import sync_to_async

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_user_creation_broadcast():
    """
    PRUEBA DE CONVERGENCIA: 
    1. Abre una conexión WebSocket.
    2. Crea un usuario en la Base de Datos.
    3. Verifica que el servidor envíe automáticamente la notificación por el socket.
    """
    # Conectamos al WebSocket de notificaciones
    communicator = WebsocketCommunicator(application, "/ws/users/")
    connected, subprotocol = await communicator.connect()
    assert connected

    # Paso 1: Creamos un usuario de prueba con nombre único para evitar duplicados
    import uuid
    username = f"test_user_{uuid.uuid4().hex[:8]}"
    await sync_to_async(User.objects.create_user)(
        username=username, 
        email=f"{username}@example.com", 
        password="password123"
    )

    # Paso 2: Recibimos la respuesta del WebSocket
    response = await communicator.receive_json_from()

    # Paso 3: Validamos Convergencia (Mensaje esperado vs Mensaje recibido)
    assert response['type'] == 'user.created'
    assert username in response['message']
    assert response['user']['username'] == username

    # Cerramos la conexión
    await communicator.disconnect()
