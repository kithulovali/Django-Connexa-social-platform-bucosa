#!/bin/sh
python manage.py migrate
gunicorn bucosa.wsgi:application --bind 0.0.0.0:$PORT