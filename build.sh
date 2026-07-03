#!/usr/bin/env bash
python manage.py collectstatic --no-input
# python manage.py migrate
daphne -b 0.0.0.0 -p 8000 conf.asgi:application