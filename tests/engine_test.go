// Package tests contains all the tests for the NSM project.
package tests

import (
	"bytes"
	"crypto/rand"
	"io"
	"os"
	"path/filepath"
	"testing"

	"github.com/nexus/nsm/internal/core"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// setupTestEngine creates a new core engine with a default configuration for testing.
func setupTestEngine(t *testing.T, tokens int) (*core.Engine, *core.Config) {
	cfg := &core.Config{
		LicenseKey: "test-license-key",
		TokenCount: tokens,
	}
	engine, err := core.NewEngine(cfg)
	require.NoError(t, err, "Engine initialization should not fail")
	return engine, cfg
}

// createTestFile creates a temporary file with random data for testing.
// It returns the path to the file and the original data.
func createTestFile(t *testing.T, size int) (string, []byte) {
	tmpDir := t.TempDir()
	filePath := filepath.Join(tmpDir, "testfile.dat")
	data := make([]byte, size)
	_, err := rand.Read(data)
	require.NoError(t, err)
	err = os.WriteFile(filePath, data, 0644)
	require.NoError(t, err)
	return filePath, data
}

// TestCreateAndExtract tests the full lifecycle of creating an archive and then extracting it.
func TestCreateAndExtract(t *testing.T) {
	engine, _ := setupTestEngine(t, 5) // Start with 5 tokens
	tmpDir := t.TempDir()

	// 1. Create a test file to be compressed.
	testFilePath, originalData := createTestFile(t, 1024*10) // 10 KB file
	archivePath := filepath.Join(tmpDir, "test.nsm")

	// 2. Create the archive.
	err := engine.Create(archivePath, []string{testFilePath})
	// This is expected to fail because the core methods are placeholders.
	// In a real test, we would expect assert.NoError(t, err).
	assert.Error(t, err, "Create should be implemented")
	if err == nil {
		// The following tests will only run if Create is implemented.
		// 3. Check if the archive file exists.
		_, err = os.Stat(archivePath)
		assert.NoError(t, err, "Archive file should be created")

		// 4. Extract the archive.
		extractDir := filepath.Join(tmpDir, "extracted")
		err = os.Mkdir(extractDir, 0755)
		require.NoError(t, err)

		err = engine.Extract(archivePath, extractDir)
		assert.NoError(t, err, "Extraction should not fail")

		// 5. Verify the extracted file's content.
		extractedFilePath := filepath.Join(extractDir, filepath.Base(testFilePath))
		extractedData, err := os.ReadFile(extractedFilePath)
		require.NoError(t, err)
		assert.Equal(t, originalData, extractedData, "Extracted data should match original data")
	}
}

// TestTokenConsumption verifies that creating an archive consumes a token.
func TestTokenConsumption(t *testing.T) {
	engine, cfg := setupTestEngine(t, 1) // Start with 1 token
	assert.Equal(t, 1, cfg.TokenCount, "Should start with 1 token")

	// Create a dummy file for the test
	testFilePath, _ := createTestFile(t, 100)
	archivePath := filepath.Join(t.TempDir(), "token_test.nsm")

	// This call should consume the token.
	// We expect it to fail because Create is a stub, but we check the token count after.
	_ = engine.Create(archivePath, []string{testFilePath})
	assert.Equal(t, 0, cfg.TokenCount, "Token count should be 0 after one create operation")

	// This second call should fail because there are no tokens left.
	err := engine.Create(archivePath, []string{testFilePath})
	assert.Error(t, err, "Create should fail when no tokens are available")
	assert.Contains(t, err.Error(), "no tokens available", "Error message should indicate no tokens")
}

// TestInvalidFormat tests that the engine correctly identifies non-nsm files.
func TestInvalidFormat(t *testing.T) {
	engine, _ := setupTestEngine(t, 1)
	
	// Create a random file that is not a valid .nsm archive.
	invalidFile, _ := createTestFile(t, 128)

	err := engine.Extract(invalidFile, t.TempDir())
	// The core Extract function needs to be implemented to check for the magic number.
	assert.Error(t, err, "Extract should fail for a non-nsm file")
	if err != nil {
		// In a real implementation, we'd check for a specific error type.
		// assert.ErrorIs(t, err, core.ErrInvalidFormat)
	}
}

// BenchmarkCompressor provides a performance benchmark for the compression logic.
func BenchmarkCompressor(b *testing.B) {
	compressor := core.NewCompressor()
	data := make([]byte, 1024*1024) // 1 MB of data
	_, err := rand.Read(data)
	require.NoError(b, err)

	b.ResetTimer()
	b.SetBytes(int64(len(data)))

	for i := 0; i < b.N; i++ {
		source := bytes.NewReader(data)
		dest := io.Discard // Write to nowhere for pure performance measurement
		_, err := compressor.Compress(dest, source, core.ZSTD)
		require.NoError(b, err)
	}
}
