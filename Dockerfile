FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install alembic

COPY ./app /app/app
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

COPY startup.sh .
RUN chmod +x startup.sh

CMD ["./startup.sh"]