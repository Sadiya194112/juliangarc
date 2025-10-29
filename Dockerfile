FROM python:3.11.13-slim-bullseye

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (including Redis server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat \
    poppler-utils \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the port you want the app to run on
EXPOSE 8500

CMD redis-server --daemonize yes && \
    /bin/bash -c "until nc -z -v -w30 127.0.0.1 6379; do echo 'Waiting for Redis...'; sleep 1; done && \
    python manage.py collectstatic --noinput && \
    daphne -b 0.0.0.0 -p 8500 src.asgi:application"
