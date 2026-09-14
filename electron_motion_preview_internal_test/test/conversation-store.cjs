const test = require('node:test');
const assert = require('node:assert/strict');

const { create, normalizedToolStatus } = require('../renderer/conversation-store.js');

test('independent turns retain success, failure, and long user content', () => {
  const store = create();
  const longMessage = 'long message '.repeat(900);
  const first = store.begin('first request');
  const second = store.begin(longMessage);
  const third = store.begin('third request');

  assert.notEqual(first.id, second.id);
  assert.notEqual(second.id, third.id);
  assert.equal(second.userMessage, longMessage);
  assert.equal(first.assistant.text, 'Thinking…');
  assert.equal(store.list().length, 3);

  const firstOutcome = store.applyResponse(first, {
    reply: 'first result',
    tool_results: [{ success: true, status: 'completed', result: 'ok' }],
  });
  const secondFailure = store.applyFailure(second, 'Core request failed [CORE_TIMEOUT].');

  assert.equal(firstOutcome.accepted, true);
  assert.equal(firstOutcome.completed, true);
  assert.equal(first.assistant.status, 'completed');
  assert.equal(secondFailure.accepted, true);
  assert.equal(second.assistant.status, 'failed');
  assert.equal(third.assistant.status, 'pending');
  assert.equal(first.assistant.text, 'first result');
});

test('awaiting confirmation is not completion and duplicate decisions are ignored', () => {
  const store = create();
  const turn = store.begin('sleep the computer');
  const pending = store.applyResponse(turn, {
    reply: 'Confirmation required.',
    tool_results: [{
      success: null,
      status: 'awaiting_confirmation',
      action: 'sleep_computer',
    }],
  });

  assert.equal(pending.awaiting, true);
  assert.equal(pending.completed, false);
  assert.equal(turn.settled, false);
  assert.equal(turn.confirmationPending, true);
  assert.equal(store.hasPendingConfirmation(), true);
  assert.equal(store.beginConfirmation(turn, 'yes'), true);
  assert.equal(store.beginConfirmation(turn, 'yes'), false);
});

test('approved-after-failure succeeds on the same turn and clears pending state', () => {
  const store = create();
  const turn = store.begin('approve the operation');
  store.applyResponse(turn, {
    tool_results: [{ success: null, status: 'awaiting_confirmation' }],
  });
  assert.equal(store.beginConfirmation(turn, 'yes'), true);

  const transportFailure = store.applyFailure(turn, 'Core request failed [CORE_NETWORK_ERROR].', {
    preserveConfirmation: true,
  });
  assert.equal(transportFailure.preserveConfirmation, true);
  assert.equal(turn.confirmationPending, true);
  assert.equal(turn.confirmationInFlight, false);
  assert.equal(store.beginConfirmation(turn, 'yes'), true);

  const approved = store.applyResponse(turn, {
    reply: 'Operation completed.',
    tool_results: [{ success: true, status: 'completed', result: 'done' }],
  });
  assert.equal(approved.completed, true);
  assert.equal(approved.awaiting, false);
  assert.equal(turn.confirmationPending, false);
  assert.equal(turn.settled, true);
  assert.equal(store.hasPendingConfirmation(), false);
});

test('denial remains owned by its turn and unknown results cannot become success', () => {
  const store = create();
  const deniedTurn = store.begin('deny the operation');
  const otherTurn = store.begin('other request');
  store.applyResponse(deniedTurn, {
    tool_results: [{ success: null, status: 'awaiting_confirmation' }],
  });
  assert.equal(store.beginConfirmation(deniedTurn, 'no'), true);

  const denied = store.applyResponse(deniedTurn, {
    reply: 'Cancelled.',
    tool_results: [{ success: false, status: 'denied', error: 'User denied the requested action.' }],
  });
  const unknown = store.applyResponse(otherTurn, {
    tool_results: [{ success: false, status: 'failed', error: "Tool 'missing' is not available." }],
  });

  assert.equal(denied.denied, true);
  assert.equal(denied.failed, true);
  assert.equal(deniedTurn.assistant.status, 'denied');
  assert.equal(deniedTurn.confirmationPending, false);
  assert.equal(unknown.completed, false);
  assert.equal(unknown.failed, true);
  assert.equal(otherTurn.assistant.status, 'failed');
});

test('denied result without a reply still gives the assistant a visible denial message', () => {
  const store = create();
  const turn = store.begin('deny the operation');
  const denied = store.applyResponse(turn, {
    tool_results: [{ success: false, status: 'denied' }],
  });

  assert.equal(denied.denied, true);
  assert.equal(denied.reply, 'The requested operation was denied.');
  assert.equal(turn.assistant.text, 'The requested operation was denied.');
});

test('new conversation invalidates stale responses and does not mix turns', () => {
  const store = create();
  const stale = store.begin('old request');
  store.newConversation();
  const fresh = store.begin('new request');

  const staleOutcome = store.applyResponse(stale, {
    reply: 'late old response',
    tool_results: [{ success: true, status: 'completed' }],
  });

  assert.equal(staleOutcome.accepted, false);
  assert.equal(store.list().length, 1);
  assert.equal(store.list()[0], fresh);
  assert.equal(fresh.assistant.status, 'pending');
});

test('a superseded streaming turn becomes explicitly cancelled', () => {
  const store = create();
  const turn = store.begin('old request');
  const outcome = store.applyCancellation(turn);

  assert.equal(outcome.accepted, true);
  assert.equal(turn.assistant.status, 'cancelled');
  assert.equal(turn.assistant.label, '● Cancelled');
  assert.equal(turn.settled, true);
  assert.equal(store.hasPendingConfirmation(), false);
});

test('status normalization keeps only explicit completed results successful', () => {
  assert.equal(normalizedToolStatus({ success: true, status: 'completed' }), 'completed');
  assert.equal(normalizedToolStatus({ success: null, status: 'awaiting_confirmation' }), 'awaiting_confirmation');
  assert.equal(normalizedToolStatus({ success: true, status: 'running' }), 'running');
  assert.equal(normalizedToolStatus({ success: false, status: 'failed' }), 'failed');
  assert.equal(normalizedToolStatus({ tool_name: 'missing' }), 'failed');

  const store = create();
  const nonTerminal = store.begin('do not claim running is complete');
  const outcome = store.applyResponse(nonTerminal, {
    tool_results: [{ success: true, status: 'running' }],
  });
  assert.equal(outcome.completed, false);
  assert.equal(outcome.failed, true);
});

test('restore rebuilds terminal turns and never restores a pending confirmation', () => {
  const store = create();
  const restored = store.restore([
    {
      id: 'turn-persisted-1',
      user: 'read the report',
      assistant: 'The report is ready.',
      status: 'completed',
      tool_results: [{ success: true, status: 'completed' }],
    },
    {
      id: 'turn-persisted-2',
      user: 'shutdown the computer',
      assistant: 'The action was denied.',
      status: 'denied',
      tool_results: [{ success: false, status: 'denied' }],
    },
    {
      id: 'turn-persisted-pending',
      user: 'should not be persisted',
      assistant: 'Confirm?',
      status: 'awaiting_confirmation',
      tool_results: [{ success: null, status: 'awaiting_confirmation' }],
    },
  ]);

  assert.equal(restored.length, 2);
  assert.equal(store.list().length, 2);
  assert.equal(store.hasPendingConfirmation(), false);
  assert.equal(store.list()[0].assistant.status, 'completed');
  assert.equal(store.list()[1].assistant.status, 'denied');
  assert.equal(store.list()[0].restored, true);
});
