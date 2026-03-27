# Usamos la imagen oficial de PostgreSQL versión 15
FROM postgres:15

# Copiamos el respaldo de Swissport directamente
# oficial de autoinicialización de Postgres.
COPY init.sql /docker-entrypoint-initdb.d/init.sql

# Los usuarios, contraseñas y puertos serán cargados automáticamente 
# desde tu archivo .env gracias a docker-compose.yml.
