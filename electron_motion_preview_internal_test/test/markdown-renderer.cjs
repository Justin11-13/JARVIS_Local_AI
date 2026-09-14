const test = require('node:test');
const assert = require('node:assert/strict');

const { parse } = require('../renderer/markdown-renderer.js');

test('parses the display Markdown blocks used by JARVIS replies', () => {
  const blocks = parse([
    '# XML guide',
    '',
    'Use **structured** output and `code`.',
    '',
    '1. Concepts',
    '2. Syntax',
    '',
    '- Example',
    '- Validation',
    '',
    '```python',
    'print("safe text")',
    '```',
  ].join('\n'));

  assert.deepEqual(
    blocks.map(({ type }) => type),
    ['heading', 'paragraph', 'list', 'list', 'code'],
  );
  assert.equal(blocks[0].level, 1);
  assert.equal(blocks[1].lines[0], 'Use **structured** output and `code`.');
  assert.equal(blocks[2].ordered, true);
  assert.deepEqual(blocks[2].items, ['Concepts', 'Syntax']);
  assert.equal(blocks[3].ordered, false);
  assert.equal(blocks[4].language, 'python');
  assert.equal(blocks[4].text, 'print("safe text")');
});

test('normalizes line endings and keeps raw HTML in text input', () => {
  const blocks = parse('<script>alert(1)</script>\r\nnext line');

  assert.equal(blocks.length, 1);
  assert.equal(blocks[0].type, 'paragraph');
  assert.deepEqual(blocks[0].lines, ['<script>alert(1)</script>', 'next line']);
});

test('separates a compact numbered answer into an intro and ordered list', () => {
  const blocks = parse('Choose a topic: 1. Concepts 2. Syntax 3. Examples');

  assert.deepEqual(blocks, [
    { type: 'paragraph', lines: ['Choose a topic:'] },
    { type: 'list', ordered: true, items: ['Concepts', 'Syntax', 'Examples'] },
  ]);
});
