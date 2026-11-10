# Same Python version CI tests on.
FROM python:3.12-slim

# Don't write .pyc files; print logs immediately instead of buffering them.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first: Docker caches this layer, so packages are only
# reinstalled when requirements.txt changes, not on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 1) bring the database schema up to date, 2) add sample data if empty, 3) start the API.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
