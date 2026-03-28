import pytest
from unittest.mock import patch
from rrhh.tasks import limpiar_tokens_expirados

@pytest.mark.django_db
class TestCeleryTasks:
    @patch('rrhh.tasks.call_command')
    def test_limpiar_tokens_expirados_success(self, mock_call_command):
        """Verifica que la tarea de celery llame al comando de django correctamente."""
        # Configurar el mock para que no lance error
        mock_call_command.return_value = None
        
        # Ejecutar la tarea directamente (sin pasar por el worker)
        result = limpiar_tokens_expirados()
        
        # Verificar que la tarea reportó éxito
        assert result == "Tokens expirados eliminados"
        # Verificar que el comando de Django fue invocado exactamente 1 vez
        mock_call_command.assert_called_once_with('flushexpiredtokens')
        
    @patch('rrhh.tasks.call_command')
    def test_limpiar_tokens_expirados_failure(self, mock_call_command):
        """Verifica que la tarea devuelva el mensaje de error apropiado si falla."""
        # Simular una excepción en el comando
        mock_call_command.side_effect = Exception("Fallo simulado de base de datos")
        
        result = limpiar_tokens_expirados()
        
        assert "Error: Fallo simulado de base de datos" in result
        mock_call_command.assert_called_once_with('flushexpiredtokens')
