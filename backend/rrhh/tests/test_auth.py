import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from core.asgi import application
from rrhh.models.user_models import CustomUser


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_login_success():
    """
    Valida que el login vía WebSocket devuelve tokens JWT.
    Usa mock de authenticate_user para no depender de auth.users (managed=False).
    """
    test_email = f"test_{uuid.uuid4().hex[:6]}@swissport.com"
    test_pass = "password_segura_123"

    # Creamos un usuario real en la DB de pruebas (managed=False pero en SQLite se crea)
    fake_user = await sync_to_async(CustomUser.objects.create_user)(
        email=test_email,
        password=test_pass
    )

    with patch(
        'rrhh.consumers.auth_consumer.AuthConsumer.authenticate_user',
        new=AsyncMock(return_value=fake_user)
    ):
        communicator = WebsocketCommunicator(application, "/ws/auth/")
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_json_to({
            "type": "login",
            "email": test_email,
            "password": test_pass
        })

        response = await communicator.receive_json_from()

        assert response["status"] == "success"
        assert "auth_data" in response
        assert "access" in response["auth_data"]
        assert "refresh" in response["auth_data"]
        assert response["user"]["email"] == test_email

        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_login_failure():
    """
    Valida que el login falla con credenciales incorrectas.
    Usa mock de authenticate_user devolviendo None.
    """
    with patch(
        'rrhh.consumers.auth_consumer.AuthConsumer.authenticate_user',
        new=AsyncMock(return_value=None)
    ):
        communicator = WebsocketCommunicator(application, "/ws/auth/")
        connected, _ = await communicator.connect()
        assert connected

        await communicator.send_json_to({
            "type": "login",
            "email": "noexiste@error.com",
            "password": "wrong_password"
        })

        response = await communicator.receive_json_from()

        assert response["status"] == "error"
        assert "message" in response
        assert "auth_data" not in response

        await communicator.disconnect()
