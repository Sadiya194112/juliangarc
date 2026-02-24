    # #!/bin/bash
    # set -e

    # echo "Waiting for Redis..."
    # until nc -z -v -w30 ${REDIS_HOST:-dokploy-redis} ${REDIS_PORT:-6379}; do
    #     echo "Waiting for Redis..."
    #     sleep 1
    # done

    # echo "Waiting for PostgreSQL..."
    # until nc -z -v -w30 ${DB_HOST} ${DB_PORT}; do
    #     echo "Waiting for PostgreSQL..."
    #     sleep 1
    # done

    # echo "Running migrations..."
    # python3 manage.py migrate --noinput

    # echo "Collecting static files..."
    # python3 manage.py collectstatic --noinput

    # echo "Starting Daphne server..."
    # exec daphne -b 0.0.0.0 -p 8500 src.asgi:application
