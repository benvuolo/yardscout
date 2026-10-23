#!/usr/bin/env node
/**
 * check_string_joins.js — flag "word-butting" string joins in JS.
 *
 * The 'whateach' class of bug: two prose fragments are concatenated and the
 * seam has a word character on both sides, so the rendered sentence is
 * missing a space ("We flag what" + "each car" -> "We flag whateach car").
 *
 * What it flags:
 *   1. `'... word' + 'word ...'`  — adjacent + joins (incl. across newlines)
 *   2. `['... word', 'word ...'].join('')` — empty-separator joins of fragments
 *
 * Heuristic to keep noise down: a seam only counts when at least one side
 * looks like prose (contains a space). Identifier/URL/key building like
 * `'jh_' + key` or `base + '/api'` is ignored.
 *
 * Usage:  node tools/check_string_joins.js [files...]
 *         (defaults to docs/*.js + backend/src/*.js)
 * Exit 1 if any seam is found — safe to wire into a pre-push hook.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const repo = path.resolve(__dirname, '..');
const defaults = [];
for (const dir of ['docs', 'backend/src']) {
  const abs = path.join(repo, dir);
  if (!fs.existsSync(abs)) continue;
  for (const f of fs.readdirSync(abs)) {
    if (f.endsWith('.js') && f !== 'sw.js') defaults.push(path.join(abs, f));
  }
}
const files = process.argv.slice(2).length ? process.argv.slice(2) : defaults;

const WORD = /[A-Za-z0-9]/;
// A string literal that we can scan without a real parser: no escapes-aware
// nesting needed for the ' + ' seam check because we only look at the literal
// boundary characters. Backtick templates are matched naively (a `${}` whose
// expression itself contains a backtick would confuse it — rare enough).
const LIT = '(?:\'(?:[^\'\\\\\\n]|\\\\.)*\'|"(?:[^"\\\\\\n]|\\\\.)*"|`(?:[^`\\\\]|\\\\.)*`)';

/** Does this literal's CONTENT end (or start) with a word char, and does
 * either side look like prose (contains a space)? */
function unquote(lit) {
  // Interpret common escapes so `\u2019` / `\'` don't masquerade as word chars.
  // `${expr}` in templates becomes a neutral (non-word) placeholder: dynamic
  // seams aren't this checker's business.
  return lit
    .slice(1, -1)
    .replace(/\$\{[^}]*\}/g, '\x00')
    .replace(/\\u\{?[0-9a-fA-F]+\}?/g, '\u2019') // any unicode escape: treat as punctuation
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, ' ')
    .replace(/\\(.)/g, '$1');
}

function isProse(s) { return s.includes(' '); }

let hits = 0;

for (const file of files) {
  const src = fs.readFileSync(file, 'utf8');
  const rel = path.relative(repo, file);

  // ---- 1. adjacent `+` joins, including across line breaks ----------------
  const joinRe = new RegExp(`(${LIT})\\s*\\+\\s*(${LIT})`, 'g');
  let m;
  while ((m = joinRe.exec(src)) !== null) {
    const left = unquote(m[1]);
    const right = unquote(m[2]);
    if (!left || !right) continue;
    const seamL = left[left.length - 1];
    const seamR = right[0];
    if (WORD.test(seamL) && WORD.test(seamR) && (isProse(left) || isProse(right))) {
      const line = src.slice(0, m.index).split('\n').length;
      console.log(`${rel}:${line}: word-butting '+' join: ...${JSON.stringify(left.slice(-18))} + ${JSON.stringify(right.slice(0, 18))}...`);
      hits++;
    }
    // Re-scan from the right literal so chains a+b+c check every seam.
    joinRe.lastIndex = m.index + m[0].length - m[2].length;
  }

  // ---- 2. array-of-fragments .join('') ------------------------------------
  const arrJoinRe = /\[([^\[\]]*)\]\s*\.join\(\s*(''|"")\s*\)/g;
  while ((m = arrJoinRe.exec(src)) !== null) {
    const inner = m[1];
    const lits = inner.match(new RegExp(LIT, 'g')) || [];
    for (let i = 0; i + 1 < lits.length; i++) {
      const left = unquote(lits[i]);
      const right = unquote(lits[i + 1]);
      if (!left || !right) continue;
      if (WORD.test(left[left.length - 1]) && WORD.test(right[0]) && (isProse(left) || isProse(right))) {
        const line = src.slice(0, m.index).split('\n').length;
        console.log(`${rel}:${line}: word-butting .join(''): ...${JSON.stringify(left.slice(-18))} | ${JSON.stringify(right.slice(0, 18))}...`);
        hits++;
      }
    }
  }
}

if (hits) {
  console.log(`\n${hits} word-butting join(s) found.`);
  process.exit(1);
}
console.log(`OK — no word-butting string joins in ${files.length} file(s).`);
