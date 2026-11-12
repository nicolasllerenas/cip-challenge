FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
ARG SERVICE
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY services services
RUN uv sync --locked --no-dev --no-editable --package cip-${SERVICE}

FROM python:3.12-slim-bookworm
ARG SERVICE
ENV PATH=/app/.venv/bin:$PATH \
    SERVICE_MODULE=cip_${SERVICE} \
    PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app:app /data
COPY --from=build /app/.venv /app/.venv
USER app
WORKDIR /home/app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/' + ('v1/health' if '${SERVICE}' == 'gateway' else 'health'))"
CMD ["sh", "-c", "exec uvicorn --factory ${SERVICE_MODULE}.api:create_app --host 0.0.0.0 --port 8000"]
