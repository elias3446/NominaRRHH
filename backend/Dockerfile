# Úsamos la imagen oficial y ligera de Python 3.11
FROM python:3.11-slim

# Evita la creación de archivos basura (.pyc)
ENV PYTHONDONTWRITEBYTECODE=1
# Asegura un log fluido en la consola de Docker
ENV PYTHONUNBUFFERED=1

# Definimos nuestra carpeta de trabajo en el contenedor
WORKDIR /app

# Copiamos e instalamos dependencias rápidamente
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo nuestro código fuente
COPY . /app/

# Levantamos el servidor de Django (Daphne) capturando la variable BACKEND_PORT desde tu .env
# Esto permite que el servidor maneje peticiones normales y WEBSOCKETS al mismo tiempo.
CMD sh -c "daphne -b 0.0.0.0 -p ${BACKEND_PORT:-8000} core.asgi:application"
