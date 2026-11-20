// analyzer.go
// Dewey.Decimal: text statistics. Launcher for go/dewey; the algorithm is specified in spec/SPEC.md.
package main

import (
	"os"

	"github.com/AndMaverick/dewey.decimal/go/dewey"
)

func main() { os.Exit(dewey.Main(os.Args[1:])) }
