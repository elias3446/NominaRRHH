from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender='rrhh.CustomUser')
def notify_new_user(sender, instance, created, **kwargs):
    """
    Señal de Django que se dispara cada vez que un usuario termina de guardarse en la DB. 
    Si el usuario es nuevo (created=True), enviamos el aviso a través de WebSockets.
    """
    if created:
        channel_layer = get_channel_layer()
        
        # 1. Notificación PÚBLICA (Segura, sin datos sensibles)
        async_to_sync(channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_created_notification',
                'message': "¡Un nuevo usuario se ha unido a NominaRRHH!",
                'user_data': None # No enviamos nada aquí
            }
        )
        
        # 2. Notificación para ADMINISTRADORES (Con todos los detalles)
        async_to_sync(channel_layer.group_send)(
            'admin_notifications',
            {
                'type': 'user_created_notification',
                'message': f"NUEVO REGISTRO: {instance.email}",
                'user_data': {
                    'id': str(instance.id),
                    'email': instance.email,
                    'role': instance.role
                }
            }
        )
