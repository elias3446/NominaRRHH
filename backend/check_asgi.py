import sys
import os

# Add the current directory to sys.path
sys.path.append('/app')

# Set settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    print("Django setup success")
    
    from core.asgi import application
    print("ASGI application import success")
    print(application)
except Exception as e:
    import traceback
    traceback.print_exc()
