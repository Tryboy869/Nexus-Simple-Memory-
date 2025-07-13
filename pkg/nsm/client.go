// Package nsm provides a high-level client library for interacting with the
// NSM (Nexus Simple Memory) compression and marketplace services.
// It simplifies the process of creating, extracting, and searching archives
// by managing configuration and token authentication automatically.
package nsm

import (
	"fmt"
	"os"
	"sync"

	"github.com/nexus/nsm/internal/auth"
	"github.com/nexus/nsm/internal/core"
	"github.com/sirupsen/logrus"
)

// Client is the main entry point for the NSM library. It provides thread-safe
// methods to interact with NSM functionalities.
type Client struct {
	engine       *core.Engine
	tokenManager *auth.TokenManager
	config       Config
	mu           sync.RWMutex // Protects the client's internal state
}

// Config holds the configuration for the NSM client.
type Config struct {
	// LicenseKey is the user's unique key for authenticating with the marketplace
	// and syncing token counts.
	LicenseKey string

	// MarketplaceURL is the base URL of the NSM marketplace API.
	// Defaults to the official NSM marketplace if empty.
	MarketplaceURL string

	// LogLevel sets the verbosity of the client's logging.
	LogLevel logrus.Level
}

// NewClient creates and initializes a new NSM client.
// It sets up the core engine and token manager based on the provided configuration.
// It will attempt to load token state from the user's home directory.
//
// Example:
//   client, err := nsm.NewClient(nsm.Config{
//       LicenseKey: "YOUR-LICENSE-KEY-HERE",
//   })
//   if err != nil { ... }
func NewClient(cfg Config) (*Client, error) {
	logrus.SetLevel(cfg.LogLevel)

	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("failed to get user home directory: %w", err)
	}

	tm, err := auth.NewTokenManager(homeDir, cfg.LicenseKey)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize token manager: %w", err)
	}

	coreCfg := &core.Config{
		LicenseKey: cfg.LicenseKey,
		TokenCount: tm.AvailableTokens(),
	}
	engine, err := core.NewEngine(coreCfg)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize core engine: %w", err)
	}

	return &Client{
		engine:       engine,
		tokenManager: tm,
		config:       cfg,
	}, nil
}

// Create compresses a list of input files into a single .nsm archive.
// This operation consumes one token. If no tokens are available, it will return an error.
func (c *Client) Create(outputFile string, inputFiles []string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Consume a token before performing the operation.
	if err := c.tokenManager.ConsumeToken(); err != nil {
		return fmt.Errorf("token required for 'create' operation: %w", err)
	}

	// The core engine will perform the actual compression.
	// In a real implementation, you would pass progress callbacks here.
	return c.engine.Create(outputFile, inputFiles)
}

// Extract decompresses a .nsm archive to a specified destination directory.
// This operation does not consume any tokens.
func (c *Client) Extract(archiveFile, destinationPath string) error {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.engine.Extract(archiveFile, destinationPath)
}

// Search performs a full-text search within a .nsm archive.
// This operation does not consume any tokens.
func (c *Client) Search(archiveFile, query string) ([]string, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.engine.Search(archiveFile, query)
}

// BuyTokens initiates the token purchase process for a given number of tokens.
// It returns a payment URL that the user must visit to complete the transaction.
//
// Returns:
//   - paymentURL: The URL for the user to complete the PayPal payment.
//   - orderID: The unique ID for this transaction.
//   - error: An error if the purchase could not be initiated.
func (c *Client) BuyTokens(count int) (paymentURL, orderID string, err error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if c.config.LicenseKey == "" {
		return "", "", fmt.Errorf("a license key is required to buy tokens")
	}

	marketplaceURL := c.config.MarketplaceURL
	if marketplaceURL == "" {
		marketplaceURL = "https://api.nexus-memory.com" // Default production URL
	}

	client := auth.NewMarketplaceClient(marketplaceURL, c.config.LicenseKey)
	resp, err := client.InitiatePurchase(count)
	if err != nil {
		return "", "", err
	}

	return resp.PaymentURL, resp.OrderID, nil
}

// AvailableTokens returns the number of currently available tokens.
// It performs a thread-safe read of the token count.
func (c *Client) AvailableTokens() int {
	// The token manager is already thread-safe, so we don't need a client-level lock here.
	return c.tokenManager.AvailableTokens()
}
