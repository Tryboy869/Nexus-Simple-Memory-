// Package main is the entry point for the NSM command-line interface.
// It uses the Cobra library to create a powerful and structured CLI application.
package main

import (
	"fmt"
	"os"

	"github.com/nexus/nsm/internal/core"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

// Global variables for command-line flags.
var (
	licenseKey string
	verbose    bool
	configFile string
)

// rootCmd represents the base command when called without any subcommands.
var rootCmd = &cobra.Command{
	Use:   "nsm",
	Short: "NSM (Nexus Simple Memory) is an intelligent compression tool.",
	Long: `NSM is a next-generation tool for compressing large files with high efficiency.
It features a token-based usage system and integrates with a marketplace for purchasing additional tokens.`,
	// This function is run before any command's Run function.
	// It's used here to configure the logging level based on the --verbose flag.
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		if verbose {
			logrus.SetLevel(logrus.DebugLevel)
		} else {
			logrus.SetLevel(logrus.InfoLevel)
		}
		logrus.SetFormatter(&logrus.JSONFormatter{})
		logrus.Info("NSM CLI initialized")
	},
}

// init function is called by Go when the package is initialized.
// It's used here to define all the commands and flags.
func init() {
	// Global flags available to all commands.
	rootCmd.PersistentFlags().StringVar(&licenseKey, "license-key", "", "Your API/license key for token validation")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose output for debugging")
	rootCmd.PersistentFlags().StringVar(&configFile, "config", "", "Path to a custom configuration file (default is $HOME/.nsm.yaml)")

	// --- Command Definitions ---
	// Each command is added to the root command.
	// The actual logic is delegated to the 'internal/core' package to keep 'main' clean.
	rootCmd.AddCommand(createCmd)
	rootCmd.AddCommand(extractCmd)
	rootCmd.AddCommand(searchCmd)
	rootCmd.AddCommand(buyTokensCmd)
	rootCmd.AddCommand(serverCmd)
}

// --- Individual Command Implementations ---

var createCmd = &cobra.Command{
	Use:   "create [output.nsm] [input_file...]",
	Short: "Create a compressed .nsm archive from one or more files.",
	Args:  cobra.MinimumNArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		logrus.WithFields(logrus.Fields{
			"output": args[0],
			"inputs": args[1:],
		}).Info("Starting archive creation")
		// Placeholder for the core logic call
		// engine, err := core.NewEngine(...)
		// err := engine.Create(args[0], args[1:])
		fmt.Println("Placeholder: Archive creation logic goes here.")
	},
}

var extractCmd = &cobra.Command{
	Use:   "extract [archive.nsm] [destination_path]",
	Short: "Extract files from a .nsm archive.",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		logrus.WithFields(logrus.Fields{
			"archive":     args[0],
			"destination": args[1],
		}).Info("Starting archive extraction")
		// Placeholder for the core logic call
		fmt.Println("Placeholder: Archive extraction logic goes here.")
	},
}

var searchCmd = &cobra.Command{
	Use:   "search [archive.nsm] [query]",
	Short: "Perform a full-text search within a .nsm archive.",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		logrus.WithFields(logrus.Fields{
			"archive": args[0],
			"query":   args[1],
		}).Info("Performing search in archive")
		// Placeholder for the core logic call
		fmt.Println("Placeholder: Full-text search logic goes here.")
	},
}

var buyTokensCmd = &cobra.Command{
	Use:   "buy-tokens",
	Short: "Open the web marketplace to buy more compression tokens.",
	Run: func(cmd *cobra.Command, args []string) {
		logrus.Info("Opening marketplace...")
		// This would typically open a browser or provide a URL.
		fmt.Println("Please visit https://your-marketplace.com/buy to purchase tokens.")
		fmt.Println("Use 'nsm --license-key YOUR_NEW_KEY' after purchase.")
	},
}

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Run the web server for the marketplace and API.",
	Run: func(cmd *cobra.Command, args []string) {
		logrus.Info("Starting NSM web server...")
		// Placeholder for the web server initialization
		// The server logic would be in another package, e.g., 'internal/server'
		fmt.Println("Placeholder: Web server startup logic goes here.")
	},
}

// main is the ultimate entry point of the application.
func main() {
	if err := rootCmd.Execute(); err != nil {
		logrus.WithError(err).Fatal("Failed to execute command")
		os.Exit(1)
	}
}
