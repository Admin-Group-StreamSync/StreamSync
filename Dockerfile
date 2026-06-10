FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000

EXPOSE 8000

# collectstatic i migrate s'executen en runtime (no en build) perquè
# necessiten les variables d'entorn (SECRET_KEY, API_BASE_URLS, etc.)
# Gunicorn arrenca immediatament després sense bloquejos.
CMD ["sh", "-c", "\
    python manage.py collectstatic --noinput && \
    python manage.py migrate --noinput && \
    python manage.py create_superuser_env && \
    gunicorn StreamSync.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --timeout 120 \
"]
