# Purpose: Containerize the Edge Node Vision Pipeline for CPU-only environments.
# Responsibilities:
# - Provide a lightweight Python runtime with PyTorch (CPU), YOLOv8, and OpenCV.
# - Install all system dependencies required to decode video files via ffmpeg.
# - Run as a non-root user for security.

# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Pre-compile wheels — PyTorch CPU wheel pulled from official index to keep image lean.
# The --extra-index-url ensures pip finds the correct CPU-only torch build.
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt


# ==========================================
# STAGE 2: Runner
# ==========================================
FROM python:3.11-slim

# Security: non-root user (same pattern as backend-api, event-engine, reid-service)
RUN addgroup --system appgroup && adduser --system --group appuser

WORKDIR /app

# Install system libraries required by OpenCV to decode video streams
# and by PyTorch for numerical computations.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copy the vision pipeline source code
COPY ./src /app/src

RUN chown -R appuser:appgroup /app

# Drop root privileges
USER appuser

# Health check — verifies the vision pipeline process is alive.
# Edge node is a batch processor, so we probe process existence.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD pgrep -f "src.main" || exit 1

# Execute the pipeline daemon
CMD ["python", "-m", "src.main"]
