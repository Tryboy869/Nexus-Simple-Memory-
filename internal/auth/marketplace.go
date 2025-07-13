// Package auth handles token management, validation, and persistence.
package auth

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/sirupsen/logrus"
)

// MarketplaceClient is a client for interacting with the NSM marketplace API.
type MarketplaceClient struct {
	BaseURL    string
	APIKey     string
	HTTPClient *http.Client
	log        *logrus.Entry
}

// NewMarketplaceClient creates a new client for the NSM marketplace.
func NewMarketplaceClient(baseURL, apiKey string) *MarketplaceClient {
	return &MarketplaceClient{
		BaseURL: baseURL,
		APIKey:  apiKey,
		HTTPClient: &http.Client{
			Timeout: 15 * time.Second,
		},
		log: logrus.WithField("component", "marketplace_client"),
	}
}

// PurchaseRequest defines the payload for requesting a token purchase.
type PurchaseRequest struct {
	TokenCount int `json:"token_count"`
}

// PurchaseResponse defines the expected response after initiating a purchase.
type PurchaseResponse struct {
	PaymentURL string `json:"payment_url"` // URL to redirect the user to for PayPal payment
	OrderID    string `json:"order_id"`
}

// InitiatePurchase sends a request to the marketplace to create a new payment order.
// It returns a URL for the user to complete the payment.
func (c *MarketplaceClient) InitiatePurchase(count int) (*PurchaseResponse, error) {
	if count <= 0 {
		return nil, fmt.Errorf("token count must be positive")
	}

	reqBody, err := json.Marshal(PurchaseRequest{TokenCount: count})
	if err != nil {
		return nil, fmt.Errorf("failed to create purchase request body: %w", err)
	}

	endpoint := fmt.Sprintf("%s/api/v1/tokens/purchase", c.BaseURL)
	req, err := http.NewRequest("POST", endpoint, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create http request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.APIKey)

	c.log.WithField("endpoint", endpoint).Info("Initiating token purchase")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to communicate with marketplace: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("marketplace returned an error (status %d)", resp.StatusCode)
	}

	var purchaseResp PurchaseResponse
	if err := json.NewDecoder(resp.Body).Decode(&purchaseResp); err != nil {
		return nil, fmt.Errorf("failed to decode purchase response: %w", err)
	}

	return &purchaseResp, nil
}

// ValidationResponse defines the structure of a successful key validation.
type ValidationResponse struct {
	IsValid         bool      `json:"is_valid"`
	AvailableTokens int       `json:"available_tokens"`
	LastSync        time.Time `json:"last_sync"`
}

// ValidateAPIKey checks an API key against the marketplace and returns its token status.
func (c *MarketplaceClient) ValidateAPIKey() (*ValidationResponse, error) {
	endpoint := fmt.Sprintf("%s/api/v1/tokens/validate", c.BaseURL)
	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create validation request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+c.APIKey)

	c.log.Info("Validating API key with marketplace")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to communicate with marketplace: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("marketplace returned an error (status %d)", resp.StatusCode)
	}

	var validationResp ValidationResponse
	if err := json.NewDecoder(resp.Body).Decode(&validationResp); err != nil {
		return nil, fmt.Errorf("failed to decode validation response: %w", err)
	}

	return &validationResp, nil
}
