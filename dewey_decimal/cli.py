"""python -m dewey_decimal FILE... [--json] [--lang en|de]. Exit codes: 0 analysed, 2 a file could not be read as UTF-8."""
from __future__ import annotations

import sys
from pathlib import Path

from .core import analyse, fixed, to_json


def thousands(n: int) -> str:
    s = str(abs(n))
    parts: list[str] = []
    while len(s) > 3:
        parts.insert(0, s[-3:])
        s = s[:-3]
    parts.insert(0, s)
    return ("-" if n < 0 else "") + ",".join(parts)


def signed(h: int) -> str:
    return ("+" if h >= 0 else "") + fixed(h)


def render(name: str, a: dict) -> str:
    out = [f"Analysis of {name}", f"  Words: {thousands(a['words'])}   Sentences: {thousands(a['sentences'])}   Paragraphs: {thousands(a['paragraphs'])}",
           f"  Characters: {thousands(a['characters'])} ({thousands(a['characters_no_space'])} without spaces)   Language: {a['language']}",
           "  Top terms: " + (", ".join(f"{t['term']} ({t['count']})" for t in a["top_terms"]) or "none")]
    if a["sentiment"]:
        s = a["sentiment"]
        out.append(f"  Sentiment: {s['label']} ({signed(s['score'].hundredths)}; {s['positive_hits']} positive and {s['negative_hits']} negative words)")
    if a["readability"]:
        out.append("  Readability: " + ", ".join(f"{k.replace('_', ' ')} {fixed(v.hundredths)}" for k, v in sorted(a["readability"].items())))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    lang = None
    if "--lang" in args:
        k = args.index("--lang")
        lang = args[k + 1] if k + 1 < len(args) else None
        del args[k:k + 2]
        if lang not in ("en", "de"):
            print("error: --lang must be en or de", file=sys.stderr)
            return 2
    files = [a for a in args if a != "--json"]
    if not files:
        print("usage: analyzer.py FILE... [--json] [--lang en|de]", file=sys.stderr)
        return 2
    results = {}
    for f in files:
        try:
            text = Path(f).read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read {f}: {e}", file=sys.stderr)
            return 2
        results[f] = analyse(text, lang)
    if as_json:
        sys.stdout.write(to_json(next(iter(results.values())) if len(results) == 1 else results))
    else:
        for f, a in results.items():
            sys.stdout.write(render(f, a))
    return 0
