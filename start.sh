#!/bin/sh
alembic upgrade head

uvicorn main:app --host localhost --port 8081 --reload