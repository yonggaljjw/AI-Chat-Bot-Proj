#!bin/bash

docker compose down

docker compose up airflow-init

docker compose up 