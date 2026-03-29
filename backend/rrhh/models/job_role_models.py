import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from .user_models import CustomUser
from .department_models import Department

class JobRole(models.Model):
    """
    Modelo de Cargos de Swissport (RRHH).
    Representa las posiciones laborales dentro de un departamento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, verbose_name="Nombre del Cargo")
    description = models.TextField(null=True, blank=True, verbose_name="Descripción")
    
    # Cada Cargo pertenece obligatoriamente a un Departamento
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='job_roles',
        verbose_name="Departamento"
    )

    # Auditoría Cronológica
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Trazabilidad de Usuarios
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='job_roles_created'
    )
    updated_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='job_roles_updated'
    )
    deleted_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='job_roles_deleted'
    )

    class Meta:
        db_table = 'rrhh_jobrole' if getattr(settings, 'IS_TESTING', False) else '"rrhh"."rrhh_jobrole"'
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['name']
        unique_together = ('name', 'department', 'deleted_at') # Evitar duplicados activos en el mismo depto

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    def soft_delete(self, user):
        """Marca el registro como eliminado lógicamente."""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
