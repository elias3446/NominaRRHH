import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rrhh.models import CustomUser

def run():
    print("--- INICIANDO PRUEBA DE CREACION ---")
    email = "test_definitivo@example.com"
    
    # 1. Borrar si existe
    CustomUser.objects.filter(email=email).delete()
    
    # 2. Crear
    u = CustomUser(id=uuid.uuid4(), email=email)
    u.set_password("pass123")
    u.save()
    
    print(f"✅ Usuario {email} creado con exito.")
    
    # 3. Verificar
    res = CustomUser.objects.filter(email=email).first()
    if res:
        print(f"🔍 Verificacion exitosa: {res.email} creado el {res.created_at}")
    else:
        print("❌ Error: El usuario no aparece en la DB.")

if __name__ == "__main__":
    run()
