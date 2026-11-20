# Dewey.Decimal specification, version 1

Three programs (Python, JavaScript, Go) implement this document. For any input text they must print byte-identical JSON. That is what the
conformance job in CI checks, on the vectors in `vectors.json` and on thousands of generated texts.

Input is a sequence of Unicode code points. No normalisation is applied. Everything below counts code points, never bytes or UTF-16 units.

## 1. Character classes

* **letter**: Unicode general category L* or M* (marks count as letters so that decomposed accents stay inside a word).
* **digit**: category Nd.
* **space**: exactly U+0009 to U+000D, U+0020, U+0085, U+00A0, U+1680, U+2000 to U+200A, U+2028, U+2029, U+202F, U+205F, U+3000.
* **line break**: U+000A, U+000D (U+000D U+000A is one break), U+0085 is only a space.
* **terminator**: `.` `!` `?` `…`. **closer**: `"` `'` `)` `]` `»` `”` `’`.

## 2. Scan

One left-to-right pass over the code points.

* A **word** starts at a letter and extends while the next code point is a letter, or is `'` `’` `-` and is followed by a letter. A word that
  ends at `'` or `-` does not include it. Words are lower-cased one code point at a time with the Unicode simple lower-case mapping, and U+0130 maps to itself, before
  counting, comparing or looking up. (A code point whose full mapping is longer than one code point is left alone.)
* A **number** starts at a digit and extends while the next code point is a digit, or is `.` or `,` and is followed by a digit.
* A **terminator run** is one or more terminators, then any closers. It **ends a sentence** if it is followed by a space or the end of the text, unless
  the run is exactly one `.` (no closers) that directly follows a word (no gap) whose lower-cased form is in `abbreviations.txt`.
* A **blank line** is a whitespace run containing two or more line breaks. It ends a sentence and a paragraph.
* A sentence is counted only if it contains at least one word. A paragraph is counted only if it contains at least one non-space code point.
  The end of the text closes the last sentence and paragraph.

## 3. Counts

`characters` all code points; `characters_no_space` code points that are not spaces; `lines` the number of line breaks, plus one if the text does not end
with a line break and is not empty; `words`; `numbers`; `sentences`; `paragraphs`; `unique_words`.

## 4. Language

Count the words found in `stopwords_en.txt` (`en`) and in `stopwords_de.txt` (`de`). The language is `en` if `en >= 3` and `en >= 1.4 * de`, `de` if `de >= 3` and
`de >= 1.4 * en`, otherwise `unknown`. A caller may force `en` or `de`.

## 5. Top terms

Words that are not stop words of either language and have at least 3 code points, counted. Sorted by count descending, then by code point order of the word.
The first 5 are reported with their counts.

## 6. Syllables

Per word, by language (`unknown` uses the English rule only for the word statistics, no scores are produced).

* **en**: keep only `a` to `z`; if none remain the word has 1 syllable; if 3 or fewer remain it has 1; otherwise remove one match of
  `(?:[^laeiouy]es|[^td]ed|[^laeiouy]e)$`, then one match of `^y`, then count the matches of `[aeiouy]{1,2}`; at least 1.
* **de**: keep letters of `a` to `z` and `ä ö ü ß`; count maximal runs of `a e i o u y ä ö ü`; at least 1.

## 7. Readability (null unless the language is known and `words > 0` and `sentences > 0`)

With `W` words, `S` sentences, `Y` syllables, `C` words of 3 or more syllables, `L` words of more than 6 letters (code points), `O` words of 1 syllable:

* **en**: `flesch_reading_ease = 206.835 - 1.015 * (W / S) - 84.6 * (Y / W)`; `flesch_kincaid_grade = 0.39 * (W / S) + 11.8 * (Y / W) - 15.59`;
  `gunning_fog = 0.4 * ((W / S) + 100 * (C / W))`.
* **de**: `flesch_amstad = 180 - (W / S) - 58.5 * (Y / W)`; `wiener_sachtext_1 = 0.1935 * MS + 0.1672 * SL + 0.1297 * IW - 0.0327 * ES - 0.875` with
  `MS = 100 * C / W`, `SL = W / S`, `IW = 100 * L / W`, `ES = 100 * O / W`.

Evaluation order is as written, left to right, in IEEE 754 double precision. Reported values are rounded half away from zero to 2 decimals: `r = floor(abs(x) * 100 + 0.5)`, the value is `sign * r / 100`.

## 8. Sentiment (null unless the language is known)

Lexicon `sentiment_<lang>.json` maps a word to an integer from -3 to 3. For each word index `i` with a lexicon value `v`: if the preceding word has a booster `b` (from
`modifiers.json`), `v = v * (1 + b)`; then if any of the three preceding words is a negator of the language, `v = v * -0.75`. `raw` is the sum. `score = raw / sqrt(raw * raw + 15)`.
Label `positive` if `score >= 0.05`, `negative` if `score <= -0.05`, else `neutral`. `positive_hits` and `negative_hits` count the lexicon words with `v > 0` and `v < 0` before modifiers.
The score is rounded as in section 7.

## 9. Output

JSON, keys sorted by code point, 2-space indent, non-ASCII written as is, a final newline. Integers as integers. Rounded values as the shortest decimal that
round-trips. Absent values are `null`. Command line: `analyzer <file>... [--json] [--lang en|de]`. Several files give an object keyed by the file name.

The plain text report (without `--json`) has these lines, in order: `Analysis of <name>`; `  Words: <n>   Sentences: <n>   Paragraphs: <n>` with thousands separators `,`;
`  Characters: <n> (<n> without spaces)   Language: <language>`; `  Top terms: <term> (<count>), ...` or `none`; if sentiment is not null
`  Sentiment: <label> (<signed score with 2 decimals>; <p> positive and <n> negative words)`; if readability is not null `  Readability: <name with _ as space> <value with 2 decimals>, ...`
with the names in key order.
