(function exposeConversationStore(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.JarvisConversationStore = api;
})(typeof window !== 'undefined' ? window : globalThis, () => {
  const failureStatuses = new Set(['failed', 'error', 'session_busy', 'cancelled']);

  function normalizedToolStatus(toolResult) {
    if (!toolResult || typeof toolResult !== 'object') return 'failed';
    if (toolResult.success === true && toolResult.status === 'completed') return 'completed';
    if (toolResult.success === null && toolResult.status === 'awaiting_confirmation') {
      return 'awaiting_confirmation';
    }
    if (typeof toolResult.status === 'string' && toolResult.status.trim()) {
      return toolResult.status;
    }
    return 'failed';
  }

  function summarizeResponse(response) {
    const result = response && typeof response === 'object' ? response : {};
    const toolResults = Array.isArray(result.tool_results) ? result.tool_results : [];
    const statuses = toolResults.map(normalizedToolStatus);
    const topLevelStatus = typeof result.status === 'string' ? result.status : '';
    const awaiting = statuses.includes('awaiting_confirmation')
      || (result.success === null && topLevelStatus === 'awaiting_confirmation');
    const denied = statuses.includes('denied') || topLevelStatus === 'denied';
    const failed = result.success === false
      || failureStatuses.has(topLevelStatus)
      || toolResults.some((item) => item && item.success === false)
      || statuses.some((status) => !['completed', 'awaiting_confirmation'].includes(status));
    const completed = statuses.includes('completed')
      || (result.success === true && topLevelStatus === 'completed');
    const label = awaiting
      ? '● Awaiting confirmation'
      : denied
        ? '● Denied'
        : failed
          ? '● Review result'
          : '● Replied';
    const reply = typeof result.reply === 'string' && result.reply.trim()
      ? result.reply
      : awaiting
        ? 'This operation is waiting for your confirmation.'
        : denied
          ? 'The requested operation was denied.'
          : failed
            ? 'The Core operation did not complete; no success is reported.'
            : 'Core returned an empty reply.';
    return {
      completed,
      denied,
      failed,
      label,
      reply,
      statuses,
      toolResults,
      awaiting,
    };
  }

  function create() {
    let epoch = 0;
    let nextTurnNumber = 0;
    const turns = new Map();

    function isCurrent(turn) {
      return Boolean(
        turn
        && turns.get(turn.id) === turn
        && turn.epoch === epoch,
      );
    }

    function begin(userMessage) {
      const turn = {
        id: `turn-${++nextTurnNumber}`,
        epoch,
        userMessage,
        assistant: {
          label: '● Thinking',
          status: 'pending',
          text: 'Thinking…',
        },
        confirmationInFlight: false,
        confirmationPending: false,
        settled: false,
      };
      turns.set(turn.id, turn);
      return turn;
    }

    function beginConfirmation(turn, decision) {
      if (!isCurrent(turn) || !turn.confirmationPending || turn.confirmationInFlight) return false;
      turn.confirmationInFlight = true;
      turn.confirmationDecision = decision;
      return true;
    }

    function applyResponse(turn, response) {
      if (!isCurrent(turn)) return { accepted: false };
      const summary = summarizeResponse(response);
      turn.assistant = {
        label: summary.label,
        status: summary.awaiting
          ? 'awaiting_confirmation'
          : summary.denied
            ? 'denied'
            : summary.failed
              ? 'failed'
              : summary.completed
                ? 'completed'
                : 'replied',
        text: summary.reply,
      };
      turn.confirmationPending = summary.awaiting;
      turn.confirmationInFlight = false;
      turn.settled = !summary.awaiting;
      return { accepted: true, ...summary };
    }

    function applyFailure(turn, text, { preserveConfirmation = false } = {}) {
      if (!isCurrent(turn)) return { accepted: false };
      const keepPending = preserveConfirmation && turn.confirmationPending;
      turn.assistant = {
        label: '● Review result',
        status: 'failed',
        text,
      };
      turn.confirmationPending = keepPending;
      turn.confirmationInFlight = false;
      turn.settled = !keepPending;
      return { accepted: true, preserveConfirmation: keepPending };
    }

    function applyCancellation(turn, text = 'This response was cancelled for a newer message.') {
      if (!isCurrent(turn)) return { accepted: false };
      turn.assistant = {
        label: '● Cancelled',
        status: 'cancelled',
        text,
      };
      turn.confirmationPending = false;
      turn.confirmationInFlight = false;
      turn.settled = true;
      return { accepted: true };
    }

    function newConversation() {
      epoch += 1;
      turns.clear();
      return epoch;
    }

    function restore(records) {
      newConversation();
      nextTurnNumber = 0;
      if (!Array.isArray(records)) return [];
      const terminalRecords = records.filter((record) => {
        if (!record || typeof record !== 'object') return false;
        if (record.status === 'awaiting_confirmation') return false;
        const toolResults = Array.isArray(record.tool_results) ? record.tool_results : [];
        return !toolResults.some((toolResult) => normalizedToolStatus(toolResult) === 'awaiting_confirmation');
      });
      return terminalRecords.map((record) => {
        nextTurnNumber += 1;
        const turn = {
          id: typeof record?.id === 'string' && record.id.trim()
            ? record.id.trim()
            : `turn-${nextTurnNumber}`,
          epoch,
          userMessage: record?.user || '',
          assistant: {
            label: record?.status === 'denied'
              ? '● Denied'
              : record?.status === 'failed'
                ? '● Review result'
                : '● Replied',
            status: record?.status === 'denied'
              ? 'denied'
              : record?.status === 'failed'
                ? 'failed'
                : 'completed',
            text: record?.assistant || '',
          },
          confirmationInFlight: false,
          confirmationPending: false,
          settled: true,
          restored: true,
          record,
        };
        turns.set(turn.id, turn);
        return turn;
      });
    }

    return {
      applyCancellation,
      applyFailure,
      applyResponse,
      begin,
      beginConfirmation,
      hasPendingConfirmation: () => [...turns.values()].some((turn) => turn.confirmationPending),
      isCurrent,
      list: () => [...turns.values()],
      newConversation,
      restore,
      summarizeResponse,
      normalizedToolStatus,
    };
  }

  return { create, normalizedToolStatus, summarizeResponse };
});
