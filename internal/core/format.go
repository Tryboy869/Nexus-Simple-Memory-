// Package core contains the main business logic for the NSM tool.
package core

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/gob"
	"hash"
	"io"
	"time"
)

const (
	// MagicNumber identifies the file as a valid .nsm archive. (NSM v1)
	MagicNumber uint32 = 0x4E534D01
	// HeaderSize is the fixed size of the archive header in bytes.
	HeaderSize = 64
)

// Header is the fixed-size block at the beginning of every .nsm file.
// Its structure must remain backward-compatible.
type Header struct {
	Magic            uint32    // 4 bytes: Magic number to identify file type.
	Version          uint16    // 2 bytes: Format version.
	CompressionType  uint8     // 1 byte: Enum for ZSTD, GZIP, etc.
	EncryptionType   uint8     // 1 byte: Enum for AES256, etc.
	Timestamp        int64     // 8 bytes: Archive creation time (UnixNano).
	IndexOffset      int64     // 8 bytes: Byte offset to the start of the Index block.
	IndexLength      int64     // 8 bytes: Length of the Index block in bytes.
	DataChecksum     [32]byte // 32 bytes: SHA-256 checksum of the compressed data block.
}

// Index contains all metadata for the files stored in the archive.
// It is serialized using gob for efficient Go-specific encoding.
type Index struct {
	Files      map[string]FileMetadata // Map of original file path to its metadata.
	SearchData map[string][]string     // A simple full-text index (e.g., keyword -> file path).
}

// FileMetadata stores information about a single file in the archive.
type FileMetadata struct {
	Path             string
	UncompressedSize int64
	CompressedSize   int64
	Offset           int64 // Offset within the compressed data block where this file begins.
	ModTime          time.Time
	Mode             uint32 // File permissions
}

// WriteHeader writes the binary Header to the given writer.
// It uses binary.Write for fixed-size data serialization.
func WriteHeader(w io.Writer, h *Header) error {
	// Use BigEndian to ensure consistent byte order across different systems.
	if err := binary.Write(w, binary.BigEndian, h); err != nil {
		return NewCoreError(ErrArchiveWrite, "failed to write archive header").Wrap(err)
	}
	return nil
}

// ReadHeader reads and parses the binary Header from the given reader.
func ReadHeader(r io.Reader) (*Header, error) {
	h := &Header{}
	if err := binary.Read(r, binary.BigEndian, h); err != nil {
		if err == io.EOF {
			return nil, NewCoreError(ErrArchiveRead, "unexpected end of file while reading header")
		}
		return nil, NewCoreError(ErrArchiveRead, "failed to read archive header").Wrap(err)
	}

	// Validate the magic number to ensure it's a compatible file.
	if h.Magic != MagicNumber {
		return nil, NewCoreError(ErrInvalidFormat, "not a valid .nsm file (magic number mismatch)")
	}
	return h, nil
}

// WriteIndex serializes the Index struct using gob and writes it to the writer.
// It returns the length of the written data.
func WriteIndex(w io.Writer, idx *Index) (int64, error) {
	counter := &writeCounter{writer: w}
	encoder := gob.NewEncoder(counter)
	if err := encoder.Encode(idx); err != nil {
		return 0, NewCoreError(ErrArchiveWrite, "failed to write archive index").Wrap(err)
	}
	return counter.total, nil
}

// ReadIndex reads from the reader and deserializes the Index struct.
func ReadIndex(r io.Reader) (*Index, error) {
	decoder := gob.NewDecoder(r)
	idx := &Index{}
	if err := decoder.Decode(idx); err != nil {
		return nil, NewCoreError(ErrArchiveRead, "failed to read archive index").Wrap(err)
	}
	return idx, nil
}

// NewChecksumWriter returns an io.Writer that calculates a SHA-256 checksum
// while passing data through to an underlying writer.
func NewChecksumWriter(w io.Writer) (io.Writer, hash.Hash) {
	hasher := sha256.New()
	// TeeReader will write to hasher and the provided writer simultaneously.
	return io.MultiWriter(w, hasher), hasher
}
