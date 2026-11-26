import {api} from '../api.js';
import {field, formValues, h, replace, select} from '../dom.js';
import {languages} from '../labels.js';
import {store} from '../store.js';
import {cueLine} from '../components/cue.js';
import {empty, feedback, noteBoard, withBusy} from '../components/notes.js';
import {rightsBadge, ticket, title} from '../components/ticket.js';

function sourceForm(messages, refresh) {
  const form = h('form', {onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      await api.addSource({...formValues(form), allow_recording: form.elements.allow_recording.checked});
      form.reset();
      await refresh();
      messages.success('来源许可已登记。');
    });
  }},
    field('许可编号', h('input', {name: 'code', placeholder: 'SRC-COAST', required: true, pattern: '[A-Z][A-Z0-9\\-]{1,23}'})),
    field('资料题名', h('input', {name: 'title', required: true})),
    field('授权方', h('input', {name: 'owner', required: true})),
    field('授权凭证', h('input', {name: 'document_ref', required: true})),
    field('有效期至', h('input', {name: 'expires_on', type: 'date', required: true})),
    h('label', {className: 'check'}, h('input', {type: 'checkbox', name: 'allow_recording'}), '允许录制回放'),
    h('button', {type: 'submit'}, '登记来源'));
  return form;
}

function termForm(messages, refresh) {
  const sourceBox = h('div', {});
  const form = h('form', {onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      await api.addTerm(formValues(form));
      form.reset();
      await refresh();
      messages.success('口述词条已入库。');
    });
  }},
    field('词条编号', h('input', {name: 'code', required: true, placeholder: 'ZH-NEW'})),
    sourceBox,
    field('语种', select('language', Object.entries(languages), 'zh')),
    field('舞台提示', h('input', {name: 'show_cue', required: true, placeholder: 'B01 · 暮色'})),
    field('实际口述', h('textarea', {name: 'spoken_text', rows: 2, maxlength: 240, required: true})),
    field('桥接关键词', h('input', {name: 'bridge_words', placeholder: 'dusk blue curtains', required: true})),
    h('button', {type: 'submit'}, '保存入库'));
  return {form, refresh: () => replace(sourceBox, field('来源许可',
    select('source_code', store.sources.map((source) => [source.code, source.title]))))};
}

export async function cataloguePage() {
  const messages = feedback();
  const available = h('div', {className: 'source-stack'});
  const lines = h('section', {className: 'script-lines', id: 'term-list'});
  const query = h('input', {type: 'search', placeholder: '检索词条或舞台提示', 'aria-label': '检索词条'});
  const language = select('term-language', [['', '全部语种'], ...Object.entries(languages)]);
  const editor = store.session.user.role === 'editor';

  function filter() {
    const need = query.value.trim().toLowerCase();
    const matches = store.terms.filter((row) =>
      (!language.value || row.language === language.value) &&
      [row.code, row.spoken_text, row.show_cue].some((text) => text.toLowerCase().includes(need)));
    replace(lines, matches.length ? matches.map((row) => cueLine(row, rightsBadge(row))) : empty('调整检索词或语种，查看其他口述词条。'));
  }

  const termEdit = editor ? termForm(messages, refresh) : null;

  async function refresh() {
    [store.sources, store.terms] = await Promise.all([api.sources(), api.terms()]);
    replace(available, store.sources.map((row) => h('article', {className: 'license-slip'},
      h('div', {className: 'slip-meta'}, h('span', {}, row.document_ref), rightsBadge(row)),
      h('h3', {}, row.title),
      h('p', {}, row.owner), h('p', {className: 'small'}, '有效期 ' + row.expires_on + ' · ' + row.term_count + ' 条'),
      h('div', {className: 'tag-row'},
        ticket(row.allow_recording ? '含录制授权' : '仅现场'),
        store.session.user.role === 'reviewer' && !row.revoked_at && h('button', {type: 'button',
          className: 'quiet', onClick: (event) => withBusy(event, messages, async () => {
            await api.revoke(row.code);
            await refresh();
            messages.success('已撤销 ' + row.code);
          })}, '撤销许可')))));
    termEdit?.refresh();
    filter();
  }

  query.addEventListener('input', filter);
  language.addEventListener('change', filter);
  await refresh();
  return h('div', {},
    title('第一幕 · 资料索引', '来源与词库', '登记剧本批注与各语种讲稿。先核对授权，再把可读出的句子摘入词库。'),
    messages.host,
    h('div', {className: 'three-four'},
      h('div', {}, h('div', {className: 'section-heading'}, h('h2', {}, '演出词条'), h('div', {className: 'filters'}, query, language)), lines),
      h('aside', {},
        noteBoard('来源授权凭证', available),
        editor && h('details', {className: 'noteboard'}, h('summary', {}, '登记新的来源'), sourceForm(messages, refresh)),
        editor && h('details', {className: 'noteboard'}, h('summary', {}, '录入口述词条'), termEdit.form))));
}
