from django.apps import AppConfig

class RrhhConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rrhh'

    def ready(self):
        # Reactivamos las señales ahora que los archivos están limpios
        import rrhh.signals
