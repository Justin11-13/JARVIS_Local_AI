(function attachResponseStream(global) {
  const DISPLAY_MARKER = '[DISPLAY]';
  const VOICE_MARKER = '[VOICE_EN]';

  function normalizeLineEndings(value) {
    return String(value || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  }

  function speechTextWithoutPresentationMarkup(value) {
    const parts = normalizeLineEndings(value).split('```');
    for (let index = 0; index < parts.length; index += 2) {
      parts[index] = parts[index]
        .replace(/^[ \t]*#{1,6}[ \t]+/gm, '')
        .replace(/^[ \t]*[-+*][ \t]+/gm, '• ')
        .replace(/\*{1,3}(.+?)\*{1,3}/g, '$1')
        .replace(/_{1,3}(.+?)_{1,3}/g, '$1');
    }
    return parts.join('```');
  }

  function plainSpeechText(value) {
    return speechTextWithoutPresentationMarkup(value).trim();
  }

  function detectSpeechLanguage(value) {
    const text = normalizeLineEndings(value);
    const hanCount = (text.match(/[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g) || []).length;
    const latinCount = (text.match(/[A-Za-z]/g) || []).length;
    if (hanCount === 0) return 'en';
    if (latinCount === 0) return 'zh';
    return hanCount >= 2 && hanCount >= latinCount * 0.2 ? 'zh' : 'en';
  }

  function isChineseVoice(voice) {
    const language = typeof voice?.language === 'string'
      ? voice.language.trim().toLowerCase().replace(/_/g, '-')
      : '';
    return language === 'zh' || language.startsWith('zh-');
  }

  function selectSpeechVoiceForText(text, voices, selectedVoiceId = '') {
    const selected = typeof selectedVoiceId === 'string' ? selectedVoiceId.trim() : '';
    if (detectSpeechLanguage(text) !== 'zh') return selected || null;

    const availableVoices = Array.isArray(voices) ? voices : [];
    const selectedVoice = availableVoices.find((voice) => voice && voice.id === selected);
    if (selected && isChineseVoice(selectedVoice)) return selected;

    const chineseVoice = availableVoices.find((voice) => {
      const language = typeof voice?.language === 'string'
        ? voice.language.trim().toLowerCase().replace(/_/g, '-')
        : '';
      return language === 'zh-cn';
    }) || availableVoices.find((voice) => isChineseVoice(voice));
    return chineseVoice?.id || selected || null;
  }

  function removeDisplayMarker(value, complete) {
    const leading = value.trimStart();
    if (leading.startsWith(DISPLAY_MARKER)) {
      const offset = value.length - leading.length + DISPLAY_MARKER.length;
      return value.slice(offset).replace(/^\n/, '');
    }
    if (!complete && DISPLAY_MARKER.startsWith(leading)) return '';
    return value;
  }

  function project(rawText, complete = false) {
    const raw = normalizeLineEndings(rawText);
    const voiceIndex = raw.indexOf(VOICE_MARKER);
    let displaySource = voiceIndex >= 0 ? raw.slice(0, voiceIndex) : raw;
    if (voiceIndex < 0 && !complete) {
      for (let length = VOICE_MARKER.length - 1; length > 0; length -= 1) {
        const suffix = VOICE_MARKER.slice(0, length);
        if (raw.endsWith(suffix)) {
          displaySource = raw.slice(0, -length);
          break;
        }
      }
    }
    const display = removeDisplayMarker(displaySource, complete);
    const speech = voiceIndex >= 0
      ? raw.slice(voiceIndex + VOICE_MARKER.length).trim()
      : complete
        ? plainSpeechText(display)
        : '';
    return { display, speech };
  }

  class StreamProjector {
    constructor() {
      this.raw = '';
      this.speech = '';
      this.displaySpeechSource = '';
    }

    append(delta) {
      this.raw += String(delta || '');
      return this._state(false);
    }

    finish() {
      return this._state(true);
    }

    _state(complete) {
      const next = project(this.raw, complete);
      // The model emits the complete DISPLAY block before VOICE_EN. Use the
      // visible response as the provisional streaming speech source so TTS
      // can start during generation. Keep `speech` as the canonical terminal
      // VOICE_EN narration for the existing completed-response contract.
      const displayDelta = next.display.startsWith(this.displaySpeechSource)
        ? next.display.slice(this.displaySpeechSource.length)
        : '';
      const speechDelta = speechTextWithoutPresentationMarkup(displayDelta);
      this.displaySpeechSource = next.display;
      this.speech = next.speech;
      return {
        raw: this.raw,
        display: next.display,
        speech: next.speech,
        speechDelta,
        complete,
      };
    }
  }

  class SpeechChunker {
    constructor({ minChars = 72, maxChars = 240 } = {}) {
      this.minChars = minChars;
      this.maxChars = maxChars;
      this.buffer = '';
    }

    push(text) {
      this.buffer += String(text || '');
      return this._drain(false);
    }

    flush() {
      return this._drain(true);
    }

    hasPendingText() {
      return Boolean(this.buffer.trim());
    }

    _drain(force) {
      const chunks = [];
      while (this.buffer) {
        const boundary = this._boundaryIndex();
        if (!force && boundary < 0 && this.buffer.length < this.maxChars) break;
        if (!force && boundary >= 0 && boundary < this.minChars && this.buffer.length < this.maxChars) {
          break;
        }
        let cut = boundary >= 0 ? boundary : this.maxChars;
        if (cut > this.maxChars) cut = this.maxChars;
        if (boundary < 0 && this.buffer.length <= this.maxChars) cut = this.buffer.length;
        if (cut <= 0) break;
        const chunk = this.buffer.slice(0, cut).trim();
        this.buffer = this.buffer.slice(cut).trimStart();
        if (chunk) chunks.push(chunk);
      }
      if (force && this.buffer.trim()) {
        chunks.push(this.buffer.trim());
        this.buffer = '';
      }
      return chunks;
    }

    _boundaryIndex() {
      const sentencePunctuation = /[。！？；]|[.!?;](?=\s|$)|\n/g;
      let match;
      let latestBoundary = -1;
      while ((match = sentencePunctuation.exec(this.buffer)) !== null) {
        const boundary = match.index + match[0].length;
        if (boundary > this.maxChars) break;
        if (boundary >= this.minChars) latestBoundary = boundary;
      }
      if (latestBoundary >= 0) return latestBoundary;
      if (this.buffer.length < this.maxChars) return -1;
      const whitespace = this.buffer.slice(0, this.maxChars + 1).lastIndexOf(' ');
      return whitespace >= this.minChars ? whitespace : -1;
    }
  }

  class DisplayPacer {
    constructor({ charsPerSecond = 42, tickMs = 50, onUpdate = () => {} } = {}) {
      this.charsPerSecond = Math.max(1, Number(charsPerSecond) || 42);
      this.tickMs = Math.max(16, Number(tickMs) || 50);
      this.onUpdate = typeof onUpdate === 'function' ? onUpdate : () => {};
      this.target = '';
      this.visible = '';
      this.timer = null;
      this.waiters = [];
    }

    setTarget(value) {
      const next = String(value || '');
      this.target = next;
      if (this.visible.length > next.length || !next.startsWith(this.visible)) {
        this.visible = next.slice(0, Math.min(this.visible.length, next.length));
      }
      this._pump();
    }

    drain() {
      if (this.visible === this.target) return Promise.resolve();
      return new Promise((resolve) => this.waiters.push(resolve));
    }

    cancel() {
      if (this.timer !== null) {
        clearTimeout(this.timer);
        this.timer = null;
      }
      this.target = this.visible;
      this._resolveWaiters();
    }

    _resolveWaiters() {
      if (this.visible !== this.target) return;
      const waiters = this.waiters.splice(0);
      waiters.forEach((resolve) => resolve());
    }

    _pump() {
      if (this.timer !== null || this.visible === this.target) {
        this._resolveWaiters();
        return;
      }
      this.timer = setTimeout(() => {
        this.timer = null;
        if (this.target.startsWith(this.visible)) {
          const step = Math.max(1, Math.round(this.charsPerSecond * this.tickMs / 1000));
          this.visible = this.target.slice(0, this.visible.length + step);
        } else {
          this.visible = this.target;
        }
        this.onUpdate(this.visible);
        this._resolveWaiters();
        this._pump();
      }, this.tickMs);
    }
  }

  global.JarvisResponseStream = Object.freeze({
    detectSpeechLanguage,
    DisplayPacer,
    isChineseVoice,
    selectSpeechVoiceForText,
    StreamProjector,
    SpeechChunker,
    plainSpeechText,
    project,
  });
})(typeof window !== 'undefined' ? window : globalThis);
