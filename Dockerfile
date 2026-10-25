# --- Этап 1: сборка зависимостей ---
FROM python:3.13-slim AS builder

WORKDIR /build
COPY requirements.txt .
# Ставим пакеты в отдельный префикс, чтобы скопировать в финальный образ только их
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Этап 2: финальный образ ---
FROM python:3.13-slim AS runtime

# Привязывает опубликованный образ в GHCR к репозиторию
LABEL org.opencontainers.image.source=https://github.com/MaksChocomint/fastapi-tasks

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Непривилегированный пользователь, от которого работает приложение
RUN useradd --create-home --uid 1000 app

WORKDIR /app
COPY --from=builder /install /usr/local
COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app

USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Этап для тестов: финальный образ + dev-зависимости и тесты ---
FROM runtime AS test

USER root
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY pytest.ini ruff.toml ./
COPY tests ./tests
USER app
# Кэш pytest отключён: у пользователя app нет прав на запись в /app
CMD ["pytest", "-v", "-p", "no:cacheprovider"]
