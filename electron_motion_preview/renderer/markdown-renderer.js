(function exposeMarkdownRenderer(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.JarvisMarkdownRenderer = api;
})(typeof window !== 'undefined' ? window : globalThis, () => {
  const FENCE_START = /^\s*```([A-Za-z0-9_+-]*)\s*$/;
  const FENCE_END = /^\s*```\s*$/;
  const HEADING = /^\s{0,3}(#{1,6})\s+(.+?)\s*$/;
  const QUOTE = /^\s{0,3}>\s?(.*)$/;
  const UNORDERED_ITEM = /^\s{0,3}[-+*]\s+(.+?)\s*$/;
  const ORDERED_ITEM = /^\s{0,3}\d+[.)、]\s+(.+?)\s*$/;
  const INLINE_TOKEN_PATTERN = /(`[^`\n]+`|\[[^\]\n]+\]\([^\s)]+\)|\*\*[^*\n]+\*\*|__[^_\n]+__|\*[^*\n]+\*|_[^_\n]+_)/;
  const SAFE_LINK_PROTOCOLS = new Set(['http:', 'https:', 'mailto:']);

  function normalize(value) {
    return String(value == null ? '' : value).replace(/\r\n?/g, '\n');
  }

  function headingMatch(line) {
    return line.match(HEADING);
  }

  function horizontalRule(line) {
    const value = line.trim();
    return /^(?:\*\s*){3,}$/.test(value)
      || /^(?:-\s*){3,}$/.test(value)
      || /^(?:_\s*){3,}$/.test(value);
  }

  function listMatch(line) {
    const unordered = line.match(UNORDERED_ITEM);
    if (unordered) return { ordered: false, text: unordered[1] };
    const ordered = line.match(ORDERED_ITEM);
    if (ordered) return { ordered: true, text: ordered[1] };
    return null;
  }

  function compactOrderedList(line) {
    const marker = /(?:^|\s)(\d+)[.)、]\s+/g;
    const matches = [...line.matchAll(marker)];
    if (matches.length < 2 || Number(matches[0][1]) !== 1) return null;
    for (let index = 1; index < matches.length; index += 1) {
      if (Number(matches[index][1]) !== index + 1) return null;
    }
    const items = matches.map((match, index) => {
      const start = match.index + match[0].length;
      const end = index + 1 < matches.length ? matches[index + 1].index : line.length;
      return line.slice(start, end).trim();
    });
    return {
      prefix: line.slice(0, matches[0].index).trim(),
      items,
    };
  }

  function isBlockStart(line) {
    return Boolean(
      line.match(FENCE_START)
      || headingMatch(line)
      || line.match(QUOTE)
      || listMatch(line)
      || horizontalRule(line),
    );
  }

  function parse(source) {
    const lines = normalize(source).split('\n');
    const blocks = [];
    let index = 0;

    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) {
        index += 1;
        continue;
      }

      const fence = line.match(FENCE_START);
      if (fence) {
        const codeLines = [];
        index += 1;
        while (index < lines.length && !FENCE_END.test(lines[index])) {
          codeLines.push(lines[index]);
          index += 1;
        }
        if (index < lines.length) index += 1;
        blocks.push({ type: 'code', language: fence[1] || '', text: codeLines.join('\n') });
        continue;
      }

      const heading = headingMatch(line);
      if (heading) {
        blocks.push({
          type: 'heading',
          level: heading[1].length,
          text: heading[2].replace(/\s+#+\s*$/, '').trim(),
        });
        index += 1;
        continue;
      }

      if (horizontalRule(line)) {
        blocks.push({ type: 'hr' });
        index += 1;
        continue;
      }

      const quote = line.match(QUOTE);
      if (quote) {
        const quoteLines = [];
        while (index < lines.length) {
          const nextQuote = lines[index].match(QUOTE);
          if (!nextQuote) break;
          quoteLines.push(nextQuote[1]);
          index += 1;
        }
        blocks.push({ type: 'quote', lines: quoteLines });
        continue;
      }

      const compactList = compactOrderedList(line);
      if (compactList) {
        if (compactList.prefix) blocks.push({ type: 'paragraph', lines: [compactList.prefix] });
        blocks.push({ type: 'list', ordered: true, items: compactList.items });
        index += 1;
        continue;
      }

      const firstItem = listMatch(line);
      if (firstItem) {
        const items = [];
        while (index < lines.length) {
          const item = listMatch(lines[index]);
          if (!item || item.ordered !== firstItem.ordered) break;
          items.push(item.text);
          index += 1;
        }
        blocks.push({ type: 'list', ordered: firstItem.ordered, items });
        continue;
      }

      const paragraphLines = [line];
      index += 1;
      while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) {
        paragraphLines.push(lines[index]);
        index += 1;
      }
      blocks.push({ type: 'paragraph', lines: paragraphLines });
    }

    return blocks;
  }

  function safeHref(value) {
    const candidate = value.trim();
    try {
      const url = new URL(candidate);
      return SAFE_LINK_PROTOCOLS.has(url.protocol) ? url.href : null;
    } catch (_error) {
      return null;
    }
  }

  function appendInline(parent, value) {
    const text = String(value == null ? '' : value);
    const tokens = new RegExp(INLINE_TOKEN_PATTERN.source, 'g');
    let cursor = 0;
    let match = tokens.exec(text);
    while (match) {
      if (match.index > cursor) parent.append(document.createTextNode(text.slice(cursor, match.index)));
      const token = match[0];
      if (token.startsWith('`')) {
        const code = document.createElement('code');
        code.textContent = token.slice(1, -1);
        parent.append(code);
      } else if (token.startsWith('[')) {
        const link = token.match(/^\[([^\]\n]+)\]\(([^)\s]+)\)$/);
        const href = link && safeHref(link[2]);
        if (!link || !href) {
          appendInline(parent, link ? link[1] : token);
        } else {
          const anchor = document.createElement('a');
          anchor.textContent = link[1];
          anchor.href = href;
          anchor.target = '_blank';
          anchor.rel = 'noreferrer noopener';
          parent.append(anchor);
        }
      } else if (token.startsWith('**') || token.startsWith('__')) {
        const strong = document.createElement('strong');
        appendInline(strong, token.slice(2, -2));
        parent.append(strong);
      } else {
        const emphasis = document.createElement('em');
        appendInline(emphasis, token.slice(1, -1));
        parent.append(emphasis);
      }
      cursor = match.index + token.length;
      match = tokens.exec(text);
    }
    if (cursor < text.length) parent.append(document.createTextNode(text.slice(cursor)));
  }

  function appendLines(parent, lines) {
    lines.forEach((line, index) => {
      if (index > 0) parent.append(document.createElement('br'));
      appendInline(parent, line);
    });
  }

  function createBlock(block) {
    if (block.type === 'code') {
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      if (block.language) pre.dataset.language = block.language;
      code.textContent = block.text;
      pre.append(code);
      return pre;
    }
    if (block.type === 'heading') {
      const heading = document.createElement(`h${block.level}`);
      appendInline(heading, block.text);
      return heading;
    }
    if (block.type === 'hr') return document.createElement('hr');
    if (block.type === 'list') {
      const list = document.createElement(block.ordered ? 'ol' : 'ul');
      block.items.forEach((item) => {
        const listItem = document.createElement('li');
        appendInline(listItem, item);
        list.append(listItem);
      });
      return list;
    }
    if (block.type === 'quote') {
      const quote = document.createElement('blockquote');
      const paragraph = document.createElement('p');
      appendLines(paragraph, block.lines);
      quote.append(paragraph);
      return quote;
    }
    const paragraph = document.createElement('p');
    appendLines(paragraph, block.lines || []);
    return paragraph;
  }

  function render(container, source) {
    if (!container || typeof container.replaceChildren !== 'function') {
      throw new TypeError('A DOM container is required for Markdown rendering.');
    }
    const blocks = parse(source);
    container.replaceChildren();
    if (!blocks.length) {
      container.append(document.createElement('p'));
      return blocks;
    }
    blocks.forEach((block) => container.append(createBlock(block)));
    return blocks;
  }

  return { parse, render };
});
