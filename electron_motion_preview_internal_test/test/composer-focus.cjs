const assert = require('node:assert/strict');
const { focusInput, isFocusShortcut, isImeEnter } = require('../renderer/composer-behavior.js');

assert.equal(isImeEnter({ key: 'Enter', isComposing: true }), true);
assert.equal(isImeEnter({ key: 'Enter', keyCode: 229 }), true);
assert.equal(isImeEnter({ key: 'Enter' }, true), true);
assert.equal(isImeEnter({ key: 'Enter' }), false);

assert.equal(isFocusShortcut({ key: 'l', ctrlKey: true }), true);
assert.equal(isFocusShortcut({ key: 'L', ctrlKey: true }), true);
assert.equal(isFocusShortcut({ key: 'l', ctrlKey: true, shiftKey: true }), false);
assert.equal(isFocusShortcut({ key: 'l', ctrlKey: true, altKey: true }), false);
assert.equal(isFocusShortcut({ key: 'k', ctrlKey: true }), false);

const input = {
  value: 'keep this draft',
  disabled: false,
  focusOptions: null,
  selection: null,
  focus(options) {
    this.focusOptions = options;
  },
  setSelectionRange(start, end) {
    this.selection = [start, end];
  },
};
assert.equal(focusInput(input), true);
assert.deepEqual(input.focusOptions, { preventScroll: true });
assert.deepEqual(input.selection, [input.value.length, input.value.length]);
assert.equal(input.value, 'keep this draft');
assert.equal(focusInput({ value: 'draft', disabled: true, focus() {} }), false);

console.log(JSON.stringify({ verification: 'passed', scope: 'composer-focus-behavior' }));
