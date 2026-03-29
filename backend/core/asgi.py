import os
from django.core.asgi import get_asgi_application

# Configurar el entorno de Django antes de cualquier otra cosa
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Inicializar la aplicación HTTP de Django
# Esto asegura que django.setup() se llame correctamente
django_asgi_app = get_asgi_application()

# Importar el resto DESPUES de que Django esté listo
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from rrhh.middleware import JWTAuthMiddlewareStack
from rrhh.consumers.user_consumer import UserConsumer
from rrhh.consumers.auth_consumer import AuthConsumer
from rrhh.consumers.user_management import UserManagementConsumer
from rrhh.consumers.department_management import DepartmentManagementConsumer
from rrhh.consumers.job_role_management import JobRoleManagementConsumer

# Definir la aplicación maestra
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter([
            path("ws/users/", UserConsumer.as_asgi()),
            path("ws/auth/", AuthConsumer.as_asgi()),
            path("ws/user-management/", UserManagementConsumer.as_asgi()),
            path("ws/department-management/", DepartmentManagementConsumer.as_asgi()),
            path("ws/job-role-management/", JobRoleManagementConsumer.as_asgi()),
        ])
    ),
})
