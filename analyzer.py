# analyzer.py
# Dewey.Decimal 📚
# A text analysis toolkit for decision-ready insights.

import sys
from collections import Counter
from textblob import TextBlob
import textstat

def analyze_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Basic counts
    word_count = len(text.split())
    char_count = len(text)

    # Most common words
    words = [w.lower() for w in text.split() if w.isalpha()]
    common_words = Counter(words).most_common(5)

    # Sentiment
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.1:
        tone = "Positive"
    elif sentiment < -0.1:
        tone = "Negative"
    else:
        tone = "Neutral"

    # Readability
    readability = textstat.flesch_kincaid_grade(text)

    # Print results
    print(f"📊 Analysis of: {file_path}")
    print(f"Words: {word_count}")
    print(f"Characters: {char_count}")
    print("Most common words:", [w for w, _ in common_words])
    print(f"Sentiment: {tone}")
    print(f"Readability (Grade Level): {readability}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <file>")
    else:
        analyze_text(sys.argv[1])
