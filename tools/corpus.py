"""Texts for the conformance checks: a curated list that exercises every rule of the spec, and a seeded generator for volume."""
from __future__ import annotations

import random

CURATED: list[tuple[str, str]] = [
    ("empty", ""),
    ("only spaces", "   \n\t  \n"),
    ("cat", "The cat sat on the mat.\n"),
    ("no final newline", "The cat sat on the mat."),
    ("two sentences", "The quick brown fox jumps over the lazy dog. The dog did not mind!"),
    ("question and ellipsis", "Is this working? Yes... it is working… Really!?"),
    ("abbreviation", "Dr. Smith met Mr. Jones at 5 p.m. in St. Louis. They talked."),
    ("not an abbreviation at end", "He lives in the city of Wien. Then he left."),
    ("decimal numbers", "Version 3.5 costs 1,200.50 dollars and 12 cents."),
    ("closing quote", "She said \"it works.\" Then she left. 'Fine,' he said."),
    ("blank line ends sentence", "First paragraph without a stop\n\nSecond paragraph without a stop\n\n\nThird"),
    ("crlf", "One line.\r\nTwo lines.\r\n\r\nNew paragraph.\r\n"),
    ("cr only", "a.\rb.\rc."),
    ("hyphen and apostrophe", "It's a well-known fact that rock-and-roll isn't dead; don't panic- really."),
    ("curly apostrophe", "It’s the ‘best’ thing we’ve done."),
    ("german", "Der Bericht ist sehr gut. Die Ergebnisse sind nicht schlecht, und wir sind mit dem Wachstum zufrieden."),
    ("german negation", "Das Produkt ist nicht gut und kein Erfolg. Es war sehr schlecht."),
    ("english sentiment", "I love this product. It is great, not bad at all, and the team was very helpful."),
    ("english negative", "This was a terrible failure. The service is not good and the delays are awful."),
    ("negation window", "It is not really a very good idea but great."),
    ("boosters", "The result was extremely good and slightly bad and very poor."),
    ("unknown language", "Lorem ipsum dolor sit amet consectetur adipiscing elit."),
    ("decomposed accents", "Café résumé und Überprüfung der Gëste."),
    ("precomposed accents", "Café résumé und Überprüfung der Gäste."),
    ("cjk", "我喜欢编程。こんにちは世界。안녕하세요 세계."),
    ("emoji astral", "Great work \U0001f600\U0001f680 team! \U0001f1e9\U0001f1ea"),
    ("greek and sigma", "ΟΔΟΣ ΑΘΗΝΑ οδός ΣΣ."),
    ("turkish dotted i", "İstanbul İI ii. İ and i."),
    ("cyrillic", "Привет мир. Это тест."),
    ("odd spaces", "a b c　d e f\u0085g​h i"),
    ("bom", "﻿The cat sat on the mat."),
    ("long word and sharp s", "Donaudampfschifffahrtsgesellschaft und Fußball sind großartig, sehr großartig."),
    ("syllable cases", "created queue bases rhythm every people table simple stone cake yellow beautiful"),
    ("many sentences", " ".join(f"Sentence number {i} is short." for i in range(30))),
    ("repeated terms", "data data data model model system analysis analysis analysis analysis report"),
    ("tie break order", "zebra apple mango apple zebra mango kiwi"),
    ("digits only", "2026 12.5 3,000 7"),
    ("punctuation only", "... !!! ??? ……"),
    ("terminator then closer then space", "He said (really!) and left.) Then \"what?\" came."),
    ("abbrev with closer", "See Dr.) Then Mr.\" ok."),
    ("de abbreviations", "Z.B. bzw. usw. gilt hier, vgl. Abb. 3 und ca. 5 Prozent."),
]

POOLS = {
    "en": ["the", "a", "of", "and", "to", "in", "is", "that", "it", "for", "as", "with", "was", "on", "be", "by", "this", "have", "from", "or", "one", "had", "not", "but", "what", "all", "were", "when", "we", "there", "can", "an", "your", "which", "their", "said", "if", "do", "will", "each", "about", "how", "up", "out", "them", "then", "she", "many", "some", "so", "these", "would", "other", "into", "has", "more", "her", "two", "like", "him", "see", "time", "could", "no", "make", "than", "first", "been", "its", "who", "now", "people", "my", "made", "over", "did", "down", "only", "way", "find", "use", "may", "water", "long", "little", "very", "after", "words", "called", "just", "where", "most", "know", "get", "through", "back", "much", "before", "go", "good", "new", "write", "our", "me", "man", "too", "any", "day", "same", "right", "look", "think", "also", "around", "another", "came", "come", "work", "three", "word", "must", "because", "does", "part", "even", "place", "well", "such", "here", "take", "why", "help", "put", "different", "away", "again", "off", "went", "old", "number", "great", "tell", "men", "say", "small", "every", "found", "still", "between", "name", "should", "home", "big", "give", "air", "line", "set", "own", "under", "read", "last", "never", "us", "left", "end", "along", "while", "might", "next", "sound", "below", "saw", "something", "thought", "both", "few", "those", "always", "looked", "show", "large", "often", "together", "asked", "house", "don't", "world", "going", "want", "school", "important", "until", "form", "food", "keep", "children", "feet", "land", "side", "without", "boy", "once", "animals", "life", "enough", "took", "sometimes", "four", "head", "above", "kind", "began", "almost", "live", "page", "got", "earth", "need", "far", "hand", "high", "year", "mother", "light", "country", "father", "let", "night", "picture", "being", "study", "second", "soon", "story", "since", "white", "ever", "paper", "hard", "near", "sentence", "better", "best", "across", "during", "today", "however", "sure", "knew", "it's", "try", "told", "young", "sun", "thing", "whole", "hear", "example", "heard", "several", "change", "answer", "room", "sea", "against", "top", "turned", "learn", "point", "city", "play", "toward", "five", "using", "himself", "usually", "good", "great", "excellent", "bad", "terrible", "poor", "not", "very", "extremely", "slightly", "never", "without", "love", "hate"],
    "de": ["der", "die", "das", "und", "ist", "nicht", "ein", "eine", "zu", "den", "dem", "mit", "auf", "für", "von", "sie", "es", "im", "sich", "auch", "an", "als", "bei", "oder", "nach", "wie", "aber", "aus", "wir", "sehr", "gut", "schlecht", "kein", "keine", "erfolg", "verlust", "wachstum", "fehler", "problem", "hervorragend", "schrecklich", "einfach", "schnell", "langsam", "kunde", "bericht", "daten", "system", "analyse", "ergebnis", "wichtig", "neu", "alt", "groß", "klein", "überprüfung", "gäste", "fußball", "ohne", "kaum", "etwas", "total"],
    "u": ["café", "résumé", "naïve", "Ünïcödé", "straße", "ÄÖÜ", "ß", "ǅ", "Ω", "ωσ", "Σ", "привет", "мир", "我喜欢", "こんにちは", "안녕", "😀", "🚀", "İ", "ı", "x́", "é", "ñ", "Ñandú"],
    "abbr": ["Dr.", "Mr.", "St.", "etc.", "usw.", "z.B.", "bzw.", "Prof.", "vs.", "No.", "Fig.", "ca."],
    "num": ["3.5", "1,200", "12", "2026", "0.05", "7,5", "1.000.000", "42."],
    "punct": [".", "!", "?", "...", "…", ",", ";", ":", "-", "(", ")", '"', "'", "”", "’", "»", "]"],
    "ws": [" ", " ", " ", " ", "\n", "\r\n", "\n\n", "\t", " ", "　", " ", "\r", "\u0085", "  ", "\n \n"],
}


def generate(rng: random.Random, max_tokens: int = 80) -> str:
    out = []
    mode = rng.choice(["en", "de", "mixed", "mixed", "u"])
    for _ in range(rng.randint(0, max_tokens)):
        r = rng.random()
        if r < 0.55:
            pool = POOLS["en"] if mode == "en" else POOLS["de"] if mode == "de" else rng.choice([POOLS["en"], POOLS["de"], POOLS["u"]]) if mode == "mixed" else POOLS["u"]
            w = rng.choice(pool)
            out.append(w.capitalize() if rng.random() < 0.2 else w.upper() if rng.random() < 0.03 else w)
        elif r < 0.62:
            out.append(rng.choice(POOLS["abbr"]))
        elif r < 0.70:
            out.append(rng.choice(POOLS["num"]))
        elif r < 0.85:
            out.append(rng.choice(POOLS["punct"]))
        else:
            out.append(rng.choice(POOLS["ws"]))
        if rng.random() < 0.7:
            out.append(rng.choice(POOLS["ws"][:6]))
    text = "".join(out)
    if rng.random() < 0.1:
        text = "﻿" + text
    return text
