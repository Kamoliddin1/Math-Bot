# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONUNBUFFERED=1


COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN python3 manage.py main
