FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

RUN mkdir -p /app/data/raw /app/data/clean && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

