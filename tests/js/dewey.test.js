'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { analyse, toJson, R } = require('../../js/dewey');

const spec = (name) => JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'spec', name), 'utf8'));
const pick = (tree, p) => p.split('.').reduce((cur, part) => (Array.isArray(cur) ? cur[Number(part)] : cur[part]), tree);

test('every vector matches', () => {
  for (const v of spec('vectors.json')) assert.strictEqual(toJson(analyse(v.text, v.lang)), v.expect, v.name);
});

test('hand verified values', () => {
  for (const h of spec('hand_verified.json')) {
    const a = analyse(h.text, h.lang);
    for (const [p, want] of Object.entries(h.checks)) {
      const got = pick(a, p);
      if (got instanceof R) assert.strictEqual(got.hundredths, Math.round(want * 100), `${h.name} ${p}`);
      else assert.deepStrictEqual(got, want, `${h.name} ${p}`);
    }
  }
});

test('characters are code points, not UTF-16 units', () => {
  assert.strictEqual(analyse('café 😀').characters, 6);
});
