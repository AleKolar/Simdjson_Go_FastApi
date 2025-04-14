FROM golang:1.21
WORKDIR /build
COPY . .
RUN go mod init deduplicator && \
    go build -o libdedup.dll -buildmode=c-shared deduplicator.go