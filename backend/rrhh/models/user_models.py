import uuid
import sys
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class SupabaseUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser):
    """
    Modelo DEPURADO Swissport.
    Sobreescribimos 'password' para que apunte a 'encrypted_password' de Supabase.
    NO usamos PermissionsMixin para evitar campos extras como is_superuser.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    
    # Sobreescribimos el campo password nativo de Django para que use la columna de Supabase
    password = models.CharField(max_length=255, db_column='encrypted_password')
    
    # Django 'last_login' mapeado a 'last_sign_in_at' de Supabase
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_sign_in_at')
    
    # Mapeo de tiempo de creación
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', null=True, blank=True)
    
    # Otros campos nativos de Supabase
    instance_id = models.UUIDField(null=True, blank=True)
    aud = models.CharField(max_length=255, default='authenticated')
    role = models.CharField(max_length=255, default='authenticated')
    is_super_admin = models.BooleanField(default=False, db_column='is_super_admin')

    # PROPIEDADES VIRTUALES (Solo en Python, no en la DB)
    @property
    def is_staff(self):
        return True if self.role in ['admin', 'service_role'] else False

    @property
    def is_superuser(self):
        return True if self.role == 'service_role' else False

    @property
    def is_active(self):
        return True

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    objects = SupabaseUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        # En Postgres usamos el esquema 'auth' de Supabase
        # En SQLite (pruebas local) usamos una tabla plana 'users'
        db_table = 'users' if 'pytest' in sys.modules else 'auth"."users'
        managed = 'pytest' in sys.modules
        verbose_name = 'Usuario Purificado Swissport'
