import pytest
from rest_framework.test import APIClient
from rrhh.models import CustomUser
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestUserRegistration:
    def setup_method(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        CustomUser.objects.all().delete()
    
    @patch('rrhh.views.get_channel_layer')
    def test_first_user_is_super_admin(self, mock_get_channel_layer):
        """
        Verifica que el primer usuario registrado en la base de datos se crea 
        automáticamente con role='service_role' y is_super_admin=True, además
        de notificar vía WebSockets y actualizar last_login.
        """
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer
        
        # Asegurarnos de que no hay usuarios
        assert CustomUser.objects.count() == 0
        
        # Registrar al primer usuario
        payload_1 = {
            "email": "first_user@test.com",
            "password": "strongpassword123",
            "password_confirm": "strongpassword123"
        }
        
        response_1 = self.client.post(self.register_url, payload_1, format='json')
        assert response_1.status_code == 201
        
        # Verificar que se crearon los privilegios y fecha de conexión
        first_user = CustomUser.objects.get(email="first_user@test.com")
        assert first_user.role == 'service_role', "El primer usuario debe tener el rol 'service_role'"
        assert first_user.is_super_admin is True, "El primer usuario debe ser is_super_admin=True"
        assert first_user.is_staff is True
        assert first_user.is_superuser is True
        assert first_user.last_login is not None, "Debe actualizarse el last_login (last_sign_in_at)"
        
        # Verificar WebSockets Notification
        mock_channel_layer.group_send.assert_called_once()
        args, kwargs = mock_channel_layer.group_send.call_args
        assert args[0] == f'user_{first_user.id}'
        assert args[1]['type'] == 'user_created_notification'
        assert args[1]['user_data']['email'] == first_user.email

    @patch('rrhh.views.get_channel_layer')
    def test_second_user_is_regular_user(self, mock_get_channel_layer):
        """
        Verifica que el segundo usuario registrado en adelante se crea
        con privilegios normales ('authenticated', is_super_admin=False).
        """
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        # Intervenir la BD creando el "primer usuario"
        CustomUser.objects.create_user(email="first_admin@test.com", password="adminpassword")
        assert CustomUser.objects.count() == 1
        
        # Registrar al SEGUNDO usuario
        payload_2 = {
            "email": "second_user@test.com",
            "password": "normalpassword123",
            "password_confirm": "normalpassword123"
        }
        
        response_2 = self.client.post(self.register_url, payload_2, format='json')
        assert response_2.status_code == 201
        
        # Verificar que este NO tiene privilegios
        second_user = CustomUser.objects.get(email="second_user@test.com")
        assert second_user.role == 'authenticated', "El segundo usuario debe tener rol normal 'authenticated'"
        assert second_user.is_super_admin is False, "El segundo usuario NO debe ser super admin"
        assert second_user.is_staff is False
        assert second_user.is_superuser is False
        assert second_user.last_login is not None
        
        # Verificar WebSockets Notification
        mock_channel_layer.group_send.assert_called_once()
