# Usamos la imagen oficial de PostgreSQL versión 15
FROM postgres:15

# (Opcional) Si en el futuro necesitas que se ejecute algún script al iniciar
# la base de datos por primera vez (como crear tablas predefinidas), puedes 
# Copiamos la carpeta que creaste ('init') con sus respaldos hacia la carpeta 
# oficial de autoinicialización de Postgres. Todo archivo .sql que esté allí 
# correrá automáticamente, poblando la BD al encender el contenedor por primera vez.
COPY ./init/ /docker-entrypoint-initdb.d/
# desde tu archivo .env gracias a docker-compose.yml.
