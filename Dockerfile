FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

# Upgrade pip and install all dependencies including gunicorn
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn==23.0.0

COPY . .

RUN python manage.py collectstatic --noinput || true


# Render injects PORT automatically; fall back to 8000 for local runs
ENV PORT=8000

# Tell Docker which port the app listens on (documentation only)
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn StreamSync.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --timeout 120"]