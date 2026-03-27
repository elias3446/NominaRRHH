import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from core.asgi import application
from asgiref.sync import sync_to_async

User = get_user_model()

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_user_creation_broadcast():
    print("\n>>> INICIANDO TEST DE CONVERGENCIA CON ESQUEMA AUTH <<<")
    
    # Conectamos al WebSocket de notificaciones
    communicator = WebsocketCommunicator(application, "/ws/users/")
    connected, subprotocol = await communicator.connect()
    assert connected

    # Paso 1: Creamos un usuario de prueba (usando email como identificador según la Opción A)
    import uuid
    email_test = f"test_{uuid.uuid4().hex[:8]}@example.com"
    try:
        await sync_to_async(User.objects.create_user)(
            email=email_test, 
            password="password123"
        )
    except Exception as e:
        print(f"\n[!!!] ERROR AL CREAR USUARIO EN ESQUEMA AUTH: {str(e)}")
        raise e

    # Paso 2: Recibimos la respuesta del WebSocket
    response = await communicator.receive_json_from()

    # Paso 3: Validamos Convergencia
    assert response['type'] == 'user.created'
    assert email_test in response['message']
    assert response['user']['email'] == email_test

    # Cerramos la conexión
    await communicator.disconnect()
