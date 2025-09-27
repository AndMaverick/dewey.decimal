# Dewey.Decimal 📊

Turning raw text into decision-ready insights.

This toolkit ingests plain text (reports, articles, logs, notes) and outputs clarity: counts, sentiment, readability, and common terms.

---

## 🚀 Features
- **Word & character counts** — quick size check  
- **Most common words** — instant keyword extraction  
- **Sentiment analysis** — positive / neutral / negative tone  
- **Readability scores** — Flesch-Kincaid, so you know if your content is exec-ready  

---

## 📂 Implementations
- [analyzer.py](analyzer.py) — Python implementation  
- [analyzer.js](analyzer.js) — JavaScript implementation  
- [analyzer.go](analyzer.go) — Go implementation  

---

## ⚡ Example Usage

### 🐍 Python
```bash
python analyzer.py example_text.txt
node analyzer.js example_text.txt
go run analyzer.go example_text.txt

## 📊 Sample Output

Running the analyzer on `example_text.txt` produces results like:
Word count: 1,245
Character count: 7,890
Most common words: [data, system, analysis, model, process]
Sentiment: Positive
Readability: Grade 8 (Flesch-Kincaid)
