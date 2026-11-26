import {api} from '../api.js';
import {field, formValues, h, replace, select} from '../dom.js';
import {channels, languages, stages} from '../labels.js';
import {store} from '../store.js';
import {empty, feedback, noteBoard, withBusy} from '../components/notes.js';
import {ticket, title} from '../components/ticket.js';

function orderEditor(edition, refresh, messages) {
  const candidates = store.terms.filter((term) => term.language !== edition.target_language && term.active);
  const current = edition.cues.map((cue) => cue.origin_code);
  const sorted = [...current, ...candidates.map((term) => term.code).filter((code) => !current.includes(code))];
  const host = h('div', {className: 'order-lines'});
  function redraw() {
    replace(host, sorted.map((code, index) => {
      const term = candidates.find((term) => term.code === code);
      const box = h('input', {name: 'cue', type: 'checkbox', value: code, checked: current.includes(code),
        onChange: () => {
          if (box.checked && !current.includes(code)) current.push(code);
          if (!box.checked) current.splice(current.indexOf(code), 1);
        }});
      return h('div', {className: 'order-control'},
        h('label', {className: 'check'}, box, term?.show_cue ?? code),
        h('button', {type: 'button', className: 'quiet', disabled: index === 0, 'aria-label': code + ' 上移', onClick: () => {
          [sorted[index - 1], sorted[index]] = [sorted[index], sorted[index - 1]];
          redraw();
        }}, '↑'),
        h('button', {type: 'button', className: 'quiet', disabled: index === sorted.length - 1, 'aria-label': code + ' 下移', onClick: () => {
          [sorted[index], sorted[index + 1]] = [sorted[index + 1], sorted[index]];
          redraw();
        }}, '↓'));
    }));
  }
  const form = h('form', {onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      await api.arrange(edition.code, sorted.filter((code) => current.includes(code)));
      await refresh();
      messages.success('走台顺序已保存。');
    });
  }}, host, h('button', {type: 'submit'}, '保存走台顺序'));
  redraw();
  return form;
}

function showBlock(block, role) {
  return h('article', {className: 'block-note'}, h('h3', {}, block.origin_code),
    h('ul', {}, block.reasons.map((reason) => h('li', {}, reason))),
    block.alternatives.length ? h('div', {},
      h('p', {className: 'small'}, '当前授权覆盖此场次的候选'),
      block.alternatives.map((choice) => h('p', {className: 'alternative'},
        h('span', {}, choice.spoken_text), role === 'reviewer' && h('button', {
          type: 'button', className: 'quiet', onClick: () => {
            store.pairSuggestion = {origin_code: block.origin_code, target_code: choice.code, scan_id: choice.scan_id};
            location.hash = 'pairing';
          }}, '批注替代')))) :
      h('p', {className: 'small'}, '可从相似候选生成替代，或联系来源方补齐原稿授权。'));
}

export async function editionPage() {
  [store.editions, store.terms] = await Promise.all([api.editions(), api.terms()]);
  const role = store.session.user.role;
  const messages = feedback();
  const sheet = h('section', {id: 'edition-sheet'});
  const actions = h('aside', {className: 'edition-actions'});
  const selected = store.editionCode || store.editions[0]?.code;
  const versions = select('edition', store.editions.map((item) => [item.code, item.code + ' · ' + item.show_title]), selected);
  versions.addEventListener('change', (event) => {
    store.editionCode = versions.value;
    withBusy(event, messages, refresh);
  });

  async function refresh() {
    if (!versions.value) {
      replace(sheet, empty('新建一份词单以排列演出词条。'));
      return;
    }
    const edition = await api.edition(versions.value);
    replace(sheet,
      h('article', {className: 'reading-sheet'},
        h('header', {},
          h('p', {className: 'eyebrow'}, edition.code + ' / ' + channels[edition.channel]),
          h('h2', {}, edition.show_title), h('p', {}, edition.show_date + ' · ' + languages[edition.target_language]),
          ticket(stages[edition.status], edition.status === 'published' ? 'ready' : 'neutral')),
        edition.cues.length ? h('ol', {className: 'edition-cues'}, edition.cues.map((cue) => h('li', {},
          h('strong', {}, String(cue.position).padStart(2, '0')),
          h('div', {}, h('small', {}, cue.show_cue), h('p', {}, cue.origin_text),
            h('p', {className: 'target-phrase'}, cue.target_text ?? '等待映射'),
            cue.license_snapshot && h('small', {}, cue.license_snapshot))))) : empty('用右侧排列走台顺序。')),
      edition.history.length && noteBoard('批次留痕', edition.history.map((item) =>
        h('p', {className: 'small'}, item.event_time.slice(0, 19).replace('T', ' ') + ' · ' + item.actor + ' · ' +
          ({arrange_cues: '更新走台顺序', publish_edition: '发布词单', open_edition: '创建词单'}[item.operation] ?? item.operation)))));
    const boxes = [];
    if (edition.status === 'draft') {
      if (edition.blocked.length) boxes.push(noteBoard('待解决的权限与映射', edition.blocked.map((block) => showBlock(block, role))));
      else boxes.push(noteBoard('发布检查', edition.cues.length ? ticket('当前许可与映射齐备', 'ready') : empty('先安排词条。')));
      if (role === 'editor') boxes.push(noteBoard('走台顺序', orderEditor(edition, refresh, messages)));
      if (role === 'reviewer') boxes.push(noteBoard('审签词单', h('button', {type: 'button', onClick: (event) =>
        withBusy(event, messages, async () => {
          await api.publish(edition.code);
          await refresh();
          messages.success('版本已冻结，可供口述席下载。');
        })}, '发布本版')));
    } else {
      boxes.push(noteBoard('给口述席',
        h('p', {}, '发布人 ' + edition.published_by),
        h('button', {type: 'button', onClick: (event) => withBusy(event, messages, async () => {
          const url = URL.createObjectURL(await api.exportEdition(edition.code));
          const anchor = h('a', {href: url, download: edition.code + '.csv'});
          anchor.click();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
          messages.success('词单已导出。');
        })}, '下载口述 CSV')));
    }
    replace(actions, boxes);
  }

  const openForm = h('form', {className: 'inline-fields', onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      const edition = await api.openEdition(formValues(openForm));
      store.editions = await api.editions();
      replace(versions, store.editions.map((item) => h('option', {value: item.code}, item.code + ' · ' + item.show_title)));
      versions.value = store.editionCode = edition.code;
      openForm.reset();
      await refresh();
      messages.success('草稿已新建。');
    });
  }},
    field('词单编号', h('input', {name: 'code', required: true})),
    field('演出名称', h('input', {name: 'show_title', required: true})),
    field('演出日期', h('input', {name: 'show_date', type: 'date', required: true})),
    field('目标语种', select('target_language', Object.entries(languages), 'en')),
    field('用途', select('channel', Object.entries(channels), 'headset')),
    h('button', {type: 'submit'}, '新建词单'));

  await refresh();
  return h('div', {}, title('第四幕 · 提词单', '演出词单', '依走台顺序排句，按演出日和复用渠道检查许可。发布后进行版本留档。'),
    h('div', {className: 'edition-toolbar'}, field('当前版本', versions),
      role === 'editor' && h('details', {className: 'noteboard'}, h('summary', {}, '新建演出词单'), openForm)),
    messages.host,
    h('div', {className: 'three-four'}, sheet, actions));
}
