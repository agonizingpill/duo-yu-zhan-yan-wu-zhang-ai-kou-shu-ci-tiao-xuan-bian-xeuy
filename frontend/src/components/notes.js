import {h, replace} from '../dom.js';

export function noteBoard(title, ...contents) {
  return h('section', {className: 'noteboard'}, h('h2', {}, title), contents);
}

export function feedback() {
  const host = h('div', {className: 'feedback', role: 'status', 'aria-live': 'polite'});
  return {
    host,
    clear: () => replace(host),
    success: (message) => replace(host, h('p', {className: 'success'}, message)),
    error: (error) => replace(host, h('p', {className: 'problem'}, error.message),
      ...((error.detail?.fields ?? []).map((field) => h('small', {}, field.field + ' · ' + field.message)))),
  };
}

export function empty(instructions) {
  return h('p', {className: 'empty-state'}, instructions);
}

export async function withBusy(event, messages, work) {
  const button = event.submitter ?? event.currentTarget;
  button.disabled = true;
  messages.clear();
  try {
    await work();
  } catch (error) {
    messages.error(error);
  } finally {
    button.disabled = false;
  }
}
