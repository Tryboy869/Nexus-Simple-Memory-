// Package api sets up and runs the REST API server for NSM.
package api

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/nexus/nsm/internal/web" // For payment handlers
	"github.com/sirupsen/logrus"
	// For rate limiting, a library like "golang.org/x/time/rate" would be used.
)

// Server holds the dependencies for the API server.
type Server struct {
	router *mux.Router
	log    *logrus.Entry
	// Add dependencies like a database connection, core engine, etc.
	paymentHandler *web.PaymentHandler
}

// NewServer creates and configures a new API server instance.
func NewServer() (*Server, error) {
	// In a real application, these would be initialized with proper configuration.
	// For example, loading PayPal credentials from environment variables.
	payPalClient := &web.PayPalClient{ /* ... */ }
	paymentHandler := web.NewPaymentHandler(payPalClient, nil) // TokenManager would be initialized here.

	s := &Server{
		router:         mux.NewRouter(),
		log:            logrus.WithField("component", "api_server"),
		paymentHandler: paymentHandler,
	}

	s.setupRoutes()
	return s, nil
}

// setupRoutes defines all the API endpoints and their handlers.
func (s *Server) setupRoutes() {
	r := s.router
	
	// Apply middlewares to all routes.
	r.Use(loggingMiddleware)
	r.Use(corsMiddleware)
	// r.Use(authMiddleware) // Placeholder for API key authentication

	apiV1 := r.PathPrefix("/api/v1").Subrouter()

	// Token and Payment Endpoints
	apiV1.HandleFunc("/tokens/purchase", s.paymentHandler.HandleCreateOrder).Methods("POST")
	apiV1.HandleFunc("/tokens/validate", s.handleValidateToken).Methods("GET") // Placeholder

	// PayPal Webhook
	r.HandleFunc("/webhooks/paypal", s.paymentHandler.HandleWebhook).Methods("POST")

	// Core Functionality Endpoints
	apiV1.HandleFunc("/create", s.handleCreateArchive).Methods("POST")
	apiV1.HandleFunc("/extract/{id}", s.handleExtractArchive).Methods("GET") // ID would be a transaction/file ID
	apiV1.HandleFunc("/search", s.handleSearchArchive).Methods("POST")
}

// Run starts the HTTP server and handles graceful shutdown.
func (s *Server) Run(addr string) error {
	srv := &http.Server{
		Addr:    addr,
		Handler: s.router,
	}

	// Graceful shutdown logic
	idleConnsClosed := make(chan struct{})
	go func() {
		sigint := make(chan os.Signal, 1)
		signal.Notify(sigint, syscall.SIGINT, syscall.SIGTERM)
		<-sigint

		s.log.Info("Shutdown signal received, gracefully shutting down...")

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		if err := srv.Shutdown(ctx); err != nil {
			s.log.WithError(err).Error("Error during server shutdown")
		}
		close(idleConnsClosed)
	}()

	s.log.WithField("address", addr).Info("API server listening")
	if err := srv.ListenAndServe(); err != http.ErrServerClosed {
		return err
	}

	<-idleConnsClosed
	s.log.Info("Server shutdown complete.")
	return nil
}

// --- Middleware Definitions ---

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		logrus.WithFields(logrus.Fields{
			"method":   r.Method,
			"uri":      r.RequestURI,
			"duration": time.Since(start),
		}).Info("API request processed")
	})
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*") // Be more restrictive in production
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// --- Handler Stubs ---

func (s *Server) handleValidateToken(w http.ResponseWriter, r *http.Request) {
	// Placeholder: extract API key, check against database, return token count
	json.NewEncoder(w).Encode(map[string]interface{}{"is_valid": true, "available_tokens": 10})
}

func (s *Server) handleCreateArchive(w http.ResponseWriter, r *http.Request) {
	// Placeholder: handle multipart/form-data file upload, call core.Engine.Create
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{"status": "processing", "archive_id": "new-archive-123"})
}

func (s *Server) handleExtractArchive(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]
	// Placeholder: retrieve archive by ID and stream it back
	s.log.WithField("id", id).Info("Extract request received")
	w.WriteHeader(http.StatusOK)
}

func (s *Server) handleSearchArchive(w http.ResponseWriter, r *http.Request) {
	// Placeholder: get archive and query from request, call core.Engine.Search
	w.WriteHeader(http.StatusOK)
}
