#!/bin/sh
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput 2> /dev/null || echo "Superuser already exists"
uwsgi conf/uwsgi.ini