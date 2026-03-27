import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class SupabaseUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Este es el Modelo de Usuario Maestro que apunta directamente al 
    Esquema 'auth' de Supabase (Opción A). 
    Utiliza UUIDs reales y está preparado para mantener tus datos históricos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Supabase guarda metadatos aquí que podemos mapear después
    raw_user_meta_data = models.JSONField(null=True, blank=True)

    objects = SupabaseUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        # Probamos con la sintaxis simplificada para ver si el test arranca
        db_table = 'auth.users'
        verbose_name = 'Usuario de Swissport (Auth)'
        verbose_name_plural = 'Usuarios de Swissport (Auth)'

    def __str__(self):
        return self.email
