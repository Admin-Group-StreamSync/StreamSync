FROM python:3.12-slim AS builder

# Evita que Python escrigui .pyc i buffereji stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies del sistema necesaries para compilar paquets Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia solo requirements primer → aprofita la caché de Docker
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# Imate final, sense compiladors ni cachés
FROM python:3.12-slim AS runtime
# Django llegira aquestes variables; els valors reals venen dels secrets
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=streamsync.settings_production \
    PORT=8000

WORKDIR /app

# Sol libpq-dev a runtime (driver PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia les dependencies instaladas en el builder
COPY --from=builder /install /usr/local

# Copia el codig font
COPY . .

# Usuari sense privilegios par ejecutar la app
RUN addgroup --system django && adduser --system --ingroup django django

# Directori par arxius estatics
RUN mkdir -p /app/staticfiles /app/mediafiles \
    && chown -R django:django /app

USER django

# collectstatic en build time
ARG SECRET_KEY=build-time-dummy-key
RUN python manage.py collectstatic --noinput

EXPOSE $PORT

# Entrypoint: espera a que la BD estigui llesta, migra i arranca Gunicorn
COPY --chown=django:django docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Gunicorn: 2 workers per CPU + 1 (ajustable vía ENV)
CMD ["gunicorn", "streamsync.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]