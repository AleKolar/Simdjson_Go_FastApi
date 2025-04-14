FROM python:3.12-slim

# Установка компилятора Go
RUN apt-get update && apt-get install -y golang gcc

# Компиляция Go-библиотеки
COPY go/ /go/
RUN cd /go && \
    go mod init deduplicator && \
    go get github.com/minio/simdjson-go && \
    go build -buildmode=c-shared -o /libdedup.so deduplicator.go

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]