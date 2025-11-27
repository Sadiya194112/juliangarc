# Use official Python slim image
FROM python:3.11.13-slim-bullseye

# Create app directory
RUN mkdir /app
WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose backend port
EXPOSE 8500

# Final command: wait for Redis, wait for PostgreSQL, migrate, collect static, run server
CMD /bin/bash -c "\
    echo 'Waiting for PostgreSQL...' && \
    until nc -z -v -w30 $DB_HOST $DB_PORT; do echo 'Waiting for Postgres...'; sleep 1; done && \
    python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    daphne -b 0.0.0.0 -p 8500 src.asgi:application"
