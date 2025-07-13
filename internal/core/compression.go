// Package core contains the main business logic for the NSM tool.
package core

import (
	"compress/gzip"
	"io"
	"runtime"
	"sync"

	"github.com/klauspost/compress/zstd"
	"github.com/sirupsen/logrus"
)

// CompressionType defines the supported compression algorithms.
type CompressionType string

const (
	// ZSTD offers a great balance between compression speed and ratio.
	ZSTD CompressionType = "zstd"
	// GZIP is widely available and a good fallback.
	GZIP CompressionType = "gzip"
)

// Compressor handles the streaming compression and decompression logic.
// It is designed to be thread-safe and memory-efficient.
type Compressor struct {
	log         *logrus.Entry
	workerPool  chan struct{} // Limits the number of concurrent compression jobs.
	zstdEncoder *sync.Pool    // Pool of ZSTD encoders to reduce allocations.
	zstdDecoder *sync.Pool    // Pool of ZSTD decoders.
}

// NewCompressor initializes a new compressor with optimized defaults.
// It creates a worker pool to control concurrency.
func NewCompressor() *Compressor {
	// Use half of the available CPU cores for the worker pool, with a minimum of 1.
	numWorkers := runtime.NumCPU() / 2
	if numWorkers == 0 {
		numWorkers = 1
	}

	return &Compressor{
		log:        logrus.WithField("component", "compressor"),
		workerPool: make(chan struct{}, numWorkers),
		zstdEncoder: &sync.Pool{
			New: func() interface{} {
				// Encoder can be configured for different levels of compression.
				encoder, _ := zstd.NewWriter(nil, zstd.WithEncoderLevel(zstd.SpeedDefault))
				return encoder
			},
		},
		zstdDecoder: &sync.Pool{
			New: func() interface{} {
				decoder, _ := zstd.NewReader(nil)
				return decoder
			},
		},
	}
}

// Compress streams data from a reader, compresses it, and writes it to a writer.
// It automatically selects the compression algorithm.
func (c *Compressor) Compress(dst io.Writer, src io.Reader, compType CompressionType) (int64, error) {
	c.log.WithField("algorithm", compType).Info("Starting compression stream")

	// Acquire a worker from the pool to limit concurrency.
	c.workerPool <- struct{}{}
	defer func() { <-c.workerPool }() // Release the worker when done.

	var compWriter io.WriteCloser
	var writtenBytes int64

	// The Counter is used to track the number of bytes written to the underlying writer.
	counter := &writeCounter{writer: dst}

	switch compType {
	case ZSTD:
		// Get an encoder from the pool and reset it to write to our destination.
		zstdWriter := c.zstdEncoder.Get().(*zstd.Encoder)
		zstdWriter.Reset(counter)
		defer func() {
			zstdWriter.Close()
			c.zstdEncoder.Put(zstdWriter) // Return encoder to the pool.
		}()
		compWriter = zstdWriter

	case GZIP:
		// Gzip writer doesn't have a poolable equivalent as easily, so we create a new one.
		gzipWriter := gzip.NewWriter(counter)
		defer gzipWriter.Close()
		compWriter = gzipWriter

	default:
		return 0, NewCoreError(ErrUnsupportedAlgorithm, "unsupported compression type: "+string(compType))
	}

	// io.Copy does the heavy lifting, streaming data in chunks, keeping memory usage low.
	_, err := io.Copy(compWriter, src)
	if err != nil {
		return 0, NewCoreError(ErrCompression, "failed during data streaming").Wrap(err)
	}

	// Important: Close the compression writer to flush any buffered data.
	if err := compWriter.Close(); err != nil {
		return 0, NewCoreError(ErrCompression, "failed to flush compression writer").Wrap(err)
	}

	writtenBytes = counter.total
	c.log.WithField("bytes_written", writtenBytes).Info("Compression stream finished")
	return writtenBytes, nil
}

// Decompress streams data from a reader, decompresses it, and writes it to a writer.
func (c *Compressor) Decompress(dst io.Writer, src io.Reader, compType CompressionType) (int64, error) {
	c.log.WithField("algorithm", compType).Info("Starting decompression stream")

	// Acquire a worker from the pool.
	c.workerPool <- struct{}{}
	defer func() { <-c.workerPool }()

	var compReader io.ReadCloser

	switch compType {
	case ZSTD:
		// Get a decoder from the pool and reset it to read from our source.
		zstdReader := c.zstdDecoder.Get().(*zstd.Decoder)
		if err := zstdReader.Reset(src); err != nil {
			c.zstdDecoder.Put(zstdReader)
			return 0, NewCoreError(ErrDecompression, "failed to reset zstd decoder").Wrap(err)
		}
		defer func() {
			zstdReader.Close()
			c.zstdDecoder.Put(zstdReader) // Return decoder to the pool.
		}()
		compReader = zstdReader

	case GZIP:
		gzipReader, err := gzip.NewReader(src)
		if err != nil {
			return 0, NewCoreError(ErrDecompression, "failed to create gzip reader").Wrap(err)
		}
		defer gzipReader.Close()
		compReader = gzipReader

	default:
		return 0, NewCoreError(ErrUnsupportedAlgorithm, "unsupported compression type: "+string(compType))
	}

	// Stream the decompressed data to the destination.
	writtenBytes, err := io.Copy(dst, compReader)
	if err != nil {
		return 0, NewCoreError(ErrDecompression, "failed during data streaming").Wrap(err)
	}

	c.log.WithField("bytes_written", writtenBytes).Info("Decompression stream finished")
	return writtenBytes, nil
}

// writeCounter is a helper struct to count bytes written to an io.Writer.
type writeCounter struct {
	writer io.Writer
	total  int64
}

func (wc *writeCounter) Write(p []byte) (int, error) {
	n, err := wc.writer.Write(p)
	wc.total += int64(n)
	return n, err
}
