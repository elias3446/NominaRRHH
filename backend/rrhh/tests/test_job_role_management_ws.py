import pytest
import json
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from core.asgi import application
from rrhh.models import CustomUser, Department, JobRole
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
import uuid

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestJobRoleManagementConsumer:
    
    async def _setup_admin(self):
        # Crear un usuario administrador para las pruebas
        self.admin = await self._create_user(f"admin_job_{uuid.uuid4().hex[:4]}@test.com", "admin123", role="service_role")
        self.token = str(AccessToken.for_user(self.admin))
        self.dept = await self._create_department("HR_DEPT")
        
    @database_sync_to_async
    def _create_user(self, email, password, role="authenticated"):
        user = CustomUser.objects.create_user(email=email, password=password, role=role)
        return user

    @database_sync_to_async
    def _create_department(self, name):
        return Department.objects.create(name=name, created_by=self.admin, updated_by=self.admin)

    @database_sync_to_async
    def _create_job_role(self, name, dept):
        return JobRole.objects.create(name=name, department=dept, created_by=self.admin, updated_by=self.admin)

    async def test_connect_authenticated(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(
            application, 
            "/ws/job-role-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_list_job_roles(self):
        await self._setup_admin()
        await self._create_job_role("Manager", self.dept)
        await self._create_job_role("Assistant", self.dept)
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/job-role-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({"action": "list"})
        response = await communicator.receive_json_from()
        
        assert response["status"] == "success"
        assert len(response["data"]) >= 2
        names = [r['name'] for r in response["data"]]
        assert "Manager" in names
        assert "Assistant" in names
        
        await communicator.disconnect()

    async def test_create_job_role(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(
            application, 
            "/ws/job-role-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        role_name = "New Role"
        await communicator.send_json_to({
            "action": "create",
            "data": {
                "name": role_name,
                "description": "Desc",
                "department": str(self.dept.id)
            }
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"]["name"] == role_name
        assert response["data"]["department"] == str(self.dept.id)
        
        await communicator.disconnect()

    async def test_update_job_role(self):
        await self._setup_admin()
        role = await self._create_job_role("Old Name", self.dept)
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/job-role-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({
            "action": "update",
            "data": {
                "id": str(role.id),
                "name": "New Name"
            }
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"]["name"] == "New Name"
        
        await communicator.disconnect()

    async def test_soft_delete_job_role(self):
        await self._setup_admin()
        role = await self._create_job_role("Delete Me", self.dept)
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/job-role-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({
            "action": "delete",
            "data": {"id": str(role.id)}
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"] == str(role.id)
        
        # Verificar soft delete
        @database_sync_to_async
        def check():
            r = JobRole.objects.get(id=role.id)
            assert r.deleted_at is not None
        await check()
        
        await communicator.disconnect()
