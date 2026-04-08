# Use Python 3.12 as the base image (slim = smaller size, no extra tools)
FROM python:3.12-slim

## Install uv
#COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt ./

RUN python3 -m pip install --upgrade pip &&  \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Tell Docker this container will listen on port 8000
EXPOSE 8000

# Command that runs when the container starts:
# 1. Apply database migrations (create/update tables)
# 2. Start Django's development server on all interfaces (0.0.0.0)
CMD ["gunicorn", "StreamSync.wsgi:application", "--bind", "0.0.0.0:8000"]


# 127.0.0.1 = only reachable from inside the container (default, won't work with Docker)
# 0.0.0.0 = listen on all interfaces, so the host machine can reach the container
