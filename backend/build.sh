#!/usr/bin/env bash
# Render build script — runs on every deploy.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# --reset-all: delete old jobs & courses then reseed from the latest CSV files.
# Skills table is preserved across deploys.
python manage.py seed_catalog --reset-all
