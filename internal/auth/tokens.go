// Package auth handles token management, validation, and persistence.
package auth

import (
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/sirupsen/logrus"
)

const (
	// DefaultFreeTokens is the number of tokens a new user gets.
	DefaultFreeTokens = 1
	// TokenFileName is the name of the local file used to persist token state.
	TokenFileName = ".nsm-tokens"
)

var (
	ErrNoTokens         = errors.New("no compression tokens available")
	ErrValidationFailed = errors.New("token validation failed with marketplace API")
	ErrPersistence      = errors.New("failed to save or load token state")
)

// TokenState represents the data structure that is saved to the local file.
type TokenState struct {
	LicenseKey     string    `json:"license_key"`
	AvailableTokens int       `json:"available_tokens"`
	LastSync       time.Time `json:"last_sync"`
}

// TokenManager provides a thread-safe way to manage user tokens.
type TokenManager struct {
	state    *TokenState
	filePath string
	log      *logrus.Entry
	mu       sync.Mutex // Protects access to the state.
	client   *http.Client // HTTP client for online validation.
}

// NewTokenManager creates a new manager. It tries to load state from the local
// persistence file, or creates a new one with a free token if not found.
func NewTokenManager(homeDir, licenseKey string) (*TokenManager, error) {
	path := filepath.Join(homeDir, TokenFileName)
	log := logrus.WithField("component", "token_manager")

	tm := &TokenManager{
		filePath: path,
		log:      log,
		client:   &http.Client{Timeout: 10 * time.Second},
		state: &TokenState{
			LicenseKey:     licenseKey,
			AvailableTokens: 0, // Default to 0 before loading/creating.
		},
	}

	// Try to load existing state.
	err := tm.loadState()
	if err != nil {
		if os.IsNotExist(err) {
			// File doesn't exist, this is a first-time run.
			log.Info("No local token file found. Creating a new one with a free token.")
			tm.state.AvailableTokens = DefaultFreeTokens
			tm.state.LastSync = time.Now()
			if saveErr := tm.saveState(); saveErr != nil {
				return nil, saveErr
			}
		} else {
			// Another error occurred while loading.
			return nil, err
		}
	}

	// If a license key is provided via flags, it overrides the one in the file.
	if licenseKey != "" && tm.state.LicenseKey != licenseKey {
		log.WithFields(logrus.Fields{
			"old_key": tm.state.LicenseKey,
			"new_key": licenseKey,
		}).Info("License key updated. Forcing online sync.")
		tm.state.LicenseKey = licenseKey
		// In a real scenario, you would force a sync with the backend here.
		// go tm.ValidateOnline()
	}

	return tm, nil
}

// ConsumeToken checks for an available token, decrements the count, and persists the change.
// This operation is thread-safe.
func (tm *TokenManager) ConsumeToken() error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	if tm.state.AvailableTokens <= 0 {
		tm.log.Warn("Attempted to use token, but none are available.")
		// Optionally, trigger an online check to see if more tokens were purchased.
		// go tm.ValidateOnline()
		return ErrNoTokens
	}

	tm.state.AvailableTokens--
	tm.log.WithField("tokens_remaining", tm.state.AvailableTokens).Info("Token consumed.")

	// Persist the new state to the file.
	return tm.saveState()
}

// AvailableTokens returns the current number of available tokens.
func (tm *TokenManager) AvailableTokens() int {
	tm.mu.Lock()
	defer tm.mu.Unlock()
	return tm.state.AvailableTokens
}

// ValidateOnline contacts the marketplace API to sync the token count.
// This is a placeholder for the actual API call.
func (tm *TokenManager) ValidateOnline() error {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	if tm.state.LicenseKey == "" {
		tm.log.Info("Skipping online validation: no license key.")
		return nil
	}

	tm.log.Info("Contacting marketplace API for token validation...")
	// --- Placeholder for API call logic ---
	// resp, err := tm.client.Get("https://your-marketplace.com/api/validate?key=" + tm.state.LicenseKey)
	// if err != nil { return ErrValidationFailed }
	// defer resp.Body.Close()
	// var apiResponse struct { Tokens int `json:"tokens"` }
	// if err := json.NewDecoder(resp.Body).Decode(&apiResponse); err != nil { ... }
	// tm.state.AvailableTokens = apiResponse.Tokens
	// tm.state.LastSync = time.Now()
	// ------------------------------------

	// Simulate a successful API call that grants 5 tokens.
	tm.log.Info("Simulated API sync successful. Token count updated.")
	tm.state.AvailableTokens = 5
	tm.state.LastSync = time.Now()

	return tm.saveState()
}

// saveState writes the current token state to the JSON file.
func (tm *TokenManager) saveState() error {
	data, err := json.MarshalIndent(tm.state, "", "  ")
	if err != nil {
		tm.log.WithError(err).Error("Failed to marshal token state.")
		return ErrPersistence
	}

	// Write with permissions that restrict access to the current user.
	if err := os.WriteFile(tm.filePath, data, 0600); err != nil {
		tm.log.WithError(err).Error("Failed to write token file.")
		return ErrPersistence
	}
	return nil
}

// loadState reads the token state from the JSON file.
func (tm *TokenManager) loadState() error {
	data, err := os.ReadFile(tm.filePath)
	if err != nil {
		return err // Return original error to check for os.IsNotExist
	}

	newState := &TokenState{}
	if err := json.Unmarshal(data, newState); err != nil {
		tm.log.WithError(err).Error("Failed to unmarshal token file. The file might be corrupted.")
		return ErrPersistence
	}

	tm.state = newState
	tm.log.WithField("tokens_loaded", tm.state.AvailableTokens).Info("Token state loaded from file.")
	return nil
}
