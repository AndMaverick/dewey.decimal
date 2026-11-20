// Package spec carries the shared data files (stop words, sentiment lexicons, modifiers, abbreviations) into the Go build.
package spec

import "embed"

//go:embed stopwords_en.txt stopwords_de.txt abbreviations.txt sentiment_en.json sentiment_de.json modifiers.json
var FS embed.FS
