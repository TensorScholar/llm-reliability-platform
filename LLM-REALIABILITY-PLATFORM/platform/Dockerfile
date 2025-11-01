 FROM python:3.11-slim AS builder
 RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
 RUN curl -sSL https://install.python-poetry.org | python3 -
 ENV PATH="/root/.local/bin:$PATH"
 WORKDIR /app
 COPY pyproject.toml .
 RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

 FROM python:3.11-slim
 RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*
 WORKDIR /app
 COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
 COPY --from=builder /usr/local/bin /usr/local/bin
 COPY src/ ./src/
 USER root
 EXPOSE 8000 9090
 HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"
 CMD ["uvicorn", "reliability_platform.main:app", "--host", "0.0.0.0", "--port", "8000"]

