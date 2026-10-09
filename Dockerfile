FROM python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    AURA_DEMO_ROOT=/data/workspaces AURA_DEV_DB=/data/unused-development.sqlite3 \
    AURA_SECURE_COOKIE=true
WORKDIR /app
COPY requirements-demo.lock /app/
RUN pip install --no-cache-dir -r requirements-demo.lock \
    && useradd --uid 10001 --create-home aura \
    && mkdir /data && chown aura:aura /data
COPY aura_safety /app/aura_safety
COPY aura_longitudinal /app/aura_longitudinal
COPY aura_communication /app/aura_communication
COPY aura_agent /app/aura_agent
COPY aura_detectors /app/aura_detectors
COPY aura_app /app/aura_app
COPY aura_simulation /app/aura_simulation
COPY aura_ui /app/aura_ui
USER aura
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "aura_app.hosted:create_hosted_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
