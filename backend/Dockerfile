# syntax=docker/dockerfile:1
# Multi-stage build:
#   1. `builder`  — installs dependencies into a venv
#   2. `runtime`  — copies the venv + source, drops to a non-root user
# The runtime stage is intentionally minimal so CVE scan noise stays low and
# the image is small.
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install deps first (cache layer)
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

# Now copy the project source and finalize the install.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev


# ---- runtime stage ----
FROM python:3.12-slim AS runtime

# Create a non-root user and group for the application. UID 10001 is
# arbitrary but high enough to avoid clashing with host UIDs when
# bind-mounting volumes.
RUN groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --home /app --shell /sbin/nologin app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

WORKDIR /app

# Pull in the venv built in the builder stage.
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/app /app/app
COPY --from=builder --chown=app:app /app/alembic /app/alembic
COPY --from=builder --chown=app:app /app/alembic.ini /app/alembic.ini

USER app

EXPOSE 8000

# `python -m` is fine because the entrypoint is the venv-installed binary.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
