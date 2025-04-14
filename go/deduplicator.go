package main

import (
	"C"
	"crypto/sha256"
	"encoding/hex"
)

//export GenerateEventHash
func GenerateEventHash(jsonStr *C.char) *C.char {
	data := []byte(C.GoString(jsonStr))
	hash := sha256.Sum256(data)
	return C.CString(hex.EncodeToString(hash[:]))
}

func main() {}

