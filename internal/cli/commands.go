// Package cli centralizes all cobra command definitions and their execution logic.
package cli

import (
	"fmt"
	"os"
	"strconv"

	"github.com/nexus/nsm/internal/api"
	"github.com/nexus/nsm/internal/auth"
	"github.com/nexus/nsm/internal/core"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	// For progress bars, a library like "github.com/vbauerster/mpb/v8" would be used.
)

// NewRootCmd creates the root command and adds all subcommands to it.
func NewRootCmd() *cobra.Command {
	rootCmd := &cobra.Command{
		Use:   "nsm",
		Short: "NSM (Nexus Simple Memory) is an intelligent compression tool.",
		Long: `A next-generation tool for compressing large files with high efficiency,
featuring a token-based usage system and an integrated marketplace.`,
	}

	// Add subcommands
	rootCmd.AddCommand(createCreateCmd())
	rootCmd.AddCommand(createExtractCmd())
	rootCmd.AddCommand(createSearchCmd())
	rootCmd.AddCommand(createBuyTokensCmd())
	rootCmd.AddCommand(createServerCmd())

	return rootCmd
}

// createCreateCmd defines the 'create' command.
func createCreateCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "create <output.nsm> <input_file...>",
		Short: "Create a compressed .nsm archive from one or more files.",
		Args:  cobra.MinimumNArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			outputFile := args[0]
			inputFiles := args[1:]

			// Placeholder for core engine initialization
			engine, err := core.NewEngine(&core.Config{}) // Config would be loaded from file
			if err != nil {
				return fmt.Errorf("failed to initialize core engine: %w", err)
			}

			logrus.WithFields(logrus.Fields{
				"output": outputFile,
				"inputs": len(inputFiles),
			}).Info("Starting archive creation")

			// Here you would initialize a progress bar.
			// e.g., p := mpb.New( ... )
			// bar := p.AddBar( ... )

			if err := engine.Create(outputFile, inputFiles); err != nil {
				// The actual implementation in engine.Create would update the progress bar.
				return fmt.Errorf("archive creation failed: %w", err)
			}

			fmt.Println("Archive created successfully:", outputFile)
			return nil
		},
	}
}

// createExtractCmd defines the 'extract' command.
func createExtractCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "extract <archive.nsm> <destination_path>",
		Short: "Extract files from a .nsm archive.",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			// Placeholder for core engine logic
			fmt.Println("Placeholder: Archive extraction logic goes here.")
			return nil
		},
	}
}

// createSearchCmd defines the 'search' command.
func createSearchCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "search <archive.nsm> <query>",
		Short: "Perform a full-text search within a .nsm archive.",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			// Placeholder for core engine logic
			fmt.Println("Placeholder: Full-text search logic goes here.")
			return nil
		},
	}
}

// createBuyTokensCmd defines the 'buy-tokens' command.
func createBuyTokensCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "buy-tokens <count>",
		Short: "Purchase more compression tokens from the marketplace.",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			count, err := strconv.Atoi(args[0])
			if err != nil || count <= 0 {
				return fmt.Errorf("invalid token count: must be a positive number")
			}

			// In a real app, baseURL and apiKey would come from config.
			marketplaceURL := "http://localhost:8080"
			apiKey, _ := cmd.Flags().GetString("license-key")
			if apiKey == "" {
				return fmt.Errorf("a license key is required to buy tokens. Use --license-key")
			}
			
			client := auth.NewMarketplaceClient(marketplaceURL, apiKey)
			
			fmt.Printf("Attempting to purchase %d token(s)...\n", count)
			resp, err := client.InitiatePurchase(count)
			if err != nil {
				return fmt.Errorf("could not initiate purchase: %w", err)
			}

			fmt.Println("\n--- Please complete your payment ---")
			fmt.Printf("Open this URL in your browser:\n%s\n\n", resp.PaymentURL)
			fmt.Println("After payment, your new tokens will be synced automatically.")
			return nil
		},
	}
}

// createServerCmd defines the 'server' command.
func createServerCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "server",
		Short: "Run the web server for the marketplace and API.",
		RunE: func(cmd *cobra.Command, args []string) error {
			port, _ := cmd.Flags().GetInt("port")
			
			logrus.WithField("port", port).Info("Starting NSM API server...")
			
			// Initialize the server
			server, err := api.NewServer()
			if err != nil {
				return fmt.Errorf("failed to initialize server: %w", err)
			}
			
			// Start listening
			return server.Run(fmt.Sprintf(":%d", port))
		},
	}
	cmd.Flags().IntP("port", "p", 8080, "Port to run the server on")
	return cmd
}
