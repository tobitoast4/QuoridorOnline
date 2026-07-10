#!/usr/bin/env bash
python manage.py collectstatic --no-input
# python manage.py migrate
# daphne -b 0.0.0.0 -p 10000 conf.asgi:application
gunicorn --bind 0.0.0.0:10000 -k uvicorn.workers.UvicornWorker conf.asgi:application