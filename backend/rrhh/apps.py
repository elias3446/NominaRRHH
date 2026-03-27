from django.apps import AppConfig

class RrhhConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rrhh'

    def ready(self):
        # Ahora el ready importa el PAQUETE de señales ordenado
        import rrhh.signals
