import pytest
from rest_framework.test import APIClient
from rrhh.models import CustomUser, UserProfile
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestUserRegistration:
    def setup_method(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        CustomUser.objects.all().delete()
    
    def test_first_user_is_super_admin(self):
        """
        Verifica que el primer usuario registrado se crea con privilegios de super admin,
        un perfil asociado y se envía la notificación por WebSocket.
        """
        # Patching inside the test for better control
        with patch('channels.layers.get_channel_layer') as mock_get_channel_layer, \
             patch('asgiref.sync.async_to_sync') as mock_async_to_sync:
            
            mock_channel_layer = MagicMock()
            mock_get_channel_layer.return_value = mock_channel_layer
            mock_async_to_sync.side_effect = lambda x: x
            
            payload = {
                "email": "admin_test@test.com",
                "password": "SwissportAdmin2026!",
                "password_confirm": "SwissportAdmin2026!"
            }
            
            response = self.client.post(self.register_url, payload, format='json')
            assert response.status_code == 201
            
            user = CustomUser.objects.get(email="admin_test@test.com")
            assert user.role == 'service_role'
            assert user.is_super_admin is True
            assert UserProfile.objects.filter(user=user).exists()
            
            # WebSocket Check
            assert mock_channel_layer.group_send.called

    def test_second_user_is_regular_user(self):
        """
        Verifica que el segundo usuario registrado tiene el rol estándar 'authenticated'.
        """
        with patch('channels.layers.get_channel_layer') as mock_get_channel_layer, \
             patch('asgiref.sync.async_to_sync') as mock_async_to_sync:
            
            mock_channel_layer = MagicMock()
            mock_get_channel_layer.return_value = mock_channel_layer
            mock_async_to_sync.side_effect = lambda x: x

            # Crear el primer admin manual
            CustomUser.objects.create_user(email="first_admin@test.com", password="password")
            
            payload = {
                "email": "regular@test.com",
                "password": "SwissportAdmin2026!",
                "password_confirm": "SwissportAdmin2026!"
            }
            
            response = self.client.post(self.register_url, payload, format='json')
            assert response.status_code == 201
            
            user = CustomUser.objects.get(email="regular@test.com")
            assert user.role == 'authenticated'
            assert user.is_super_admin is False
