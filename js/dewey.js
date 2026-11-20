'use strict';
// Dewey.Decimal in JavaScript. The normative text is spec/SPEC.md; the Python and Go versions must print the same bytes.

const fs = require('fs');
const path = require('path');

const SPEC = path.join(__dirname, '..', 'spec');
const wordsFile = (name) => new Set(fs.readFileSync(path.join(SPEC, name), 'utf8').split(/\s+/).filter(Boolean));
const STOP = { en: wordsFile('stopwords_en.txt'), de: wordsFile('stopwords_de.txt') };
const ABBREVIATIONS = wordsFile('abbreviations.txt');
const LEXICON = {};
for (const k of ['en', 'de']) LEXICON[k] = new Map(Object.entries(JSON.parse(fs.readFileSync(path.join(SPEC, `sentiment_${k}.json`), 'utf8'))));
const MOD = JSON.parse(fs.readFileSync(path.join(SPEC, 'modifiers.json'), 'utf8'));
const NEGATORS = { en: new Set(MOD.negators.en), de: new Set(MOD.negators.de) };
const BOOSTERS = new Map(Object.entries(MOD.boosters));

const SPACES = new Set([0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x20, 0x85, 0xa0, 0x1680, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]);
for (let c = 0x2000; c <= 0x200a; c++) SPACES.add(c);
const TERMINATORS = new Set(['.', '!', '?', '…']);
const CLOSERS = new Set(['"', "'", ')', ']', '»', '”', '’']);
const CONNECTORS = new Set(["'", '’', '-']);
const LETTER = /^[\p{L}\p{M}]$/u;
const DIGIT = /^\p{Nd}$/u;

const isSpace = (c) => SPACES.has(c.codePointAt(0));
const isLetter = (c) => LETTER.test(c);
const isDigit = (c) => DIGIT.test(c);

function lower(word) {
  let out = '';
  for (const c of word) {
    const lc = c.toLowerCase();
    out += Array.from(lc).length === 1 ? lc : c;
  }
  return out;
}

function scan(text) {
  const cps = Array.from(text);
  const n = cps.length;
  const words = [];
  let numbers = 0, sentences = 0, paragraphs = 0;
  let hasWord = false, hasText = false, lastEnd = -1, lastWord = '';
  let i = 0;
  while (i < n) {
    const c = cps[i];
    if (isLetter(c)) {
      let j = i + 1;
      while (j < n && (isLetter(cps[j]) || (CONNECTORS.has(cps[j]) && j + 1 < n && isLetter(cps[j + 1])))) j++;
      const w = lower(cps.slice(i, j).join(''));
      words.push(w);
      lastWord = w; lastEnd = j; hasWord = hasText = true;
      i = j;
    } else if (isDigit(c)) {
      let j = i + 1;
      while (j < n && (isDigit(cps[j]) || ((cps[j] === '.' || cps[j] === ',') && j + 1 < n && isDigit(cps[j + 1])))) j++;
      numbers++; hasText = true;
      i = j;
    } else if (TERMINATORS.has(c)) {
      let j = i;
      while (j < n && TERMINATORS.has(cps[j])) j++;
      const runEnd = j;
      while (j < n && CLOSERS.has(cps[j])) j++;
      hasText = true;
      if (j >= n || isSpace(cps[j])) {
        const singleDot = runEnd === i + 1 && cps[i] === '.' && j === runEnd;
        if (!(singleDot && lastEnd === i && ABBREVIATIONS.has(lastWord)) && hasWord) {
          sentences++;
          hasWord = false;
        }
      }
      i = j;
    } else if (isSpace(c)) {
      let j = i, breaks = 0;
      while (j < n && isSpace(cps[j])) {
        if (cps[j] === '\r') {
          breaks++;
          if (j + 1 < n && cps[j + 1] === '\n') j++;
        } else if (cps[j] === '\n') breaks++;
        j++;
      }
      if (breaks >= 2) {
        if (hasWord) { sentences++; hasWord = false; }
        if (hasText) { paragraphs++; hasText = false; }
      }
      i = j;
    } else {
      hasText = true;
      i++;
    }
  }
  if (hasWord) sentences++;
  if (hasText) paragraphs++;
  return { words, numbers, sentences, paragraphs };
}

function countLines(text) {
  if (text === '') return 0;
  let breaks = 0;
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '\r') {
      breaks++;
      if (text[i + 1] === '\n') i++;
    } else if (text[i] === '\n') breaks++;
  }
  const last = text[text.length - 1];
  return breaks + (last === '\r' || last === '\n' ? 0 : 1);
}

function detectLanguage(words) {
  let en = 0, de = 0;
  for (const w of words) {
    if (STOP.en.has(w)) en++;
    if (STOP.de.has(w)) de++;
  }
  if (en >= 3 && en >= 1.4 * de) return 'en';
  if (de >= 3 && de >= 1.4 * en) return 'de';
  return 'unknown';
}

const EN_SILENT = /(?:[^laeiouy]es|[^td]ed|[^laeiouy]e)$/;
const EN_GROUPS = /[aeiouy]{1,2}/g;
const DE_RUNS = /[aeiouyäöü]+/g;

function syllables(word, lang) {
  if (lang === 'de') {
    const w = Array.from(word).filter((ch) => (ch >= 'a' && ch <= 'z') || 'äöüß'.includes(ch)).join('');
    return Math.max(1, (w.match(DE_RUNS) || []).length);
  }
  let w = Array.from(word).filter((ch) => ch >= 'a' && ch <= 'z').join('');
  if (w.length <= 3) return 1;
  w = w.replace(EN_SILENT, '').replace(/^y/, '');
  return Math.max(1, (w.match(EN_GROUPS) || []).length);
}

// A value rounded to hundredths, carried as an exact integer.
class R {
  constructor(hundredths) { this.hundredths = hundredths; }
  valueOf() { return this.hundredths / 100; }
}

function round2(x) {
  const r = Math.floor(Math.abs(x) * 100 + 0.5);
  return new R(x >= 0 ? r : -r);
}

function fixed(h) {
  const a = Math.abs(h);
  return `${h < 0 ? '-' : ''}${Math.floor(a / 100)}.${String(a % 100).padStart(2, '0')}`;
}

function short(h) {
  const a = Math.abs(h), whole = Math.floor(a / 100), frac = a % 100;
  const body = frac === 0 ? String(whole) : frac % 10 === 0 ? `${whole}.${frac / 10}` : `${whole}.${String(frac).padStart(2, '0')}`;
  return h < 0 && a !== 0 ? `-${body}` : body;
}

function readability(words, sentences, lang) {
  if (lang === 'unknown' || words.length === 0 || sentences === 0) return null;
  const w = words.length, s = sentences;
  const syl = words.map((x) => syllables(x, lang));
  const y = syl.reduce((a, b) => a + b, 0);
  const c = syl.filter((k) => k >= 3).length;
  const long = words.filter((x) => Array.from(x).length > 6).length;
  const o = syl.filter((k) => k === 1).length;
  if (lang === 'en') {
    return {
      flesch_reading_ease: round2(206.835 - 1.015 * (w / s) - 84.6 * (y / w)),
      flesch_kincaid_grade: round2(0.39 * (w / s) + 11.8 * (y / w) - 15.59),
      gunning_fog: round2(0.4 * ((w / s) + 100 * (c / w))),
    };
  }
  const ms = 100 * c / w, sl = w / s, iw = 100 * long / w, es = 100 * o / w;
  return {
    flesch_amstad: round2(180 - (w / s) - 58.5 * (y / w)),
    wiener_sachtext_1: round2(0.1935 * ms + 0.1672 * sl + 0.1297 * iw - 0.0327 * es - 0.875),
  };
}

function sentiment(words, lang) {
  if (lang === 'unknown') return null;
  const lex = LEXICON[lang], neg = NEGATORS[lang];
  let raw = 0, pos = 0, negc = 0;
  words.forEach((w, i) => {
    if (!lex.has(w)) return;
    const v0 = lex.get(w);
    if (v0 > 0) pos++;
    if (v0 < 0) negc++;
    let v = v0;
    if (i > 0 && BOOSTERS.has(words[i - 1])) v = v * (1 + BOOSTERS.get(words[i - 1]));
    for (let k = Math.max(0, i - 3); k < i; k++) {
      if (neg.has(words[k])) { v = v * -0.75; break; }
    }
    raw += v;
  });
  const score = raw / Math.sqrt(raw * raw + 15);
  const label = score >= 0.05 ? 'positive' : score <= -0.05 ? 'negative' : 'neutral';
  return { score: round2(score), label, positive_hits: pos, negative_hits: negc };
}

function compareCodePoints(a, b) {
  const x = Array.from(a), y = Array.from(b);
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const d = x[i].codePointAt(0) - y[i].codePointAt(0);
    if (d !== 0) return d;
  }
  return x.length - y.length;
}

function analyse(text, lang) {
  const sc = scan(text);
  const words = sc.words;
  const language = lang === 'en' || lang === 'de' ? lang : detectLanguage(words);
  const counts = new Map();
  for (const w of words) {
    if (Array.from(w).length >= 3 && !STOP.en.has(w) && !STOP.de.has(w)) counts.set(w, (counts.get(w) || 0) + 1);
  }
  const top = [...counts.entries()].sort((a, b) => b[1] - a[1] || compareCodePoints(a[0], b[0])).slice(0, 5);
  const cps = Array.from(text);
  return {
    characters: cps.length,
    characters_no_space: cps.filter((c) => !isSpace(c)).length,
    language,
    lines: countLines(text),
    numbers: sc.numbers,
    paragraphs: sc.paragraphs,
    readability: readability(words, sc.sentences, language),
    sentences: sc.sentences,
    sentiment: sentiment(words, language),
    top_terms: top.map(([term, count]) => ({ count, term })),
    unique_words: new Set(words).size,
    words: words.length,
  };
}

function str(v) {
  let out = '"';
  for (const ch of v) {
    const c = ch.codePointAt(0);
    if (ch === '"') out += '\\"';
    else if (ch === '\\') out += '\\\\';
    else if (c < 0x20) out += `\\u${c.toString(16).padStart(4, '0')}`;
    else out += ch;
  }
  return out + '"';
}

function dump(v, depth) {
  const pad = '  '.repeat(depth), inner = '  '.repeat(depth + 1);
  if (v === null || v === undefined) return 'null';
  if (v instanceof R) return short(v.hundredths);
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (typeof v === 'number') return String(v);
  if (typeof v === 'string') return str(v);
  if (Array.isArray(v)) {
    if (v.length === 0) return '[]';
    return '[\n' + v.map((x) => inner + dump(x, depth + 1)).join(',\n') + '\n' + pad + ']';
  }
  const keys = Object.keys(v).sort(compareCodePoints);
  if (keys.length === 0) return '{}';
  return '{\n' + keys.map((k) => `${inner}${str(k)}: ${dump(v[k], depth + 1)}`).join(',\n') + '\n' + pad + '}';
}

const toJson = (obj) => dump(obj, 0) + '\n';

function thousands(n) {
  let s = String(Math.abs(n));
  const parts = [];
  while (s.length > 3) { parts.unshift(s.slice(-3)); s = s.slice(0, -3); }
  parts.unshift(s);
  return (n < 0 ? '-' : '') + parts.join(',');
}

function render(name, a) {
  const out = [
    `Analysis of ${name}`,
    `  Words: ${thousands(a.words)}   Sentences: ${thousands(a.sentences)}   Paragraphs: ${thousands(a.paragraphs)}`,
    `  Characters: ${thousands(a.characters)} (${thousands(a.characters_no_space)} without spaces)   Language: ${a.language}`,
    '  Top terms: ' + (a.top_terms.map((t) => `${t.term} (${t.count})`).join(', ') || 'none'),
  ];
  if (a.sentiment) {
    const s = a.sentiment, h = s.score.hundredths;
    out.push(`  Sentiment: ${s.label} (${h >= 0 ? '+' : ''}${fixed(h)}; ${s.positive_hits} positive and ${s.negative_hits} negative words)`);
  }
  if (a.readability) {
    out.push('  Readability: ' + Object.entries(a.readability).sort((x, y) => compareCodePoints(x[0], y[0])).map(([k, v]) => `${k.replace(/_/g, ' ')} ${fixed(v.hundredths)}`).join(', '));
  }
  return out.join('\n') + '\n';
}

function main(argv) {
  const args = argv.slice();
  const asJson = args.includes('--json');
  let lang = null;
  const k = args.indexOf('--lang');
  if (k >= 0) {
    lang = args[k + 1];
    args.splice(k, 2);
    if (lang !== 'en' && lang !== 'de') { process.stderr.write('error: --lang must be en or de\n'); return 2; }
  }
  const files = args.filter((a) => a !== '--json');
  if (files.length === 0) { process.stderr.write('usage: analyzer.js FILE... [--json] [--lang en|de]\n'); return 2; }
  const results = new Map();
  for (const f of files) {
    let text;
    try {
      text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(fs.readFileSync(f));
    } catch (e) {
      process.stderr.write(`error: cannot read ${f}: ${e.message}\n`);
      return 2;
    }
    results.set(f, analyse(text, lang));
  }
  if (asJson) {
    process.stdout.write(toJson(results.size === 1 ? [...results.values()][0] : Object.fromEntries(results)));
  } else {
    for (const [f, a] of results) process.stdout.write(render(f, a));
  }
  return 0;
}

module.exports = { analyse, toJson, render, scan, syllables, round2, main, R };
