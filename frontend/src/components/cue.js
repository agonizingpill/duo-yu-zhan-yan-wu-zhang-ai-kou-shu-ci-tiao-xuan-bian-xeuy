import {h} from '../dom.js';
import {languages} from '../labels.js';
import {ticket} from './ticket.js';

export function cueLine({code, show_cue, spoken_text, language, source_code}, trailing) {
  return h('article', {className: 'cue-line'},
    h('div', {className: 'cue-index'}, code, language && ticket(languages[language])),
    h('div', {className: 'cue-reading'},
      h('small', {}, show_cue ?? ''), h('p', {}, spoken_text), source_code && h('small', {}, source_code)),
    trailing);
}
