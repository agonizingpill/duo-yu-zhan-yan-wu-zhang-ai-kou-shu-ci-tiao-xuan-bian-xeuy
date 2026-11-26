import {h} from '../dom.js';

export function ticket(label, variant = 'neutral') {
  return h('span', {className: 'ticket ' + variant}, label);
}

export function rightsBadge(row) {
  if (row.revoked_at) return ticket('已撤销', 'blocked');
  if (row.expires_on < new Date().toISOString().slice(0, 10)) return ticket('已到期', 'blocked');
  return ticket('许可有效', 'ready');
}

export function title(number, heading, detail) {
  return h('header', {className: 'page-title'},
    h('p', {className: 'eyebrow'}, number), h('h1', {}, heading), h('p', {}, detail));
}
