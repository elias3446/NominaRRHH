from django.apps import AppConfig

class RrhhConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rrhh'

    def ready(self):
        # El corazón de las señales de Nómina ahora late aquí
        import rrhh.signals
