import uuid
import sys
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings

# Detección de entorno para mapeo de tablas (Postgres vs SQLite)
_IS_SQLITE = settings.DATABASES['default']['ENGINE'].endswith('sqlite3')
_IS_TEST = 'pytest' in sys.modules or 'test' in sys.argv

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
    
    # Mapeo de tiempo de creación y borrado lógico
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', null=True, blank=True)
    deleted_at = models.DateTimeField(db_column='deleted_at', null=True, blank=True)
    
    # Otros campos nativos de Supabase
    instance_id = models.UUIDField(null=True, blank=True)
    aud = models.CharField(max_length=255, default='authenticated')
    role = models.CharField(max_length=255, default='authenticated')
    is_super_admin = models.BooleanField(default=False, db_column='is_super_admin')
    
    # Nuevos Metadatos Extensos (auth.users de Supabase)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    email_confirmed_at = models.DateTimeField(null=True, blank=True)
    invited_at = models.DateTimeField(null=True, blank=True)
    
    # Tokens Confirmación / Recuperación
    confirmation_token = models.CharField(max_length=255, null=True, blank=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    recovery_token = models.CharField(max_length=255, null=True, blank=True)
    recovery_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Tokens Cambio Correo
    email_change_token_new = models.CharField(max_length=255, null=True, blank=True)
    email_change_token_current = models.CharField(max_length=255, null=True, blank=True)
    email_change = models.CharField(max_length=255, null=True, blank=True)
    email_change_sent_at = models.DateTimeField(null=True, blank=True)
    email_change_confirm_status = models.SmallIntegerField(null=True, blank=True, default=0)
    
    # Telefono
    phone = models.CharField(max_length=255, unique=True, null=True, blank=True)
    phone_confirmed_at = models.DateTimeField(null=True, blank=True)
    phone_change = models.CharField(max_length=255, null=True, blank=True)
    phone_change_token = models.CharField(max_length=255, null=True, blank=True)
    phone_change_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos extra
    raw_app_meta_data = models.JSONField(null=True, blank=True, default=dict)
    raw_user_meta_data = models.JSONField(null=True, blank=True, default=dict)
    
    # Estado del usuario (Ban, Reauth, SSO)
    banned_until = models.DateTimeField(null=True, blank=True)
    reauthentication_token = models.CharField(max_length=255, null=True, blank=True)
    reauthentication_sent_at = models.DateTimeField(null=True, blank=True)
    is_sso_user = models.BooleanField(default=False)

    # PROPIEDADES VIRTUALES (Solo en Python, no en la DB)
    @property
    def confirmed_at(self):
        """Devuelve el tiempo de confirmación calculado."""
        return self.email_confirmed_at or self.phone_confirmed_at
    
    @property
    def is_staff(self):
        return True if self.role in ['admin', 'service_role'] else False

    @property
    def is_superuser(self):
        return True if self.role == 'service_role' else False

    @property
    def is_active(self):
        # El usuario no está activo si ha sido borrado (soft delete)
        if self.deleted_at is not None:
            return False
        
        # El usuario no está activo si ha sido baneado y la fecha aún no expira
        if self.banned_until and self.banned_until > timezone.now():
            return False
            
        return True

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    objects = SupabaseUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        # Usamos el search_path de Postgres (django,auth,public) para encontrar 'users'
        # En SQLite (pruebas local) se creará de forma nativa.
        db_table = 'users'
        _is_test = 'pytest' in sys.modules or 'test' in sys.argv
        managed = _is_test
        verbose_name = 'Usuario Purificado Swissport'
