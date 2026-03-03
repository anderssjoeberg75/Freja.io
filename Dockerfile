FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN groupadd --system freja && useradd --system --gid freja --create-home --home-dir /home/freja freja

COPY --chown=freja:freja . .

RUN mkdir -p /app/db /app/logs && chown -R freja:freja /app/db /app/logs

USER freja

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app_socketio", "--host", "0.0.0.0", "--port", "8000"]
