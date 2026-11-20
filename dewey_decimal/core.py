"""Dewey.Decimal reference implementation in Python. The normative text is spec/SPEC.md; the JS and Go versions must print the same bytes."""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

SPEC = Path(__file__).resolve().parent.parent / "spec"
SPACES = frozenset([*range(0x09, 0x0E), 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000])
TERMINATORS = frozenset(".!?…")
CLOSERS = frozenset("\"')]»”’")
CONNECTORS = frozenset("'’-")


def _words_file(name: str) -> frozenset[str]:
    return frozenset((SPEC / name).read_text(encoding="utf-8").split())


STOP = {"en": _words_file("stopwords_en.txt"), "de": _words_file("stopwords_de.txt")}
ABBREVIATIONS = _words_file("abbreviations.txt")
LEXICON = {k: json.loads((SPEC / f"sentiment_{k}.json").read_text(encoding="utf-8")) for k in ("en", "de")}
_MOD = json.loads((SPEC / "modifiers.json").read_text(encoding="utf-8"))
NEGATORS = {k: frozenset(v) for k, v in _MOD["negators"].items()}
BOOSTERS: dict[str, float] = _MOD["boosters"]


def is_letter(c: str) -> bool:
    return unicodedata.category(c)[0] in "LM"


def is_digit(c: str) -> bool:
    return unicodedata.category(c) == "Nd"


def lower(word: str) -> str:
    out = []
    for c in word:
        lc = c.lower()
        out.append(lc if len(lc) == 1 else c)
    return "".join(out)


def scan(text: str) -> dict[str, Any]:
    cps = list(text)
    n = len(cps)
    words: list[str] = []
    numbers = sentences = paragraphs = 0
    has_word = has_text = False
    last_end = -1
    last_word = ""
    i = 0
    while i < n:
        c = cps[i]
        if is_letter(c):
            j = i + 1
            while j < n and (is_letter(cps[j]) or (cps[j] in CONNECTORS and j + 1 < n and is_letter(cps[j + 1]))):
                j += 1
            w = lower("".join(cps[i:j]))
            words.append(w)
            last_word, last_end = w, j
            has_word = has_text = True
            i = j
        elif is_digit(c):
            j = i + 1
            while j < n and (is_digit(cps[j]) or (cps[j] in ".," and j + 1 < n and is_digit(cps[j + 1]))):
                j += 1
            numbers += 1
            has_text = True
            i = j
        elif c in TERMINATORS:
            j = i
            while j < n and cps[j] in TERMINATORS:
                j += 1
            run_end = j
            while j < n and cps[j] in CLOSERS:
                j += 1
            has_text = True
            if j >= n or ord(cps[j]) in SPACES:
                single_dot = run_end == i + 1 and cps[i] == "." and j == run_end
                if not (single_dot and last_end == i and last_word in ABBREVIATIONS) and has_word:
                    sentences += 1
                    has_word = False
            i = j
        elif ord(c) in SPACES:
            j = i
            breaks = 0
            while j < n and ord(cps[j]) in SPACES:
                if cps[j] == "\r":
                    breaks += 1
                    if j + 1 < n and cps[j + 1] == "\n":
                        j += 1
                elif cps[j] == "\n":
                    breaks += 1
                j += 1
            if breaks >= 2:
                if has_word:
                    sentences += 1
                    has_word = False
                if has_text:
                    paragraphs += 1
                    has_text = False
            i = j
        else:
            has_text = True
            i += 1
    if has_word:
        sentences += 1
    if has_text:
        paragraphs += 1
    return {"words": words, "numbers": numbers, "sentences": sentences, "paragraphs": paragraphs}


def count_lines(text: str) -> int:
    if not text:
        return 0
    breaks = 0
    i, n = 0, len(text)
    while i < n:
        if text[i] == "\r":
            breaks += 1
            if i + 1 < n and text[i + 1] == "\n":
                i += 1
        elif text[i] == "\n":
            breaks += 1
        i += 1
    return breaks + (0 if text[-1] in "\r\n" else 1)


def detect_language(words: list[str]) -> str:
    en = sum(w in STOP["en"] for w in words)
    de = sum(w in STOP["de"] for w in words)
    if en >= 3 and en >= 1.4 * de:
        return "en"
    if de >= 3 and de >= 1.4 * en:
        return "de"
    return "unknown"


_EN_SILENT = re.compile(r"(?:[^laeiouy]es|[^td]ed|[^laeiouy]e)$")
_EN_GROUPS = re.compile(r"[aeiouy]{1,2}")
_DE_RUNS = re.compile(r"[aeiouyäöü]+")


def syllables(word: str, lang: str) -> int:
    if lang == "de":
        return max(1, len(_DE_RUNS.findall("".join(ch for ch in word if "a" <= ch <= "z" or ch in "äöüß"))))
    w = "".join(ch for ch in word if "a" <= ch <= "z")
    if len(w) <= 3:
        return 1
    w = _EN_SILENT.sub("", w, count=1)
    w = re.sub(r"^y", "", w, count=1)
    return max(1, len(_EN_GROUPS.findall(w)))


class R(float):
    """A value rounded to hundredths. ``hundredths`` is exact; the float is only for arithmetic in callers."""

    hundredths: int

    def __new__(cls, hundredths: int) -> R:
        obj = super().__new__(cls, hundredths / 100)
        obj.hundredths = hundredths
        return obj


def round2(x: float) -> R:
    r = math.floor(abs(x) * 100 + 0.5)
    return R(r if x >= 0 else -r)


def fixed(h: int) -> str:
    """Hundredths as text with exactly two decimals (human output)."""
    a = abs(h)
    return f"{'-' if h < 0 else ''}{a // 100}.{a % 100:02d}"


def short(h: int) -> str:
    """Hundredths as the shortest decimal (JSON): 0, 12, 2.4, 116.15."""
    a = abs(h)
    whole, frac = divmod(a, 100)
    body = str(whole) if frac == 0 else f"{whole}.{frac // 10}" if frac % 10 == 0 else f"{whole}.{frac:02d}"
    return "-" + body if h < 0 and a != 0 else body


def readability(words: list[str], sentences: int, lang: str) -> dict[str, R] | None:
    if lang == "unknown" or not words or sentences == 0:
        return None
    w, s = len(words), sentences
    syl = [syllables(x, lang) for x in words]
    y = sum(syl)
    c = sum(k >= 3 for k in syl)
    long_ = sum(len(x) > 6 for x in words)
    o = sum(k == 1 for k in syl)
    if lang == "en":
        return {"flesch_reading_ease": round2(206.835 - 1.015 * (w / s) - 84.6 * (y / w)),
                "flesch_kincaid_grade": round2(0.39 * (w / s) + 11.8 * (y / w) - 15.59),
                "gunning_fog": round2(0.4 * ((w / s) + 100 * (c / w)))}
    ms, sl, iw, es = 100 * c / w, w / s, 100 * long_ / w, 100 * o / w
    return {"flesch_amstad": round2(180 - (w / s) - 58.5 * (y / w)),
            "wiener_sachtext_1": round2(0.1935 * ms + 0.1672 * sl + 0.1297 * iw - 0.0327 * es - 0.875)}


def sentiment(words: list[str], lang: str) -> dict[str, Any] | None:
    if lang == "unknown":
        return None
    lex, neg = LEXICON[lang], NEGATORS[lang]
    raw = 0.0
    pos = negc = 0
    for i, w in enumerate(words):
        if w not in lex:
            continue
        v0 = lex[w]
        pos += v0 > 0
        negc += v0 < 0
        v = float(v0)
        if i > 0 and words[i - 1] in BOOSTERS:
            v = v * (1 + BOOSTERS[words[i - 1]])
        if any(words[k] in neg for k in range(max(0, i - 3), i)):
            v = v * -0.75
        raw += v
    score = raw / math.sqrt(raw * raw + 15)
    label = "positive" if score >= 0.05 else "negative" if score <= -0.05 else "neutral"
    return {"score": round2(score), "label": label, "positive_hits": pos, "negative_hits": negc}


def analyse(text: str, lang: str | None = None) -> dict[str, Any]:
    sc = scan(text)
    words = sc["words"]
    language = lang if lang in ("en", "de") else detect_language(words)
    counts = Counter(w for w in words if len(w) >= 3 and w not in STOP["en"] and w not in STOP["de"])
    top = sorted(counts.items(), key=lambda kv: (-kv[1], [ord(ch) for ch in kv[0]]))[:5]
    return {
        "characters": len(text),
        "characters_no_space": sum(ord(ch) not in SPACES for ch in text),
        "language": language,
        "lines": count_lines(text),
        "numbers": sc["numbers"],
        "paragraphs": sc["paragraphs"],
        "readability": readability(words, sc["sentences"], language),
        "sentences": sc["sentences"],
        "sentiment": sentiment(words, language),
        "top_terms": [{"count": c, "term": w} for w, c in top],
        "unique_words": len(set(words)),
        "words": len(words),
    }


def _string(v: str) -> str:
    out = ['"']
    for ch in v:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _dump(v: Any, depth: int) -> str:
    pad, inner = "  " * depth, "  " * (depth + 1)
    if v is None:
        return "null"
    if isinstance(v, R):
        return short(v.hundredths)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return _string(v)
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[\n" + ",\n".join(inner + _dump(x, depth + 1) for x in v) + "\n" + pad + "]"
    keys = sorted(v, key=lambda k: [ord(c) for c in k])
    if not keys:
        return "{}"
    return "{\n" + ",\n".join(f"{inner}{_string(k)}: {_dump(v[k], depth + 1)}" for k in keys) + "\n" + pad + "}"


def to_json(obj: Any) -> str:
    """The canonical output of spec section 9: sorted keys, 2-space indent, rounded values as shortest decimals."""
    return _dump(obj, 0) + "\n"
