import json
import subprocess
import sys
import unittest
from pathlib import Path

from dewey_decimal.core import R, analyse, syllables, to_json

ROOT = Path(__file__).resolve().parent.parent
EM = chr(0x2014)


def pick(tree, path):
    cur = tree
    for part in path.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


class TestVectors(unittest.TestCase):
    def test_every_vector_matches(self):
        for v in json.loads((ROOT / "spec" / "vectors.json").read_text(encoding="utf-8")):
            self.assertEqual(to_json(analyse(v["text"], v["lang"])), v["expect"], v["name"])

    def test_vectors_file_is_current(self):
        r = subprocess.run([sys.executable, "tools/gen_vectors.py", "--check"], cwd=ROOT, capture_output=True)
        self.assertEqual(r.returncode, 0, "run python tools/gen_vectors.py")

    def test_hand_verified(self):
        for h in json.loads((ROOT / "spec" / "hand_verified.json").read_text(encoding="utf-8")):
            a = analyse(h["text"], h["lang"])
            for path, want in h["checks"].items():
                got = pick(a, path)
                if isinstance(got, R):
                    self.assertEqual(got.hundredths, round(want * 100), (h["name"], path))
                else:
                    self.assertEqual(got, want, (h["name"], path))


class TestRules(unittest.TestCase):
    def test_syllable_examples(self):
        for w, n in {"cat": 1, "table": 2, "cake": 1, "education": 4, "banana": 3, "": 1, "123": 1}.items():
            self.assertEqual(syllables(w, "en"), n, w)
        for w, n in {"gut": 1, "universität": 5, "schönheit": 2, "bericht": 2}.items():
            self.assertEqual(syllables(w, "de"), n, w)

    def test_output_is_valid_json_and_has_no_em_dash(self):
        for _, text in [("x", "Great work. Not bad at all!"), ("y", "Der Bericht ist sehr gut.")]:
            out = to_json(analyse(text))
            json.loads(out)
            self.assertNotIn(EM, out)

    def test_json_shape(self):
        a = json.loads(to_json(analyse("The cat sat on the mat.")))
        self.assertEqual(sorted(a), sorted(["characters", "characters_no_space", "language", "lines", "numbers", "paragraphs", "readability",
                                            "sentences", "sentiment", "top_terms", "unique_words", "words"]))

    def test_rounding_is_half_away_from_zero(self):
        from dewey_decimal.core import round2
        self.assertEqual(round2(0.125).hundredths, 13)
        self.assertEqual(round2(-0.125).hundredths, -13)
        self.assertEqual(round2(2.4).hundredths, 240)
        self.assertEqual(round2(-0.001).hundredths, 0)

    def test_repository_has_no_em_dash(self):
        kinds = {".py", ".md", ".js", ".go", ".txt", ".json", ".yml"}
        files = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in kinds and ".git" not in p.parts and "__pycache__" not in p.parts]
        bad = [str(p.relative_to(ROOT)) for p in files if EM in p.read_text(encoding="utf-8")]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
