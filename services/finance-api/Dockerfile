FROM python:3.11-slim

WORKDIR /app

COPY finance-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY shared /app/shared
COPY finance-api /app

ENV PYTHONPATH=/app
EXPOSE 8004

CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8004"]
