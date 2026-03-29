import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from ..models.user_models import CustomUser
from ..models.job_role_models import JobRole
from ..serializers import JobRoleSerializer

class JobRoleManagementConsumer(AsyncWebsocketConsumer):
    """
    Consumidor WebSocket de tiempo real para Gestión de Cargos.
    Estructura robusta similar a Departamentos para sincronización instantánea y auditoría.
    """
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or self.user.is_anonymous:
            await self.close(code=403)
            return

        self.room_group_name = 'job_role_management_updates'
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
                await self.list_job_roles()
            elif action == 'create':
                await self.create_job_role(payload)
            elif action == 'update':
                await self.update_job_role(payload.get('id'), payload)
            elif action == 'delete':
                await self.delete_job_role(payload.get('id'))
            else:
                await self.send_error(f"Acción '{action}' no soportada")

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'detail'):
                 # Errores de validación de DRF serializados correctamente
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
    def _list_job_roles(self):
        # Listamos solo los cargos no borrados
        roles = JobRole.objects.filter(deleted_at__isnull=True).select_related(
            'department', 'created_by', 'updated_by'
        )
        # Nota: prefetch_related optimizado para información anidada
        return JobRoleSerializer(roles, many=True).data

    async def list_job_roles(self):
        data = await self._list_job_roles()
        await self.send_success('list', data)

    @database_sync_to_async
    def _create_job_role(self, data, user):
        serializer = JobRoleSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            role = serializer.save(created_by=user, updated_by=user)
            return JobRoleSerializer(role).data

    async def create_job_role(self, payload):
        try:
            data = await self._create_job_role(payload, self.user)
            await self.send_success('create', data)
            
            # Sincronización masiva con casting a tipos seguros de JSON para la capa de canales
            safe_data = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'job_role_update_event',
                    'action': 'job_role_created',
                    'data': safe_data
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def _update_job_role(self, role_id, data, user):
        role = JobRole.objects.get(id=role_id, deleted_at__isnull=True)
        serializer = JobRoleSerializer(role, data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            updated_role = serializer.save(updated_by=user, updated_at=timezone.now())
            return JobRoleSerializer(updated_role).data

    async def update_job_role(self, role_id, payload):
        try:
            data = await self._update_job_role(role_id, payload, self.user)
            await self.send_success('update', data)
            
            safe_data = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'job_role_update_event',
                    'action': 'job_role_updated',
                    'data': safe_data
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def _delete_job_role(self, role_id, user):
        role = JobRole.objects.get(id=role_id, deleted_at__isnull=True)
        role.soft_delete(user)
        return str(role.id)

    async def delete_job_role(self, role_id):
        try:
            id_deleted = await self._delete_job_role(role_id, self.user)
            await self.send_success('delete', id_deleted)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'job_role_update_event',
                    'action': 'job_role_deleted',
                    'data': {'id': id_deleted}
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    async def job_role_update_event(self, event):
        """Manejador de eventos grupales."""
        await self.send(text_data=json.dumps({
            'event': event['action'],
            'data': event['data']
        }, cls=DjangoJSONEncoder))
