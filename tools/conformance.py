"""Run the Python, JavaScript and Go programs on the same texts and require byte-identical output.

    python tools/conformance.py [N] [SEED]

Texts: the curated corpus plus N generated ones (default 3000). For each text, the JSON output and the plain text report from the
three programs must be the same bytes. Exit 1 on the first disagreement, after printing the text that caused it."""
from __future__ import annotations

import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from corpus import CURATED, generate  # noqa: E402


def run(cmd: list[str]) -> bytes:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=600)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return r.stdout


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    rng = random.Random(seed)
    texts = [t for _, t in CURATED] + [generate(rng) for _ in range(n)]
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        files = []
        for i, t in enumerate(texts):
            p = d / f"t{i:05d}.txt"
            p.write_bytes(t.encode("utf-8"))
            files.append(str(p))
        gobin = d / "dewey-go"
        subprocess.run(["go", "build", "-o", str(gobin), "analyzer.go"], cwd=ROOT, check=True)
        impls = {"python": [sys.executable, "analyzer.py"], "javascript": ["node", "analyzer.js"], "go": [str(gobin)]}
        bad = 0
        for mode in (["--json"], []):
            for lang in ([], ["--lang", "en"], ["--lang", "de"]):
                if mode == [] and lang:
                    continue
                out = {k: run(cmd + files + mode + lang) for k, cmd in impls.items()}
                if len(set(out.values())) == 1:
                    continue
                # find the first text where they differ
                for f in files:
                    one = {k: run(cmd + [f] + mode + lang) for k, cmd in impls.items()}
                    if len(set(one.values())) > 1:
                        bad += 1
                        print(f"DISAGREEMENT on {Path(f).name} {mode + lang}: {texts[int(Path(f).stem[1:])]!r}")
                        for k, v in one.items():
                            print(f"--- {k}\n{v.decode('utf-8', 'replace')}")
                        break
        if bad:
            return 1
    print(f"{len(texts)} texts, 3 implementations, JSON (detected, forced en, forced de) and text reports: byte-identical")
    return 0


if __name__ == "__main__":
    shutil.which("go") or sys.exit("go is required")
    sys.exit(main())
