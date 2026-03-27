import pytest
import uuid
from unittest.mock import MagicMock
from channels.testing import WebsocketCommunicator
from core.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_user_creation_broadcast():
    """
    Verifica que se emite una notificación 'user.created' al grupo WebSocket.
    Simula directamente el evento de channel_layer en lugar de crear usuarios
    reales en auth.users (managed=False, tabla de Supabase).
    """
    communicator = WebsocketCommunicator(application, "/ws/users/")
    connected, subprotocol = await communicator.connect()
    assert connected

    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()

    email_test = f"test_{uuid.uuid4().hex[:8]}@example.com"

    await channel_layer.group_send(
        "user_notifications",
        {
            "type": "user_created_notification",
            "message": f"Nuevo usuario registrado: {email_test}",
            "user_data": {"email": email_test, "id": str(uuid.uuid4())}
        }
    )

    response = await communicator.receive_json_from(timeout=3)

    assert response['type'] == 'user.created'
    assert email_test in response['message']
    assert response['user']['email'] == email_test

    await communicator.disconnect()
