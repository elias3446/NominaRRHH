# Usamos la versión estable de Node.js en Alpine (ligera)
FROM node:20-alpine

WORKDIR /app

# Usaremos NPM estandarizado. Copiamos configuraciones
COPY package.json package-lock.json* bun.lock* ./

# Instalamos las dependencias
RUN npm install

# Copiamos el resto del frontend
COPY . .

# Comando que arranca Vite, lo expone (host 0.0.0.0) y toma el puerto del .env
CMD sh -c "npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT:-3000}"
