from django.db import models
from django.conf import settings

class UserProfile(models.Model):
    """
    Extensión del perfil de usuario que se guarda en el esquema público y se relaciona
    1 a 1 con auth.users (CustomUser).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=150, null=True, blank=True)
    employee_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.email})"
