// analyzer.go
// Dewey.Decimal 📚
// A text analysis toolkit for decision-ready insights.

package main

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"os"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run analyzer.go <file>")
		return
	}

	filePath := os.Args[1]
	content, err := ioutil.ReadFile(filePath)
	if err != nil {
		fmt.Println("Error reading file:", err)
		return
	}

	text := string(content)

	// Word & char counts
	words := strings.Fields(text)
	wordCount := len(words)
	charCount := len(text)

	// Most common words
	freq := make(map[string]int)
	for _, w := range words {
		w = strings.ToLower(strings.Trim(w, ".,!?;:\"'"))
		if w != "" {
			freq[w]++
		}
	}
	common := topWords(freq, 5)

	// Print results
	fmt.Printf("📊 Analysis of: %s\n", filePath)
	fmt.Printf("Words: %d\n", wordCount)
	fmt.Printf("Characters: %d\n", charCount)
	fmt.Printf("Most common words: %v\n", common)
}

// Get top N most common words
func topWords(freq map[string]int, n int) []string {
	result := []string{}
	for w := range freq {
		result = append(result, w)
	}
	// Simple sort by frequency
	for i := 0; i < len(result); i++ {
		for j := i + 1; j < len(result); j++ {
			if freq[result[j]] > freq[result[i]] {
				result[i], result[j] = result[j], result[i]
			}
		}
	}
	if len(result) > n {
		return result[:n]
	}
	return result
}
