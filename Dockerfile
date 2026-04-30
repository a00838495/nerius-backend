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

# curl is needed for HEALTHCHECK; ca-certificates for HTTPS to Aiven/etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

# DB_SSL_CA defaults to empty: Cloud SQL via Unix socket handles TLS itself.
# For Aiven/external MySQL, set DB_SSL_CA=/app/ca.pem at the platform level.
ENV DB_SSL_CA=""

RUN chmod +x start.sh

RUN adduser --disabled-password --gecos "" --no-create-home appuser \
    && chown -R appuser /app

USER appuser

# Cloud Run injects $PORT; default 8080 also works on Dockploy.
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8080}/api/v1/health" || exit 1

CMD ["./start.sh"]
