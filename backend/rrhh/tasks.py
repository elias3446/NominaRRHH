from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def limpiar_tokens_expirados():
    """
    Tarea asíncrona de Celery que llama al comando nativo de SimpleJWT
    para eliminar de la base de datos (blacklist) los tokens cuya fecha
    de expiración ya haya pasado, liberando espacio con Redis.
    """
    logger.info("Iniciando tarea de depuración de tokens expirados (Blacklist)...")
    try:
        call_command('flushexpiredtokens')
        logger.info("Depuración de tokens completada de manera exitosa.")
        return "Tokens expirados eliminados"
    except Exception as e:
        logger.error(f"Error al depurar tokens expirados: {e}")
        return f"Error: {str(e)}"
