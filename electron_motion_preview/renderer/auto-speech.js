(function exposeAutoSpeech(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.JarvisAutoSpeech = api;
})(typeof window !== 'undefined' ? window : globalThis, () => {
  function errorMessage(error) {
    return error && typeof error.message === 'string' && error.message.trim()
      ? error.message.trim()
      : 'Automatic speech failed.';
  }

  function now() {
    return typeof performance !== 'undefined' && typeof performance.now === 'function'
      ? performance.now()
      : Date.now();
  }

  function create(options = {}) {
    const synthesize = typeof options.synthesize === 'function' ? options.synthesize : null;
    const play = typeof options.play === 'function' ? options.play : null;
    const stop = typeof options.stop === 'function' ? options.stop : null;
    const onState = typeof options.onState === 'function' ? options.onState : () => {};
    let enabled = false;
    let current = null;
    let next = null;
    let runner = null;
    let generation = 0;
    let lastError = '';
    const seen = new Set();
    const seenOrder = [];
    const pending = [];
    const maxQueued = Number.isInteger(options.maxQueued)
      ? Math.max(1, options.maxQueued)
      : 8;

    function itemSnapshot(item) {
      return item ? {
        id: item.id,
        state: item.state,
        createdAt: item.createdAt,
        audioReadyAt: item.audioReadyAt ?? null,
        playbackStartedAt: item.playbackStartedAt ?? null,
        playbackEndedAt: item.playbackEndedAt ?? null,
      } : null;
    }

    function report(state, error = lastError) {
      lastError = error || '';
      onState({
        enabled,
        state,
        pending: Number(Boolean(current)) + Number(Boolean(next)) + pending.length,
        current: itemSnapshot(current),
        next: itemSnapshot(next),
        error: lastError,
      });
    }

    function remember(id) {
      seen.add(id);
      seenOrder.push(id);
      while (seenOrder.length > 1024) seen.delete(seenOrder.shift());
    }

    function hasCapacity() {
      return !current || !next;
    }

    function place(item) {
      remember(item.id);
      if (!current) current = item;
      else if (!next) next = item;
      else pending.push(item);
      report(current === item ? 'buffering' : 'queued');
      pump();
    }

    function promotePending() {
      if (!current && pending.length) current = pending.shift();
      if (!next && pending.length) next = pending.shift();
    }

    function joinPendingText(first, second) {
      const needsSpace = /[A-Za-z0-9]$/.test(first) && /^[A-Za-z0-9]/.test(second);
      return `${first}${needsSpace ? ' ' : ''}${second}`;
    }

    async function prepare(item) {
      if (item.audio || item.failed) return item.audio;
      if (item.preparing) return item.preparePromise;
      const itemGeneration = generation;
      item.preparing = true;
      item.state = 'synthesizing';
      report(current === item ? 'synthesizing' : 'queued');
      item.preparePromise = (async () => {
        try {
          if (!synthesize) throw new Error('Automatic speech synthesis bridge is unavailable.');
          const audio = await synthesize(item.text, item.voiceId);
          if (itemGeneration !== generation) return null;
          if (!audio) throw new Error('Automatic speech synthesis returned no audio.');
          item.audio = audio;
          item.audioReadyAt = now();
          item.state = 'ready';
          report(current === item ? 'ready' : 'queued');
          return item.audio;
        } catch (error) {
          if (itemGeneration !== generation) return null;
          item.failed = true;
          item.state = 'error';
          report('error', errorMessage(error));
          return null;
        } finally {
          item.preparing = false;
          item.preparePromise = null;
        }
      })();
      return item.preparePromise;
    }

    async function run() {
      const runGeneration = generation;
      while (enabled && current && runGeneration === generation) {
        const item = current;
        const audio = await prepare(item);
        if (!enabled || runGeneration !== generation || current !== item) return;
        if (next) void prepare(next);
        if (!audio || !play) {
          if (!audio && item.state !== 'error') report('error', 'Automatic speech returned no audio.');
          item.state = item.state === 'error' ? 'error' : 'completed';
        } else {
          item.state = 'playing';
          item.playbackStartedAt = now();
          report('playing');
          try {
            await play(audio, item);
            item.playbackEndedAt = now();
            if (runGeneration !== generation) return;
          } catch (error) {
            item.playbackEndedAt = now();
            item.state = 'error';
            report('error', errorMessage(error));
          }
        }
        if (current !== item || runGeneration !== generation) return;
        if (item.state !== 'error') item.state = 'completed';
        current = next;
        next = null;
        promotePending();
        report(current ? 'buffering' : 'ready', '');
      }
    }

    function pump() {
      if (runner || !enabled || !current) return;
      runner = run().catch((error) => report('error', errorMessage(error))).finally(() => {
        runner = null;
        if (enabled && current) pump();
      });
    }

    function cancel(reason = 'Automatic speech cancelled.') {
      generation += 1;
      if (current) current.state = 'cancelled';
      if (next) next.state = 'cancelled';
      pending.forEach((item) => { item.state = 'cancelled'; });
      current = null;
      next = null;
      pending.length = 0;
      if (enabled) report('cancelled', reason);
      if (stop) {
        try {
          const stopResult = stop();
          if (stopResult && typeof stopResult.catch === 'function') {
            stopResult.catch((error) => report('error', errorMessage(error)));
          }
        } catch (error) {
          report('error', errorMessage(error));
        }
      }
    }

    function setEnabled(nextEnabled) {
      const shouldEnable = nextEnabled === true;
      if (shouldEnable === enabled) return enabled;
      enabled = shouldEnable;
      if (!enabled) {
        cancel('Automatic speech disabled.');
        report('off', '');
        return enabled;
      }
      report(synthesize && play ? 'ready' : 'error', synthesize && play ? '' : 'Automatic speech bridge is unavailable.');
      pump();
      return enabled;
    }

    function enqueue(id, text, options = {}) {
      const normalizedId = typeof id === 'string' ? id.trim() : '';
      const normalizedText = typeof text === 'string' ? text.trim() : '';
      const voiceId = typeof options?.voiceId === 'string' && options.voiceId.trim()
        ? options.voiceId.trim()
        : null;
      if (!enabled || !normalizedId || !normalizedText || seen.has(normalizedId)) return Promise.resolve(false);
      const item = {
        id: normalizedId,
        text: normalizedText,
        voiceId,
        state: 'buffering',
        createdAt: now(),
        audio: null,
        audioReadyAt: null,
        playbackStartedAt: null,
        playbackEndedAt: null,
        preparing: false,
        failed: false,
      };
      if (hasCapacity()) {
        place(item);
        return Promise.resolve(true);
      }
      if (pending.length >= maxQueued) {
        const tail = pending[pending.length - 1];
        tail.text = joinPendingText(tail.text, item.text);
        remember(item.id);
        report('queued');
        return Promise.resolve(true);
      }
      place(item);
      return Promise.resolve(true);
    }

    return {
      cancel,
      enqueue,
      isEnabled: () => enabled,
      pendingCount: () => Number(Boolean(current)) + Number(Boolean(next)) + pending.length,
      setEnabled,
      snapshot: () => ({
        enabled,
        pending: Number(Boolean(current)) + Number(Boolean(next)) + pending.length,
        speaking: Boolean(current?.state === 'playing'),
        current: itemSnapshot(current),
        next: itemSnapshot(next),
      }),
    };
  }

  return { create };
});
