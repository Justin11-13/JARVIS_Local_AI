(function exposeComposerBehavior(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.JarvisComposerBehavior = api;
})(typeof window !== 'undefined' ? window : globalThis, () => {
  function isImeEnter(event, compositionActive = false) {
    return Boolean(
      compositionActive
      || event?.isComposing
      || event?.keyCode === 229,
    );
  }

  function isFocusShortcut(event) {
    return Boolean(
      event?.ctrlKey
      && !event?.altKey
      && !event?.metaKey
      && !event?.shiftKey
      && typeof event?.key === 'string'
      && event.key.toLowerCase() === 'l',
    );
  }

  function focusInput(input) {
    if (!input || input.disabled || typeof input.focus !== 'function') return false;
    input.focus({ preventScroll: true });
    if (typeof input.setSelectionRange === 'function') {
      const end = input.value.length;
      input.setSelectionRange(end, end);
    }
    return true;
  }

  return { focusInput, isFocusShortcut, isImeEnter };
});
