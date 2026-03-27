"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
<<<<<<< Updated upstream

from django.core.asgi import get_asgi_application
=======
import django
from channels.routing import ProtocolTypeRouter, URLRouter
>>>>>>> Stashed changes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.asgi import get_asgi_application
from django.urls import path
from rrhh.middleware import JWTAuthMiddlewareStack  # Nuevo middleware por tokens
from rrhh.consumers.user_consumer import UserConsumer
from rrhh.consumers.auth_consumer import AuthConsumer

<<<<<<< Updated upstream
application = get_asgi_application()
=======
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddlewareStack(  # Cambiado para soportar JWT (estilo Supabase)
        URLRouter([
            path("ws/users/", UserConsumer.as_asgi()),
            path("ws/auth/", AuthConsumer.as_asgi()),
        ])
    ),
})
>>>>>>> Stashed changes
