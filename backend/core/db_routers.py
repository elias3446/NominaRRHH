class DjangoSchemaRouter:
    """
    Router para dirigir las tablas centrales de Django
    (admin, auth, sessions, contenttypes) hacia el esquema 'django'.
    """
    django_apps = ['admin', 'auth', 'contenttypes', 'sessions', 'messages']

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.django_apps:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.django_apps:
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Esta lógica no es estrictamente necesaria aquí con un solo DB,
        # pero es bueno tenerla para que Django sepa que estas apps están gestionadas.
        return True

class AuthSchemaRouter:
    """
    Router específico para dirigir SimpleJWT al esquema 'auth' de Supabase.
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'token_blacklist':
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'token_blacklist':
            return 'default'
        return None
