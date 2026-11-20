"""Write spec/vectors.json from the curated texts and the Python reference. CI regenerates it and fails if the committed file differs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from corpus import CURATED  # noqa: E402

from dewey_decimal.core import analyse, to_json  # noqa: E402


def build() -> str:
    vectors = []
    for name, text in CURATED:
        for lang in (None, "en", "de"):
            if lang is not None and name not in ("unknown language", "cat", "german", "english sentiment", "decomposed accents"):
                continue
            vectors.append({"name": name + (f" (forced {lang})" if lang else ""), "text": text, "lang": lang, "expect": to_json(analyse(text, lang))})
    return json.dumps(vectors, ensure_ascii=True, indent=1) + "\n"


if __name__ == "__main__":
    out = ROOT / "spec" / "vectors.json"
    if "--check" in sys.argv:
        sys.exit(0 if out.read_text(encoding="utf-8") == build() else 1)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out}")
