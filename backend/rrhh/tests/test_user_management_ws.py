import pytest
import json
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from core.asgi import application
from rrhh.models import CustomUser, UserProfile
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestUserManagementConsumer:
    
    async def _setup_admin(self):
        # Crear un usuario administrador para las pruebas
        self.admin = await self._create_user("admin@test.com", "admin123", role="service_role")
        self.token = str(AccessToken.for_user(self.admin))
        
    @database_sync_to_async
    def _create_user(self, email, password, role="authenticated"):
        user = CustomUser.objects.create_user(email=email, password=password, role=role)
        UserProfile.objects.get_or_create(user=user, first_name="Test", last_name="User")
        return user

    async def test_connect_authenticated(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(
            application, 
            "/ws/user-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_list_users_filtering(self):
        """
        Verifica que la lista obtenida EXCLUYE:
        1. Al propio usuario que hace la petición.
        2. A todos los usuarios marcados como is_super_admin.
        """
        await self._setup_admin()
        # El administrador (self.admin) es un superadmin por setup_admin (service_role)
        
        # Creamos un usuario regular que SÍ debe aparecer
        regular = await self._create_user("regular@test.com", "SwissportAdmin2026!")
        
        # Creamos otro superadmin que NO debe aparecer
        other_admin = await self._create_user("other_admin@test.com", "SwissportAdmin2026!", role="service_role")
        await database_sync_to_async(lambda: CustomUser.objects.filter(id=other_admin.id).update(is_super_admin=True))()
        
        communicator = WebsocketCommunicator(application, "/ws/user-management/")
        communicator.scope['user'] = self.admin
        await communicator.connect()
        
        await communicator.send_json_to({"action": "list"})
        response = await communicator.receive_json_from()
        
        assert response["status"] == "success"
        users_list = response["data"]
        
        # Verificaciones de filtrado masivo
        email_list = [u['email'] for u in users_list]
        
        assert "regular@test.com" in email_list
        assert self.admin.email not in email_list
        assert "other_admin@test.com" not in email_list
        
        await communicator.disconnect()

    async def test_create_user(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(application, "/ws/user-management/")
        communicator.scope['user'] = self.admin
        await communicator.connect()
        await communicator.send_json_to({
            "action": "create",
            "data": {
                "email": "newuser@test.com",
                "password": "newpassword123",
                "role": "authenticated",
                "profile": {"first_name": "New", "last_name": "User"}
            }
        })
        while True:
            msg = await communicator.receive_json_from()
            if msg.get("status") == "success":
                break
        assert msg["action"] == "create"
        await communicator.disconnect()

    async def test_update_user(self):
        await self._setup_admin()
        target_user = await self._create_user("update_me@test.com", "password")
        communicator = WebsocketCommunicator(application, "/ws/user-management/")
        communicator.scope['user'] = self.admin
        await communicator.connect()
        await communicator.send_json_to({
            "action": "update",
            "data": {"id": str(target_user.id), "email": "updated@test.com"}
        })
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        await communicator.disconnect()

    async def test_delete_user_soft_invalidates_session(self):
        """
        Garantiza que el borrado lógico marca al usuario como inactivo
        y dispara el evento de desconexión masiva para cerrar todas sus sesiones.
        """
        await self._setup_admin()
        
        # El usuario victima tiene una sesión abierta
        victim = await self._create_user("victim@test.com", "SwissportAdmin2026!")
        victim_token = str(AccessToken.for_user(victim))
        
        victim_ws = WebsocketCommunicator(application, "/ws/users/") # UserConsumer
        connected, _ = await victim_ws.connect()
        assert connected
        
        # Autenticar manualmente para asegurar suscripción a grupos
        await victim_ws.send_json_to({
            "type": "authenticate",
            "token": victim_token
        })
        auth_res = await victim_ws.receive_json_from()
        assert auth_res["type"] == "auth_success"
        
        # El admin borra al usuario
        admin_ws = WebsocketCommunicator(application, "/ws/user-management/")
        admin_ws.scope['user'] = self.admin
        await admin_ws.connect()
        
        await admin_ws.send_json_to({
            "action": "delete",
            "data": {"id": str(victim.id)}
        })
        
        # El admin recibe éxito
        admin_res = await admin_ws.receive_json_from()
        assert admin_res["status"] == "success"
        
        # El usuario victima DEBE recibir el mensaje de force_logout por su canal personal
        victim_msg = await victim_ws.receive_json_from(timeout=5)
        assert victim_msg["type"] == "force_logout"
        
        # Y su objeto de usuario ya no debe estar activo
        @database_sync_to_async
        def check_status():
            from django.db import connection
            connection.close() # Forzar refresco
            u = CustomUser.objects.get(id=victim.id)
            assert u.is_active is False
        
        await check_status()
        
        await admin_ws.disconnect()
        await victim_ws.disconnect()
