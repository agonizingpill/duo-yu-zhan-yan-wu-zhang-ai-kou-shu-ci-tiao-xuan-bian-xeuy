import {api} from '../api.js';
import {field, formValues, h, replace, select} from '../dom.js';
import {languages, stages} from '../labels.js';
import {store} from '../store.js';
import {cueLine} from '../components/cue.js';
import {empty, feedback, noteBoard, withBusy} from '../components/notes.js';
import {rightsBadge, ticket, title} from '../components/ticket.js';

export async function matchingPage() {
  [store.terms, store.scans] = await Promise.all([api.terms(), api.scans()]);
  const messages = feedback();
  const result = h('div', {id: 'scan-proposals'});
  const history = h('div', {className: 'scan-history'});
  const originOptions = store.terms.filter((term) => term.active)
    .map((term) => [term.code, term.code + ' · ' + term.show_cue]);
  const scanForm = h('form', {onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      const scan = await api.enqueue(formValues(scanForm));
      store.selectedScan = scan.id;
      await populate(scan.id, true);
      await refreshHistory();
    });
  }},
    field('原词', select('origin_code', originOptions, 'ZH-WATER')),
    field('目标语种', select('target_language', Object.entries(languages), 'en')),
    h('button', {type: 'submit'}, '定位同义候选'));

  async function refreshHistory() {
    store.scans = await api.scans();
    replace(history, store.scans.length ? store.scans.map((scan) => h('button', {type: 'button', className: 'history-link',
      onClick: (event) => withBusy(event, messages, () => populate(scan.id))},
      h('span', {}, '#' + scan.id + ' · ' + scan.origin_code), ticket(stages[scan.status]))) : empty('登记一次扫描后即可回看。'));
  }

  async function populate(id, wait = false) {
    let scan = await api.inspectScan(id);
    if (wait) {
      replace(result, h('p', {className: 'empty-state'}, '正在构建字符词表并计算候选…'));
      for (let attempt = 0; attempt < 36 && scan.status === 'queued'; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 300));
        scan = await api.inspectScan(id);
      }
    }
    if (scan.status !== 'ready') {
      replace(result, empty(scan.error ?? '后台还在排队。可从扫描笔记打开此记录查看。'));
      return;
    }
    const details = h('div', {className: 'scan-metadata'},
      ticket('降至 ' + scan.dimensions + ' 维', 'ready'), ticket('词表 ' + scan.vocabulary_size),
      ticket('解释方差 ' + (Number(scan.explained_variance) * 100).toFixed(1) + '%'),
      h('small', {title: scan.fingerprint}, '语料 ' + scan.fingerprint.slice(0, 10)));
    replace(result,
      h('div', {className: 'anchor-line'}, cueLine(scan.origin, ticket('原词'))),
      details,
      h('ol', {className: 'ranked-cues'}, scan.pairs.map((pair) => h('li', {},
        h('div', {className: 'rank-heading'},
          h('span', {}, String(pair.rank).padStart(2, '0')), rightsBadge(pair),
          h('strong', {}, Number(pair.similarity).toFixed(3))),
        cueLine({...pair, code: pair.target_code, language: scan.target_language},
          store.session.user.role === 'reviewer' && h('button', {type: 'button', className: 'quiet',
            onClick: () => {
              store.pairSuggestion = {origin_code: scan.origin_code, target_code: pair.target_code, scan_id: scan.id};
              location.hash = 'pairing';
            }}, '去批注')),
        h('meter', {min: -1, max: 1, value: pair.similarity, 'aria-label': '余弦相似度'})))));
  }

  await refreshHistory();
  const latest = store.selectedScan ?? store.scans[0]?.id;
  if (latest) await populate(latest);
  else replace(result, empty('从左侧选一条原词开始。审核员可从结果直接打开映射批注。'));

  return h('div', {}, title('第二幕 · 字符索引', '相似候选', '字符片段和桥接关键词提供相似表达，选择时请同时核对口述语义与来源许可。'),
    messages.host,
    h('div', {className: 'cue-workbench'},
      h('aside', {}, store.session.user.role !== 'reader' && noteBoard('扫描设置', scanForm), noteBoard('扫描笔记', history)),
      h('section', {className: 'ranked-notebook'}, h('h2', {}, '候选对照'), result)));
}
