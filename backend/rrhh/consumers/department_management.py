import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from ..models.user_models import CustomUser
from ..models.department_models import Department
from ..serializers import DepartmentSerializer

class DepartmentManagementConsumer(AsyncWebsocketConsumer):
    """
    Consumidor WebSocket de tiempo real para Gestión de Departamentos.
    Maneja el ciclo de vida CRUD con sincronización masiva a todos los administradores.
    """
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or self.user.is_anonymous:
            await self.close(code=403)
            return

        self.room_group_name = 'department_management_updates'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            payload = data.get('data', {})

            if action == 'list':
                await self.list_departments()
            elif action == 'create':
                await self.create_department(payload)
            elif action == 'update':
                await self.update_department(payload.get('id'), payload)
            elif action == 'delete':
                await self.delete_department(payload.get('id'))
            else:
                await self.send_error(f"Acción '{action}' no soportada")

        except Exception as e:
            # Capturamos errores de validación de DRH si ocurren
            error_msg = str(e)
            if hasattr(e, 'detail'):
                error_msg = json.dumps(e.detail, cls=DjangoJSONEncoder)
            await self.send_error(error_msg)

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'status': 'error',
            'message': message
        }, cls=DjangoJSONEncoder))

    async def send_success(self, action, data=None):
        response = {'status': 'success', 'action': action}
        if data is not None:
            response['data'] = data
        await self.send(text_data=json.dumps(response, cls=DjangoJSONEncoder))

    @database_sync_to_async
    def _list_departments(self):
        # Listamos solo los no borrados lógicamente
        departments = Department.objects.filter(deleted_at__isnull=True).prefetch_related('created_by', 'updated_by')
        return DepartmentSerializer(departments, many=True).data

    async def list_departments(self):
        data = await self._list_departments()
        await self.send_success('list', data)

    @database_sync_to_async
    def _create_department(self, data, user):
        from ..serializers import JobRoleSerializer
        
        serializer = DepartmentSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            department = serializer.save(created_by=user, updated_by=user)
            department_data = DepartmentSerializer(department).data
            
            # Extraer cargos creados (ver DepartmentSerializer create)
            created_roles = getattr(department, '_created_roles', [])
            roles_data = JobRoleSerializer(created_roles, many=True).data if created_roles else []
            
            return department_data, roles_data

    async def create_department(self, payload):
        try:
            data, roles_data = await self._create_department(payload, self.user)
            await self.send_success('create', data)
            
            # Aseguramos que data sea serializable para la capa de canales (Redis)
            safe_data = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
            
            # Notificamos a todos de la creación del depto
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'department_update_event',
                    'action': 'department_created',
                    'data': safe_data
                }
            )
            
            # Emitir eventos para los nuevos cargos creados junto con el depto
            if roles_data:
                for role_data in roles_data:
                    safe_role = json.loads(json.dumps(role_data, cls=DjangoJSONEncoder))
                    await self.channel_layer.group_send(
                        'job_role_management_updates',
                        {
                            'type': 'job_role_update_event',
                            'action': 'job_role_created',
                            'data': safe_role
                        }
                    )
        except Exception as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def _update_department(self, dept_id, data, user):
        dept = Department.objects.get(id=dept_id, deleted_at__isnull=True)
        serializer = DepartmentSerializer(dept, data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            department = serializer.save(updated_by=user, updated_at=timezone.now())
            return DepartmentSerializer(department).data

    async def update_department(self, dept_id, payload):
        try:
            data = await self._update_department(dept_id, payload, self.user)
            await self.send_success('update', data)
            
            safe_data = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'department_update_event',
                    'action': 'department_updated',
                    'data': safe_data
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def _delete_department(self, dept_id, user):
        dept = Department.objects.get(id=dept_id, deleted_at__isnull=True)
        dept.soft_delete(user)
        return str(dept.id)

    async def delete_department(self, dept_id):
        try:
            id_deleted = await self._delete_department(dept_id, self.user)
            await self.send_success('delete', id_deleted)
            
            # id_deleted ya es un string (ver _delete_department)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'department_update_event',
                    'action': 'department_deleted',
                    'data': {'id': id_deleted}
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    async def department_update_event(self, event):
        """Manejador de eventos grupales."""
        await self.send(text_data=json.dumps({
            'event': event['action'],
            'data': event['data']
        }, cls=DjangoJSONEncoder))
