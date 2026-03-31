#!/bin/sh
# docker/entrypoint.sh
# S'executa cada cop que arranca el contenedor.
# Espera a que PostgreSQL estigui ple abans de continuar

set -e

echo " Esperant a que PostgreSQL estigui disponible..."

# Extreu host puert de DATABASE_URL si está definida
# Format esperat: postgresql://user:pass@host:port/db
if [ -n "$DATABASE_URL" ]; then
    DB_HOST=$(echo "$DATABASE_URL" | sed -e 's|.*@||' -e 's|:.*||' -e 's|/.*||')
    DB_PORT=$(echo "$DATABASE_URL" | sed -e 's|.*:||' -e 's|/.*||')
    DB_PORT=${DB_PORT:-5432}
else
    DB_HOST=${DB_HOST:-db}
    DB_PORT=${DB_PORT:-5432}
fi

# Espera activa fins que PostgreSQL accepti conexions
until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
result = s.connect_ex(('$DB_HOST', int('$DB_PORT')))
s.close()
sys.exit(result)
" 2>/dev/null; do
    echo "   PostgreSQL no disponible en $DB_HOST:$DB_PORT — reintentant en 2s..."
    sleep 2
done

echo " PostgreSQL disponible en $DB_HOST:$DB_PORT"

# Aplica migraciones pendientes
echo " Aplicant migraciones Django..."
python manage.py migrate --noinput

echo " Iniciant aplicacio..."
exec "$@"