FROM python:3.11-slim

WORKDIR /app

COPY __NAME__-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY shared /app/shared
COPY __NAME__-api /app

ENV PYTHONPATH=/app
EXPOSE __PORT__

CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port __PORT__"]
