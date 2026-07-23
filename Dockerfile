FROM ghcr.io/astral-sh/uv:0.11.30 AS uv

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY --chown=app:app app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

RUN mkdir -p /app/data/raw /app/data/clean && chown -R app:app /app/data
USER app

EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS test
USER root
COPY tests ./tests
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra dev --no-editable
CMD ["pytest", "-q"]
