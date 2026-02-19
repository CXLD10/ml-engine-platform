FROM python:3.11-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

COPY app ./app
COPY configs ./configs
COPY train.py ./train.py
COPY .env.example ./.env.example

RUN mkdir -p /app/artifacts/models /app/artifacts/predictions && chown -R appuser:appgroup /app
VOLUME ["/app/artifacts/models", "/app/artifacts/predictions"]

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; p=os.getenv('PORT','8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/ready', timeout=3)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
