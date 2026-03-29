import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from ..models.user_models import CustomUser
from ..models.profile_models import UserProfile
from ..serializers import UserDetailSerializer, UserRegistrationSerializer
from rest_framework.exceptions import ValidationError
from django.db import transaction

class UserManagementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        # Por ahora lo mantenemos sencillo, pero podríamos validar que el usuario sea admin
        if self.user.is_anonymous:
            await self.close(code=403)
            return

        self.room_group_name = 'user_management_updates'
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
                await self.list_users()
            elif action == 'get':
                await self.get_user(payload.get('id'))
            elif action == 'create':
                await self.create_user(payload)
            elif action == 'update':
                await self.update_user(payload.get('id'), payload)
            elif action == 'delete':
                await self.delete_user(payload.get('id'))
            else:
                await self.send_error("Acción no soportada")

        except json.JSONDecodeError:
            await self.send_error("Formato JSON inválido")
        except Exception as e:
            await self.send_error(str(e))

    async def send_error(self, message):
        await self.send(text_data=json.dumps({
            'status': 'error',
            'message': message
        }))

    async def send_success(self, action, data=None):
        response = {'status': 'success', 'action': action}
        if data is not None:
            response['data'] = data
        await self.send(text_data=json.dumps(response))

    @database_sync_to_async
    def _list_users(self, current_user_id):
        # Listamos solo los usuarios no borrados (logico)
        # EXCLUIMOS: Super administradores (por flag o rol) y el propio usuario logueado
        users = CustomUser.objects.filter(
            deleted_at__isnull=True
        ).exclude(
            id=current_user_id
        ).exclude(
            is_super_admin=True
        ).exclude(
            role='service_role'
        ).prefetch_related('profile')
        
        serializer = UserDetailSerializer(users, many=True)
        return serializer.data

    async def list_users(self):
        users_data = await self._list_users(self.user.id)
        await self.send_success('list', users_data)

    @database_sync_to_async
    def _get_user(self, user_id):
        try:
            user = CustomUser.objects.get(id=user_id, deleted_at__isnull=True)
            return UserDetailSerializer(user).data
        except CustomUser.DoesNotExist:
            return None

    async def get_user(self, user_id):
        if not user_id:
            return await self.send_error("ID de usuario requerido")
        
        user_data = await self._get_user(user_id)
        if user_data:
            await self.send_success('get', user_data)
        else:
            await self.send_error("Usuario no encontrado")

    @database_sync_to_async
    def _create_user(self, data):
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                
                # Configurar metadatos nativos del sistema en creación automática
                user.email_confirmed_at = timezone.now()
                user.raw_app_meta_data = {'provider': 'email', 'providers': ['email']}
                user.raw_user_meta_data = {}
                user.is_sso_user = False
                user.role = data.get('role', 'authenticated')
                user.save()
                
                return UserDetailSerializer(user).data
        raise ValidationError(serializer.errors)

    async def create_user(self, payload):
        try:
            user_data = await self._create_user(payload)
            await self.send_success('create', user_data)
            # Notificamos a todos los administradores del nuevo usuario
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_update_event',
                    'action': 'user_created',
                    'data': user_data
                }
            )
        except ValidationError as e:
            await self.send_error(e.detail)

    @database_sync_to_async
    def _update_user(self, user_id, data):
        try:
            user = CustomUser.objects.get(id=user_id, deleted_at__isnull=True)
            
            with transaction.atomic():
                save_user = False
                
                # Actualizar Email y trazar el cambio
                if 'email' in data and data['email'] != user.email:
                    user.email_change = user.email # Mantiene el antiguo por seguridad temporal
                    user.email_change_token_new = "pending_auto_token_email"
                    user.email_change_sent_at = timezone.now()
                    user.email = data['email']
                    user.email_confirmed_at = timezone.now() # Modificación aprobada por administrador, confirmación implícita
                    save_user = True
                
                # Teléfono (Manejo análogo)
                if 'phone' in data and data['phone'] != user.phone:
                    user.phone_change = user.phone
                    user.phone_change_token = "pending_auto_token_phone"
                    user.phone_change_sent_at = timezone.now()
                    user.phone = data['phone']
                    user.phone_confirmed_at = timezone.now()
                    save_user = True

                # Bloquear/Deshabilitar Usuarios (Enviando { banned_until: "2099-01-01T..." })
                if 'banned_until' in data:
                    user.banned_until = data['banned_until']
                    save_user = True

                # Contraseña (con log de recuperación/cambio)
                if 'password' in data:
                    user.set_password(data['password'])
                    user.recovery_sent_at = timezone.now()
                    save_user = True
                    
                # Rol y Permisos
                if 'role' in data:
                    user.role = data['role']
                    save_user = True
                    
                # Metadatos Raw
                if 'raw_app_meta_data' in data:
                    user.raw_app_meta_data = data['raw_app_meta_data']
                    save_user = True
                if 'raw_user_meta_data' in data:
                    user.raw_user_meta_data = data['raw_user_meta_data']
                    save_user = True
                if 'is_sso_user' in data:
                    user.is_sso_user = data['is_sso_user']
                    save_user = True

                if save_user:
                    user.updated_at = timezone.now()
                    user.save()

                # Actualizar perfil público de manera paralela
                if 'profile' in data:
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    profile_data = data['profile']
                    for key, value in profile_data.items():
                        if hasattr(profile, key):
                            setattr(profile, key, value)
                    profile.save()

            return UserDetailSerializer(user).data
        except CustomUser.DoesNotExist:
            raise ValueError("Usuario no encontrado")

    async def update_user(self, user_id, payload):
        if not user_id:
            return await self.send_error("ID de usuario requerido")
        try:
            user_data = await self._update_user(user_id, payload)
            await self.send_success('update', user_data)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_update_event',
                    'action': 'user_updated',
                    'data': user_data
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    @database_sync_to_async
    def _delete_user(self, user_id):
        try:
            user = CustomUser.objects.get(id=user_id, deleted_at__isnull=True)
            with transaction.atomic():
                # Borrado lógico para auth.users
                user.deleted_at = timezone.now()
                user.save()
                
                # Borrado físico para el Perfil en schema public (si existe)
                if hasattr(user, 'profile'):
                    user.profile.delete()
                
                # Sincronizar con Channels para forzar cierre de sesión en todos los dispositivos
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'user_{user_id}',
                    {
                        'type': 'force_logout',
                        'message': 'Tu cuenta ha sido desactivada por el administrador.'
                    }
                )
            return user_id
        except CustomUser.DoesNotExist:
            raise ValueError("Usuario no encontrado o ya eliminado")

    async def delete_user(self, user_id):
        if not user_id:
            return await self.send_error("ID de usuario requerido")
        try:
            deleted_id = await self._delete_user(user_id)
            await self.send_success('delete', {'id': deleted_id})
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_update_event',
                    'action': 'user_deleted',
                    'data': {'id': deleted_id}
                }
            )
        except Exception as e:
            await self.send_error(str(e))

    async def user_update_event(self, event):
        # Reenviar los cambios al WebSocket cliente
        await self.send(text_data=json.dumps({
            'event': event['action'],
            'data': event['data']
        }))
