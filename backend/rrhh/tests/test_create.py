import os
import django
import uuid
from django.db import connection
from django.contrib.auth.hashers import make_password

# 1. Configurar el entorno de Django para el script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def create_real_hashed_user():
    u_id = str(uuid.uuid4())
    email = 'elias_seguro@example.com'
    password_plano = 'elias12345'
    password_hash = make_password(password_plano)
    
    print(f"\n--- INICIANDO CREACIÓN DE USUARIO PARA {email} ---")
    print(f"ID sugerido: {u_id}")
    print(f"Hash generado por Django: {password_hash[:15]}...")

    with connection.cursor() as cursor:
        try:
            # Insertamos directamente usando el nombre del esquema completo
            cursor.execute("""
                INSERT INTO auth.users (id, email, encrypted_password, aud, role) 
                VALUES (%s, %s, %s, 'authenticated', 'authenticated')
            """, [u_id, email, password_hash])
            print(">>> ✅ INSERT SQL EXITOSO DESDE DJANGO <<<")
        except Exception as e:
            print(f">>> ❌ ERROR AL INSERTAR: {str(e)}")

if __name__ == "__main__":
    create_real_hashed_user()
