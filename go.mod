module github.com/nexus/nsm

go 1.20

require (
	github.com/gorilla/mux v1.8.1
	github.com/klauspost/compress v1.17.2 // Includes zstd
	github.com/sirupsen/logrus v1.9.3
	github.com/spf13/cobra v1.8.0
)

// Indirect dependencies are managed by Go's module system.
// They are included here for completeness but are not directly required in the code.
require (
	github.com/inconshreveable/mousetrap v1.1.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
	golang.org/x/sys v0.15.0 // indirect
)

require github.com/stretchr/testify v1.7.0

require (
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
