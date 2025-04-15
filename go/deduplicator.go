// package main
//
// import (
//     "C"
//     "crypto/sha256"
//     "encoding/hex"
//     "github.com/minio/simdjson-go"
// )
//
// //export GenerateEventHash
// func GenerateEventHash(jsonStr *C.char) *C.char {
//     // Преобразуем C строку в байты
//     data := []byte(C.GoString(jsonStr))
//
//     // Вызов Parse с тремя аргументами
//     var pj simdjson.ParsedJson
//     if _, err := simdjson.Parse(data, &pj); err != nil {
//         return C.CString("") // Пустая строка в случае ошибки
//     }
//
//     // Генерируем SHA-256 хеш для строковых данных
//     hash := sha256.Sum256(data)
//     return C.CString(hex.EncodeToString(hash[:]))
// }
//
// func main() {}

package main

import (
	"C"
	"encoding/hex"
	"sync"
	"unsafe"

	"github.com/minio/simdjson-go"
	"github.com/zeebo/xxh3"
)

var (
	parserPool = sync.Pool{
		New: func() interface{} {
			return &simdjson.Parser{}
		},
	}

	hashCache sync.Map
)

//export GenerateEventHash
func GenerateEventHash(jsonStr *C.char) *C.char {
	data := unsafe.Slice((*byte)(unsafe.Pointer(jsonStr)), C.strlen(jsonStr))

	// Проверка кэша
	if v, ok := hashCache.Load(string(data)); ok {
		return C.CString(v.(string))
	}

	// Валидация JSON
	parser := parserPool.Get().(*simdjson.Parser)
	defer parserPool.Put(parser)

	if _, err := parser.ParseBytes(data); err != nil {
		return nil
	}

	// Генерация хеша
	hash := xxh3.Hash(data)
	hexHash := hex.EncodeToString(hash[:])

	// Кэширование
	hashCache.Store(string(data), hexHash)

	return C.CString(hexHash)
}

func main() {}

