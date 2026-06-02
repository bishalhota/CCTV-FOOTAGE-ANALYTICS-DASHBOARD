# Purpose: Containerize the Backend API for scalable production deployment.
# Responsibilities:
# - Provide a clean, minimal runtime environment for the FastAPI server.
# - Enforce security best practices (running as a non-root user).
# - Optimize build times and image size using Docker Multi-Stage builds.

# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies required for compiling asyncpg/psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker layer caching
COPY requirements.txt .

# Compile wheels instead of installing directly. This creates a highly optimized 
# binary package that we can drop into the final image without carrying over GCC.
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ==========================================
# STAGE 2: Runner
# ==========================================
FROM python:3.11-slim

# Security: Create a non-root user. Running web APIs as root in Docker is a 
# massive security risk. If an RCE vulnerability is found in the app, 
# the attacker is trapped as a low-privileged user.
RUN addgroup --system appgroup && adduser --system --group appuser

WORKDIR /app

# Install only the runtime dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled wheels from the builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install the wheels without caching to save space
RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copy the actual application source code
COPY ./src /app/src
# Include Alembic files for running database migrations inside the container
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini
# Include the seeder script so the lifespan hook can auto-seed on first boot
COPY ./scripts /app/scripts

# Transfer file ownership to the secure non-root user
RUN chown -R appuser:appgroup /app

# Drop root privileges immediately
USER appuser

EXPOSE 8000

# Health check — Docker/Railway/Render use this to determine if the container is ready.
# Hits our /health endpoint every 30s; 3 consecutive failures = container marked unhealthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Principal Note: Run Uvicorn directly via the exec form (JSON array).
# Do NOT use `CMD uvicorn ...` (shell form) because it wraps the process in `/bin/sh -c`.
# Shell wrapping breaks POSIX signal handling, meaning the container won't shut down 
# gracefully when Kubernetes sends a SIGTERM, resulting in dropped client connections.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
