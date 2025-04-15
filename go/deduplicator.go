package main

import (
    "C"
    "crypto/sha256"
    "encoding/hex"
    "github.com/minio/simdjson-go"
)

//export GenerateEventHash
func GenerateEventHash(jsonStr *C.char) *C.char {
    // Преобразуем C строку в байты
    data := []byte(C.GoString(jsonStr))

    // Вызов Parse с тремя аргументами
    var pj simdjson.ParsedJson
    if _, err := simdjson.Parse(data, &pj); err != nil {
        return C.CString("") // Пустая строка в случае ошибки
    }

    // Генерируем SHA-256 хеш для строковых данных
    hash := sha256.Sum256(data)
    return C.CString(hex.EncodeToString(hash[:]))
}

func main() {}

