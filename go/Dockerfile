#FROM golang:1.21 AS builder
#
#WORKDIR /app
#
## Копируем Go-файлы
#COPY go/deduplicator.go go/Makefile ./
#
## Сборка библиотеки
#RUN make build
#
#FROM python:3.12-slim
#
## Установка зависимостей
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends gcc libc6-dev && \
#    rm -rf /var/lib/apt/lists/*
#
#WORKDIR /app
#
## Копируем зависимости Python
#COPY requirements.txt .
#
## Установка Python-пакетов
#RUN pip install --no-cache-dir -r requirements.txt
#
## Копируем артефакты из builder
#COPY --from=builder /app/libdedup.so ./lib/
#
## Копируем основной код
#COPY src/ ./src/
#COPY main.py ./

# Настройки среды
#ENV PYTHONPATH=/app \
#    PYTHONUNBUFFERED=1
#
#EXPOSE 8000


# Запуск приложения
# CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

