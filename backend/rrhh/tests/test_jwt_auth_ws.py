import uuid
import pytest
from unittest.mock import patch, MagicMock
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken
from core.asgi import application


def make_fake_user(email="ws_test@example.com"):
    """Crea un usuario falso sin BD (CustomUser tiene managed=False → auth.users Supabase)."""
    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()
    fake_user.email = email
    fake_user.is_anonymous = False
    fake_user.is_active = True
    return fake_user


def make_valid_token(user):
    """Genera un AccessToken de SimpleJWT con los claims del usuario falso."""
    token = AccessToken()
    token['user_id'] = str(user.id)
    token['email'] = user.email
    return str(token)


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_jwt_auth_websocket_cookie_success():
    """Verifica conexión exitosa con JWT en cabecera Cookie."""
    fake_user = make_fake_user("ws_cookie_success@example.com")
    valid_token = make_valid_token(fake_user)

    # Simulamos el Handshake con una Cookie
    headers = [(b"cookie", f"access_token={valid_token}".encode())]
    
    with patch('rrhh.middleware.jwt_middleware.get_user', return_value=fake_user):
        communicator = WebsocketCommunicator(application, "/ws/users/", headers=headers)
        connected, _ = await communicator.connect()
        assert connected, "La conexión debe ser aceptada con el token en la Cookie"
        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_jwt_auth_websocket_message_success():
    """Verifica autenticación exitosa enviando un mensaje JSON de tipo 'authenticate'."""
    fake_user = make_fake_user("ws_message_success@example.com")
    valid_token = make_valid_token(fake_user)

    # Conectamos inicialmente (middleware inicializa como Anónimo al no haber cookie/header)
    communicator = WebsocketCommunicator(application, "/ws/users/")
    connected, _ = await communicator.connect()
    assert connected

    with patch('rrhh.consumers.user_consumer.UserConsumer.get_user', return_value=fake_user):
        # Enviar mensaje de autenticación
        await communicator.send_json_to({
            "type": "authenticate",
            "token": valid_token
        })

        # Esperar respuesta de éxito
        response = await communicator.receive_json_from()
        assert response['type'] == 'auth_success'
        assert fake_user.email in response['message']
        
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_no_token_is_anonymous():
    """Verifica que conectar sin identificación resulta en AnonymousUser."""
    communicator = WebsocketCommunicator(application, "/ws/users/")
    connected, _ = await communicator.connect()
    assert connected, "Debe aceptarse la conexión anónima"
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_session_persistence_private_group():
    """
    Verifica que la persistencia en el grupo privado ocurre tras la autenticación por mensaje.
    """
    fake_user = make_fake_user("persistence_msg@example.com")
    valid_token = make_valid_token(fake_user)

    communicator = WebsocketCommunicator(application, "/ws/users/")
    await communicator.connect()

    with patch('rrhh.consumers.user_consumer.UserConsumer.get_user', return_value=fake_user):
        # Autenticar
        await communicator.send_json_to({"type": "authenticate", "token": valid_token})
        await communicator.receive_json_from() # auth_success

        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        # Enviar notificación al grupo privado del usuario (debe estar unido ahora)
        await channel_layer.group_send(
            f"user_{fake_user.id}",
            {
                "type": "user_created_notification",
                "message": "Persistencia lograda vía mensaje",
                "user_data": {"email": fake_user.email}
            }
        )

        response = await communicator.receive_json_from(timeout=3)
        assert response['type'] == 'user.created'
        assert response['message'] == "Persistencia lograda vía mensaje"

    await communicator.disconnect()
