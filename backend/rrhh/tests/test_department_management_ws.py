import pytest
import json
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from core.asgi import application
from rrhh.models import CustomUser, Department
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
import uuid

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestDepartmentManagementConsumer:
    
    async def _setup_admin(self):
        # Crear un usuario administrador para las pruebas
        self.admin = await self._create_user("admin_dept@test.com", "admin123", role="service_role")
        self.token = str(AccessToken.for_user(self.admin))
        
    @database_sync_to_async
    def _create_user(self, email, password, role="authenticated"):
        user = CustomUser.objects.create_user(email=email, password=password, role=role)
        return user

    @database_sync_to_async
    def _create_department(self, name, description="Test Desc"):
        return Department.objects.create(name=name, description=description, created_by=self.admin, updated_by=self.admin)

    async def test_connect_authenticated(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_list_departments(self):
        await self._setup_admin()
        await self._create_department("DEPT1")
        await self._create_department("DEPT2")
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({"action": "list"})
        response = await communicator.receive_json_from()
        
        assert response["status"] == "success"
        assert len(response["data"]) >= 2
        names = [d['name'] for d in response["data"]]
        assert "DEPT1" in names
        assert "DEPT2" in names
        
        await communicator.disconnect()

    async def test_create_department(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        new_name = f"NEW_DEPT_{uuid.uuid4().hex[:6]}"
        await communicator.send_json_to({
            "action": "create",
            "data": {
                "name": new_name,
                "description": "New description"
            }
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"]["name"] == new_name
        
        await communicator.disconnect()

    async def test_update_department(self):
        await self._setup_admin()
        dept = await self._create_department("UPDATE_ME")
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({
            "action": "update",
            "data": {
                "id": str(dept.id),
                "name": "I_AM_UPDATED"
            }
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"]["name"] == "I_AM_UPDATED"
        
        await communicator.disconnect()

    async def test_soft_delete_department(self):
        await self._setup_admin()
        dept = await self._create_department("DELETE_ME")
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({
            "action": "delete",
            "data": {"id": str(dept.id)}
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"] == str(dept.id)
        
        # Verificar en DB que está borrado lógicamente
        @database_sync_to_async
        def check_soft_delete():
            d = Department.objects.get(id=dept.id)
            assert d.deleted_at is not None
            assert d.deleted_by == self.admin
            
        await check_soft_delete()
        await communicator.disconnect()

    async def test_duplicate_name_error(self):
        await self._setup_admin()
        await self._create_department("EXISTING")
        
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        await communicator.send_json_to({
            "action": "create",
            "data": {"name": "EXISTING"}
        })
        
        response = await communicator.receive_json_from()
        assert response["status"] == "error"
        assert "EXISTING" in response["message"] or "nombre" in response["message"].lower() or "exists" in response["message"].lower()
        
        await communicator.disconnect()

    async def test_create_department_with_job_roles(self):
        await self._setup_admin()
        communicator = WebsocketCommunicator(
            application, 
            "/ws/department-management/",
            headers=[(b"cookie", f"access_token={self.token}".encode())]
        )
        communicator.scope['user'] = self.admin
        connected, _ = await communicator.connect()
        assert connected
        
        new_name = f"DEPT_WITH_ROLES_{uuid.uuid4().hex[:6]}"
        await communicator.send_json_to({
            "action": "create",
            "data": {
                "name": new_name,
                "description": "Department that has roles",
                "job_roles": [
                    {"name": "Manager", "description": "Líder de pruebas"},
                    {"name": "Analyst", "description": "Analista de pruebas"}
                ]
            }
        })
        
        # El create envía la confirmación status: success
        response = await communicator.receive_json_from()
        assert response["status"] == "success"
        assert response["data"]["name"] == new_name
        
        # Verificar en base de datos si se crearon y relacionaron los job roles
        @database_sync_to_async
        def check_job_roles():
            from rrhh.models import JobRole
            dept = Department.objects.get(name=new_name)
            roles = JobRole.objects.filter(department=dept)
            assert roles.count() == 2
            assert set([r.name for r in roles]) == {"Manager", "Analyst"}
            
        await check_job_roles()
        await communicator.disconnect()
