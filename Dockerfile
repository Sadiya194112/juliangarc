FROM python:3.11.13-slim-bullseye

# Create app directory
RUN mkdir /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose backend port
EXPOSE 8500

# Final CMD
CMD /bin/bash -c "\
    until nc -z -v -w30 dokploy-redis 6379; do echo 'Waiting for Redis...'; sleep 1; done && \
    python manage.py collectstatic --noinput && \
    daphne -b 0.0.0.0 -p 8500 src.asgi:application"
