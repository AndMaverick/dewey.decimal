// Package dewey is the Go implementation of Dewey.Decimal. The normative text is spec/SPEC.md; the Python and
// JavaScript versions must print the same bytes.
package dewey

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"regexp"
	"sort"
	"strings"
	"unicode"
	"unicode/utf8"

	"github.com/AndMaverick/dewey.decimal/spec"
)

var (
	stop          = map[string]map[string]bool{"en": wordSet("stopwords_en.txt"), "de": wordSet("stopwords_de.txt")}
	abbreviations = wordSet("abbreviations.txt")
	lexicon       = map[string]map[string]int{"en": loadLexicon("sentiment_en.json"), "de": loadLexicon("sentiment_de.json")}
	negators      = map[string]map[string]bool{}
	boosters      = map[string]float64{}

	enSilent = regexp.MustCompile(`(?:[^laeiouy]es|[^td]ed|[^laeiouy]e)$`)
	enGroups = regexp.MustCompile(`[aeiouy]{1,2}`)
	deRuns   = regexp.MustCompile(`[aeiouyäöü]+`)
)

func init() {
	raw, err := spec.FS.ReadFile("modifiers.json")
	must(err)
	var m struct {
		Negators map[string][]string `json:"negators"`
		Boosters map[string]float64  `json:"boosters"`
	}
	must(json.Unmarshal(raw, &m))
	for k, v := range m.Negators {
		negators[k] = map[string]bool{}
		for _, w := range v {
			negators[k][w] = true
		}
	}
	boosters = m.Boosters
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}

func wordSet(name string) map[string]bool {
	raw, err := spec.FS.ReadFile(name)
	must(err)
	out := map[string]bool{}
	for _, w := range strings.Fields(string(raw)) {
		out[w] = true
	}
	return out
}

func loadLexicon(name string) map[string]int {
	raw, err := spec.FS.ReadFile(name)
	must(err)
	out := map[string]int{}
	must(json.Unmarshal(raw, &out))
	return out
}

func isSpace(r rune) bool {
	switch {
	case r >= 0x09 && r <= 0x0d, r == 0x20, r == 0x85, r == 0xa0, r == 0x1680, r >= 0x2000 && r <= 0x200a,
		r == 0x2028, r == 0x2029, r == 0x202f, r == 0x205f, r == 0x3000:
		return true
	}
	return false
}

func isLetter(r rune) bool     { return unicode.IsLetter(r) || unicode.IsMark(r) }
func isDigit(r rune) bool      { return unicode.IsDigit(r) }
func isTerminator(r rune) bool { return r == '.' || r == '!' || r == '?' || r == 0x2026 }
func isCloser(r rune) bool {
	return r == '"' || r == '\'' || r == ')' || r == ']' || r == 0xbb || r == 0x201d || r == 0x2019
}
func isConnector(r rune) bool { return r == '\'' || r == 0x2019 || r == '-' }

func lower(rs []rune) string {
	var b strings.Builder
	for _, r := range rs {
		if r == 0x130 {
			b.WriteRune(r)
		} else {
			b.WriteRune(unicode.ToLower(r))
		}
	}
	return b.String()
}

type scanResult struct {
	words                          []string
	numbers, sentences, paragraphs int
}

func scan(text []rune) scanResult {
	n := len(text)
	res := scanResult{}
	hasWord, hasText := false, false
	lastEnd, lastWord := -1, ""
	i := 0
	for i < n {
		c := text[i]
		switch {
		case isLetter(c):
			j := i + 1
			for j < n && (isLetter(text[j]) || (isConnector(text[j]) && j+1 < n && isLetter(text[j+1]))) {
				j++
			}
			w := lower(text[i:j])
			res.words = append(res.words, w)
			lastWord, lastEnd = w, j
			hasWord, hasText = true, true
			i = j
		case isDigit(c):
			j := i + 1
			for j < n && (isDigit(text[j]) || ((text[j] == '.' || text[j] == ',') && j+1 < n && isDigit(text[j+1]))) {
				j++
			}
			res.numbers++
			hasText = true
			i = j
		case isTerminator(c):
			j := i
			for j < n && isTerminator(text[j]) {
				j++
			}
			runEnd := j
			for j < n && isCloser(text[j]) {
				j++
			}
			hasText = true
			if j >= n || isSpace(text[j]) {
				singleDot := runEnd == i+1 && text[i] == '.' && j == runEnd
				if !(singleDot && lastEnd == i && abbreviations[lastWord]) && hasWord {
					res.sentences++
					hasWord = false
				}
			}
			i = j
		case isSpace(c):
			j, breaks := i, 0
			for j < n && isSpace(text[j]) {
				if text[j] == '\r' {
					breaks++
					if j+1 < n && text[j+1] == '\n' {
						j++
					}
				} else if text[j] == '\n' {
					breaks++
				}
				j++
			}
			if breaks >= 2 {
				if hasWord {
					res.sentences++
					hasWord = false
				}
				if hasText {
					res.paragraphs++
					hasText = false
				}
			}
			i = j
		default:
			hasText = true
			i++
		}
	}
	if hasWord {
		res.sentences++
	}
	if hasText {
		res.paragraphs++
	}
	return res
}

func countLines(text []rune) int {
	if len(text) == 0 {
		return 0
	}
	breaks := 0
	for i := 0; i < len(text); i++ {
		if text[i] == '\r' {
			breaks++
			if i+1 < len(text) && text[i+1] == '\n' {
				i++
			}
		} else if text[i] == '\n' {
			breaks++
		}
	}
	last := text[len(text)-1]
	if last == '\r' || last == '\n' {
		return breaks
	}
	return breaks + 1
}

func detectLanguage(words []string) string {
	en, de := 0, 0
	for _, w := range words {
		if stop["en"][w] {
			en++
		}
		if stop["de"][w] {
			de++
		}
	}
	if en >= 3 && float64(en) >= float64(1.4*float64(de)) {
		return "en"
	}
	if de >= 3 && float64(de) >= float64(1.4*float64(en)) {
		return "de"
	}
	return "unknown"
}

func syllables(word, lang string) int {
	if lang == "de" {
		var b strings.Builder
		for _, ch := range word {
			if (ch >= 'a' && ch <= 'z') || ch == 'ä' || ch == 'ö' || ch == 'ü' || ch == 'ß' {
				b.WriteRune(ch)
			}
		}
		return max(1, len(deRuns.FindAllString(b.String(), -1)))
	}
	var b strings.Builder
	for _, ch := range word {
		if ch >= 'a' && ch <= 'z' {
			b.WriteRune(ch)
		}
	}
	w := b.String()
	if len(w) <= 3 {
		return 1
	}
	if loc := enSilent.FindStringIndex(w); loc != nil {
		w = w[:loc[0]] + w[loc[1]:]
	}
	w = strings.TrimPrefix(w, "y")
	return max(1, len(enGroups.FindAllString(w, -1)))
}

// R is a value rounded to hundredths, carried as an exact integer.
type R struct{ H int }

func round2(x float64) R {
	r := int(math.Floor(math.Abs(x)*100 + 0.5))
	if x < 0 {
		r = -r
	}
	return R{r}
}

// Fixed writes hundredths with exactly two decimals.
func Fixed(h int) string {
	a := h
	sign := ""
	if h < 0 {
		a, sign = -h, "-"
	}
	return fmt.Sprintf("%s%d.%02d", sign, a/100, a%100)
}

func short(h int) string {
	a := h
	if a < 0 {
		a = -a
	}
	whole, frac := a/100, a%100
	var body string
	switch {
	case frac == 0:
		body = fmt.Sprintf("%d", whole)
	case frac%10 == 0:
		body = fmt.Sprintf("%d.%d", whole, frac/10)
	default:
		body = fmt.Sprintf("%d.%02d", whole, frac)
	}
	if h < 0 && a != 0 {
		return "-" + body
	}
	return body
}

// mul keeps every product rounded to a double before it is added, so no platform fuses a multiply and an add.
func mul(a, b float64) float64 { return float64(a * b) }

func readability(words []string, sentences int, lang string) map[string]any {
	if lang == "unknown" || len(words) == 0 || sentences == 0 {
		return nil
	}
	w, s := float64(len(words)), float64(sentences)
	var y, c, long, o int
	for _, x := range words {
		k := syllables(x, lang)
		y += k
		if k >= 3 {
			c++
		}
		if utf8.RuneCountInString(x) > 6 {
			long++
		}
		if k == 1 {
			o++
		}
	}
	yf, cf, lf, of := float64(y), float64(c), float64(long), float64(o)
	if lang == "en" {
		return map[string]any{
			"flesch_reading_ease":  round2(206.835 - mul(1.015, w/s) - mul(84.6, yf/w)),
			"flesch_kincaid_grade": round2(mul(0.39, w/s) + mul(11.8, yf/w) - 15.59),
			"gunning_fog":          round2(mul(0.4, (w/s)+mul(100, cf/w))),
		}
	}
	ms, sl, iw, es := 100*cf/w, w/s, 100*lf/w, 100*of/w
	return map[string]any{
		"flesch_amstad":     round2(180 - w/s - mul(58.5, yf/w)),
		"wiener_sachtext_1": round2(mul(0.1935, ms) + mul(0.1672, sl) + mul(0.1297, iw) - mul(0.0327, es) - 0.875),
	}
}

func sentiment(words []string, lang string) map[string]any {
	if lang == "unknown" {
		return nil
	}
	lex, neg := lexicon[lang], negators[lang]
	raw := 0.0
	pos, negc := 0, 0
	for i, w := range words {
		v0, ok := lex[w]
		if !ok {
			continue
		}
		if v0 > 0 {
			pos++
		}
		if v0 < 0 {
			negc++
		}
		v := float64(v0)
		if i > 0 {
			if b, ok := boosters[words[i-1]]; ok {
				v = mul(v, 1+b)
			}
		}
		for k := max(0, i-3); k < i; k++ {
			if neg[words[k]] {
				v = mul(v, -0.75)
				break
			}
		}
		raw += v
	}
	score := raw / math.Sqrt(mul(raw, raw)+15)
	label := "neutral"
	if score >= 0.05 {
		label = "positive"
	} else if score <= -0.05 {
		label = "negative"
	}
	return map[string]any{"score": round2(score), "label": label, "positive_hits": pos, "negative_hits": negc}
}

// Analyse returns the result tree of spec section 9. lang is "en", "de" or "" for detection.
func Analyse(text string, lang string) map[string]any {
	rs := []rune(text)
	sc := scan(rs)
	language := lang
	if language != "en" && language != "de" {
		language = detectLanguage(sc.words)
	}
	counts := map[string]int{}
	unique := map[string]bool{}
	for _, w := range sc.words {
		unique[w] = true
		if utf8.RuneCountInString(w) >= 3 && !stop["en"][w] && !stop["de"][w] {
			counts[w]++
		}
	}
	type kv struct {
		w string
		c int
	}
	var all []kv
	for w, c := range counts {
		all = append(all, kv{w, c})
	}
	sort.Slice(all, func(i, j int) bool {
		if all[i].c != all[j].c {
			return all[i].c > all[j].c
		}
		return all[i].w < all[j].w
	})
	top := []any{}
	for i := 0; i < len(all) && i < 5; i++ {
		top = append(top, map[string]any{"count": all[i].c, "term": all[i].w})
	}
	nonSpace := 0
	for _, r := range rs {
		if !isSpace(r) {
			nonSpace++
		}
	}
	out := map[string]any{
		"characters": len(rs), "characters_no_space": nonSpace, "language": language, "lines": countLines(rs),
		"numbers": sc.numbers, "paragraphs": sc.paragraphs, "sentences": sc.sentences, "top_terms": top,
		"unique_words": len(unique), "words": len(sc.words),
		"readability": nil, "sentiment": nil,
	}
	if r := readability(sc.words, sc.sentences, language); r != nil {
		out["readability"] = r
	}
	if s := sentiment(sc.words, language); s != nil {
		out["sentiment"] = s
	}
	return out
}

func quote(v string) string {
	var b strings.Builder
	b.WriteByte('"')
	for _, ch := range v {
		switch {
		case ch == '"':
			b.WriteString(`\"`)
		case ch == '\\':
			b.WriteString(`\\`)
		case ch < 0x20:
			fmt.Fprintf(&b, `\u%04x`, ch)
		default:
			b.WriteRune(ch)
		}
	}
	b.WriteByte('"')
	return b.String()
}

func dump(v any, depth int) string {
	pad, inner := strings.Repeat("  ", depth), strings.Repeat("  ", depth+1)
	switch x := v.(type) {
	case nil:
		return "null"
	case R:
		return short(x.H)
	case int:
		return fmt.Sprintf("%d", x)
	case string:
		return quote(x)
	case []any:
		if len(x) == 0 {
			return "[]"
		}
		parts := make([]string, len(x))
		for i, e := range x {
			parts[i] = inner + dump(e, depth+1)
		}
		return "[\n" + strings.Join(parts, ",\n") + "\n" + pad + "]"
	case map[string]any:
		keys := make([]string, 0, len(x))
		for k := range x {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		if len(keys) == 0 {
			return "{}"
		}
		parts := make([]string, len(keys))
		for i, k := range keys {
			parts[i] = inner + quote(k) + ": " + dump(x[k], depth+1)
		}
		return "{\n" + strings.Join(parts, ",\n") + "\n" + pad + "}"
	}
	panic(fmt.Sprintf("dewey: cannot write %T", v))
}

// ToJSON is the canonical output of spec section 9.
func ToJSON(v any) string { return dump(v, 0) + "\n" }

func thousands(n int) string {
	s := fmt.Sprintf("%d", n)
	neg := strings.HasPrefix(s, "-")
	s = strings.TrimPrefix(s, "-")
	var parts []string
	for len(s) > 3 {
		parts = append([]string{s[len(s)-3:]}, parts...)
		s = s[:len(s)-3]
	}
	parts = append([]string{s}, parts...)
	out := strings.Join(parts, ",")
	if neg {
		return "-" + out
	}
	return out
}

// Render is the human readable report.
func Render(name string, a map[string]any) string {
	var lines []string
	lines = append(lines, "Analysis of "+name,
		fmt.Sprintf("  Words: %s   Sentences: %s   Paragraphs: %s", thousands(a["words"].(int)), thousands(a["sentences"].(int)), thousands(a["paragraphs"].(int))),
		fmt.Sprintf("  Characters: %s (%s without spaces)   Language: %s", thousands(a["characters"].(int)), thousands(a["characters_no_space"].(int)), a["language"].(string)))
	var terms []string
	for _, t := range a["top_terms"].([]any) {
		m := t.(map[string]any)
		terms = append(terms, fmt.Sprintf("%s (%d)", m["term"].(string), m["count"].(int)))
	}
	if len(terms) == 0 {
		terms = []string{"none"}
	}
	lines = append(lines, "  Top terms: "+strings.Join(terms, ", "))
	if s, ok := a["sentiment"].(map[string]any); ok {
		h := s["score"].(R).H
		sign := ""
		if h >= 0 {
			sign = "+"
		}
		lines = append(lines, fmt.Sprintf("  Sentiment: %s (%s%s; %d positive and %d negative words)", s["label"].(string), sign, Fixed(h), s["positive_hits"].(int), s["negative_hits"].(int)))
	}
	if r, ok := a["readability"].(map[string]any); ok {
		keys := make([]string, 0, len(r))
		for k := range r {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		var parts []string
		for _, k := range keys {
			parts = append(parts, strings.ReplaceAll(k, "_", " ")+" "+Fixed(r[k].(R).H))
		}
		lines = append(lines, "  Readability: "+strings.Join(parts, ", "))
	}
	return strings.Join(lines, "\n") + "\n"
}

// Main runs the command line: FILE... [--json] [--lang en|de]. It returns the exit code.
func Main(args []string) int {
	asJSON, lang := false, ""
	var files []string
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--json":
			asJSON = true
		case "--lang":
			if i+1 >= len(args) || (args[i+1] != "en" && args[i+1] != "de") {
				fmt.Fprintln(os.Stderr, "error: --lang must be en or de")
				return 2
			}
			lang = args[i+1]
			i++
		default:
			files = append(files, args[i])
		}
	}
	if len(files) == 0 {
		fmt.Fprintln(os.Stderr, "usage: analyzer FILE... [--json] [--lang en|de]")
		return 2
	}
	results := map[string]any{}
	for _, f := range files {
		raw, err := os.ReadFile(f)
		if err == nil && !utf8.Valid(raw) {
			err = fmt.Errorf("not valid UTF-8")
		}
		if err != nil {
			fmt.Fprintf(os.Stderr, "error: cannot read %s: %v\n", f, err)
			return 2
		}
		results[f] = Analyse(string(raw), lang)
	}
	if asJSON {
		if len(files) == 1 {
			fmt.Print(ToJSON(results[files[0]]))
		} else {
			fmt.Print(ToJSON(results))
		}
		return 0
	}
	for _, f := range files {
		fmt.Print(Render(f, results[f].(map[string]any)))
	}
	return 0
}
