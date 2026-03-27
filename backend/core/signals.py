from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender=User)
def notify_new_user(sender, instance, created, **kwargs):
    """
    Señal de Django que se dispara cada vez que un usuario termina de guardarse en la DB. 
    Si el usuario es nuevo (created=True), enviamos el aviso a través de WebSockets.
    """
    if created:
        channel_layer = get_channel_layer()
        
        # Enviar mensaje a todo el grupo 'user_notifications'
        async_to_sync(channel_layer.group_send)(
            'user_notifications',
            {
                'type': 'user_created_notification',
                'message': f"¡Se ha creado un nuevo usuario: {instance.username}!",
                'user_data': {
                    'id': instance.id,
                    'username': instance.username,
                    'email': instance.email
                }
            }
        )
