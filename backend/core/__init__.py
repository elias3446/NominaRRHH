# Importar las señales de WebSockets cuando Django arranque
default_app_config = 'core.apps.CoreConfig'
import core.signals
