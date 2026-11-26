import {api} from '../api.js';
import {field, formValues, h, replace, select} from '../dom.js';
import {languages} from '../labels.js';
import {sourceTerm, store} from '../store.js';
import {cueLine} from '../components/cue.js';
import {empty, feedback, noteBoard, withBusy} from '../components/notes.js';
import {rightsBadge, ticket, title} from '../components/ticket.js';

export async function pairingPage() {
  [store.terms, store.pairs] = await Promise.all([api.terms(), api.pairs()]);
  const hint = store.pairSuggestion;
  const messages = feedback();
  const lines = h('div', {id: 'mappings-list'});
  const preview = h('div', {className: 'pair-preview'});
  const options = store.terms.map((row) => [row.code, row.code + ' · ' + row.show_cue]);
  const originals = select('origin_code', options, hint?.origin_code ?? 'ZH-WATER');
  const translations = select('target_code', options, hint?.target_code ?? 'EN-WATER');
  let scanId = hint?.scan_id ?? null;
  function inspect() {
    replace(preview, [originals.value, translations.value].map((code) => {
      const term = sourceTerm(code);
      return term && cueLine(term, rightsBadge(term));
    }));
  }

  for (const control of [originals, translations]) {
    control.addEventListener('change', () => {
      scanId = null;
      inspect();
    });
  }

  const form = h('form', {onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      const pair = await api.approve({...formValues(form), scan_id: scanId});
      store.pairSuggestion = null;
      store.pairs = await api.pairs();
      renderPairs();
      messages.success(pair.origin_code + ' 已映射至 ' + pair.target_code + '。草稿词单随即采用新译。');
    });
  }},
    field('原语词', originals), field('目标语词', translations),
    field('批注依据', h('textarea', {name: 'note', rows: 3, minlength: 2, maxlength: 100, required: true,
      placeholder: '说明口述时长、语义和授权的核验结果'})),
    h('button', {type: 'submit'}, '签审映射'));

  function renderPairs() {
    replace(lines, store.pairs.length ? store.pairs.map((pair) => h('article', {className: 'pair-note'},
      h('div', {className: 'slip-meta'}, h('span', {}, pair.origin_code + ' → ' + pair.target_code), rightsBadge(pair)),
      h('div', {}, h('p', {className: 'source-phrase'}, pair.origin_text),
        h('p', {className: 'target-phrase'}, pair.target_text)),
      h('footer', {}, ticket(languages[pair.target_language]), h('span', {}, pair.note), h('small', {}, '审签 ' + pair.approver)))) :
      empty('从相似候选选一条对应表达，或手工填写原语和目标语。'));
  }
  inspect();
  renderPairs();
  return h('div', {}, title('第三幕 · 逐句签审', '映射批注', '原词在同一目标语种只保留一条生效映射。批准替换后，旧批注留在历史中。'),
    messages.host,
    h('div', {className: 'three-four'}, h('section', {}, h('h2', {}, '已审核映射'), lines),
      h('aside', {}, noteBoard('对照原稿', preview),
        store.session.user.role === 'reviewer' && noteBoard('签审替换', hint && h('p', {className: 'small'}, '来自候选 #' + hint.scan_id), form))));
}
