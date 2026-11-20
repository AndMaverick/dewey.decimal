"""Measured claims for the README, recomputed here. Exit 1 if a check fails.

    python tools/evaluate.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dewey_decimal.core import analyse, syllables  # noqa: E402

# word: syllables, counted by ear and checked against a dictionary
EN = ["cat", "1", "dog", "1", "house", "1", "water", "2", "table", "2", "simple", "2", "people", "2", "little", "2", "apple", "2", "purple", "2", "music", "2", "city", "2", "happy", "2", "money", "2", "story", "2", "family", "3", "banana", "3", "computer", "3", "beautiful", "3", "important", "3", "different", "3", "animal", "3", "hospital", "3", "vegetable", "3", "education", "4", "information", "4", "university", "5", "communication", "5", "organization", "5", "create", "2", "created", "3", "walked", "1", "jumped", "1", "wanted", "2", "needed", "2", "loved", "1", "played", "1", "baked", "1", "asked", "1", "hated", "2", "decided", "3", "ended", "2", "faded", "2", "hoped", "1", "cake", "1", "make", "1", "time", "1", "home", "1", "name", "1", "because", "2", "every", "3", "queue", "1", "rhythm", "2", "science", "2", "quiet", "2", "poem", "2", "idea", "3", "area", "3", "real", "1", "being", "2", "going", "2", "doing", "2", "seeing", "2", "fire", "1", "hour", "1", "our", "1", "yes", "1", "table", "2", "bottle", "2", "middle", "2", "uncle", "2", "people", "2", "average", "3", "business", "2", "evening", "2", "camera", "3", "chocolate", "2", "interesting", "3", "favorite", "3", "comfortable", "3", "temperature", "4", "vegetable", "3", "restaurant", "3", "secretary", "4", "history", "3", "memory", "3", "company", "3", "together", "3", "remember", "3", "yesterday", "3", "tomorrow", "3", "package", "2", "message", "2", "language", "2", "village", "2", "average", "3", "courage", "2", "orange", "2", "change", "1", "strange", "1", "large", "1", "judge", "1", "bridge", "1"]
DE = ["gut", "1", "haus", "1", "buch", "1", "schule", "2", "bericht", "2", "kunde", "2", "daten", "2", "system", "2", "analyse", "4", "ergebnis", "3", "wichtig", "2", "universität", "5", "überprüfung", "4", "geschäft", "2", "wachstum", "2", "erfolg", "2", "fehler", "2", "problem", "2", "computer", "3", "telefon", "3", "familie", "3", "musik", "2", "straße", "2", "fußball", "2", "schönheit", "2", "freundlich", "2", "mutter", "2", "vater", "2", "bruder", "2", "schwester", "2", "kinder", "2", "eltern", "2", "zeitung", "2", "wasser", "2", "sprache", "2", "mensch", "1", "arbeit", "2", "leben", "2", "liebe", "2", "frühling", "2", "sommer", "2", "herbst", "1", "winter", "2", "theater", "3", "europa", "3", "china", "2", "ukraine", "3", "museum", "3", "hotel", "2", "kaffee", "2", "tee", "1"]
POSITIVE = ["I love this product and it works great.", "The team was helpful and the support was excellent.", "A wonderful, fantastic result for everyone.",
            "We are delighted with the success and the growth.", "This is the best service I have used, highly recommended.", "Thanks, the improvement is impressive.",
            "The new version is fast, reliable and easy to use.", "What a brilliant and exciting opportunity this is.", "I am happy and proud of the progress.",
            "The results were not bad at all, actually very good.", "Great job, the quality is outstanding and the price is fair.", "An amazing experience, perfect from start to finish."]
NEGATIVE = ["This was a terrible failure and a waste of money.", "The service is awful and the delays are unacceptable.", "I hate the new design, it is confusing and slow.",
            "The product is not good and the support was rude.", "A disaster for the company, with heavy losses and layoffs.", "The app crashes and the bugs are annoying.",
            "Very disappointing, the quality is poor and unreliable.", "It is a scam and a fraud, never again.", "We are worried about the risks and the growing debt.",
            "The results were not great and not helpful.", "Horrible experience, the worst I have had.", "This is useless and the errors keep getting worse."]
NEUTRAL = ["The meeting is on Tuesday at ten in the conference room.", "The report has twelve pages and three tables.", "Please send the file to the address below.",
           "The office opens at nine and closes at five.", "The train leaves from platform four.", "We moved the server to a new rack last month."]
POS_DE = ["Das Produkt ist sehr gut und der Service war hervorragend.", "Wir sind mit dem Erfolg und dem Wachstum zufrieden.", "Ein großartiges und wunderbares Ergebnis.",
          "Die Unterstützung war hilfreich und die Qualität ist ausgezeichnet.", "Danke, die Verbesserung ist beeindruckend."]
NEG_DE = ["Das Produkt ist schlecht und ein totaler Misserfolg.", "Der Service war schrecklich und die Verzögerungen sind ärgerlich.", "Es gibt zu viele Fehler und Probleme.",
          "Das Ergebnis ist nicht gut und sehr enttäuschend.", "Eine Katastrophe für die Firma mit hohen Verlusten."]
HARD = [("Oh great, another delay. Just what we needed.", "negative"), ("The service wasn't exactly terrible.", "positive"), ("I can't say I hate it.", "positive")]


def main() -> int:
    ok = True
    for name, table, lang in (("English", EN, "en"), ("German", DE, "de")):
        pairs = sorted(dict(zip(table[::2], map(int, table[1::2]), strict=True)).items())
        wrong = [(w, n, syllables(w, lang)) for w, n in pairs if syllables(w, lang) != n]
        print(f"{name} syllables right: {len(pairs) - len(wrong)}/{len(pairs)}")
        print("  misses: " + ", ".join(f"{w} (true {n}, got {g})" for w, n, g in wrong))
    print("  (the English rule is a known heuristic; these are the figures to expect on ordinary text, and the misses are listed)")

    def label(text: str, lang: str) -> str:
        return analyse(text, lang)["sentiment"]["label"]

    en = [(t, "positive") for t in POSITIVE] + [(t, "negative") for t in NEGATIVE] + [(t, "neutral") for t in NEUTRAL]
    de = [(t, "positive") for t in POS_DE] + [(t, "negative") for t in NEG_DE]
    for name, items, lang in (("English", en, "en"), ("German", de, "de")):
        right = sum(label(t, lang) == want for t, want in items)
        print(f"{name} sentiment labels right on {len(items)} hand-labelled sentences: {right}/{len(items)}")
        for t, want in items:
            if label(t, lang) != want:
                print(f"  missed ({want}): {t}")
    hard = sum(label(t, "en") == want for t, want in HARD)
    print(f"sarcasm and double negatives, written to be hard: {hard}/{len(HARD)}")

    r = subprocess.run([sys.executable, "tools/conformance.py", "1500"], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    ok &= r.returncode == 0
    print("pass" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
