package dewey

import (
	"encoding/json"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

func load(t *testing.T, name string, v any) {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join("..", "..", "spec", name))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(raw, v); err != nil {
		t.Fatal(err)
	}
}

func TestVectors(t *testing.T) {
	var vs []struct {
		Name   string  `json:"name"`
		Text   string  `json:"text"`
		Lang   *string `json:"lang"`
		Expect string  `json:"expect"`
	}
	load(t, "vectors.json", &vs)
	for _, v := range vs {
		lang := ""
		if v.Lang != nil {
			lang = *v.Lang
		}
		if got := ToJSON(Analyse(v.Text, lang)); got != v.Expect {
			t.Errorf("%s: output differs from the vector\n%s", v.Name, got)
		}
	}
}

func pick(tree any, path string) any {
	cur := tree
	for _, part := range strings.Split(path, ".") {
		switch x := cur.(type) {
		case []any:
			i, _ := strconv.Atoi(part)
			cur = x[i]
		case map[string]any:
			cur = x[part]
		}
	}
	return cur
}

func TestHandVerified(t *testing.T) {
	var hs []struct {
		Name   string         `json:"name"`
		Text   string         `json:"text"`
		Lang   *string        `json:"lang"`
		Checks map[string]any `json:"checks"`
	}
	load(t, "hand_verified.json", &hs)
	for _, h := range hs {
		lang := ""
		if h.Lang != nil {
			lang = *h.Lang
		}
		a := Analyse(h.Text, lang)
		for path, want := range h.Checks {
			got := pick(a, path)
			switch w := want.(type) {
			case nil:
				if got != nil {
					t.Errorf("%s %s: want null, got %v", h.Name, path, got)
				}
			case string:
				if got != w {
					t.Errorf("%s %s: want %q, got %v", h.Name, path, w, got)
				}
			case float64:
				switch g := got.(type) {
				case R:
					if g.H != int(math.Round(w*100)) {
						t.Errorf("%s %s: want %v, got %d hundredths", h.Name, path, w, g.H)
					}
				case int:
					if float64(g) != w {
						t.Errorf("%s %s: want %v, got %d", h.Name, path, w, g)
					}
				default:
					t.Errorf("%s %s: unexpected %T", h.Name, path, got)
				}
			case []any:
				if g, ok := got.([]any); !ok || len(g) != len(w) {
					t.Errorf("%s %s: want empty list, got %v", h.Name, path, got)
				}
			}
		}
	}
}

func TestCharactersAreCodePoints(t *testing.T) {
	if got := Analyse("café \U0001F600", "")["characters"]; got != 6 {
		t.Errorf("got %v, want 6", got)
	}
}
