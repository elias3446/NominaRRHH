import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from core.consumers import UserConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Esta es la puerta de entrada para todas las conexiones del proyecto
application = ProtocolTypeRouter({
    # Protocolo estándar de Web (HTTP)
    "http": get_asgi_application(),

    # Protocolo de WebSockets (tiempo real)
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # Definimos la ruta de conexión: ws://localhost:8000/ws/users/
            path("ws/users/", UserConsumer.as_asgi()),
        ])
    ),
})
