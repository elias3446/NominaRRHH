import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from .user_models import CustomUser

class Department(models.Model):
    """
    Modelo de Departamentos de Swissport (RRHH).
    Incluye trazabilidad completa vinculada a auth.users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True, verbose_name="Nombre del Departamento")
    description = models.TextField(null=True, blank=True, verbose_name="Descripción")
    
    # Auditoría (Vinculado a nuestro CustomUser/auth.users)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='departments_created'
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='departments_updated'
    )
    deleted_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='departments_deleted'
    )

    class Meta:
        db_table = 'rrhh_department' if getattr(settings, 'IS_TESTING', False) else '"rrhh"."rrhh_department"'
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['name']

    def __str__(self):
        return self.name

    def soft_delete(self, user):
        """Marca el registro como eliminado lógicamente."""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
