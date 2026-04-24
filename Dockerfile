# Stage 1: Build — compile C extensions (bcrypt, etc.)
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime — lean final image
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

ENV DB_SSL_CA=/app/ca.pem

RUN chmod +x start.sh

RUN adduser --disabled-password --gecos "" --no-create-home appuser \
    && chown -R appuser /app

USER appuser

# Cloud Run injects $PORT (default 8080)
EXPOSE 8080

CMD ["./start.sh"]
