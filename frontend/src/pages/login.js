import {api} from '../api.js';
import {field, formValues, h} from '../dom.js';
import {authenticate} from '../store.js';
import {feedback, withBusy} from '../components/notes.js';

export function loginPage() {
  const messages = feedback();
  const form = h('form', {className: 'login-form', onSubmit: (event) => {
    event.preventDefault();
    withBusy(event, messages, async () => {
      authenticate(await api.login(formValues(form)));
      location.hash = 'catalogue';
    });
  }},
    h('h2', {}, '进入工作席'),
    field('账号', h('input', {name: 'username', autocomplete: 'username', placeholder: 'editor', required: true})),
    field('密码', h('input', {name: 'password', type: 'password', autocomplete: 'current-password', required: true})),
    h('button', {type: 'submit'}, '登录'), messages.host,
    h('small', {}, '演示身份 editor / reviewer / reader，使用 StageDesk2026!'));
  return h('main', {className: 'login-sheet'},
    h('section', {className: 'cover-copy'},
      h('div', {className: 'mark'}, '浮桥'),
      h('p', {className: 'eyebrow'}, '浮桥无障碍演出协作组'),
      h('h1', {}, '口述词页'),
      h('p', {className: 'cover-annotation'}, '从剧本走台到译词定稿。把现场口述和回放用句的许可核对留在同一份词单里。'),
      h('div', {className: 'cue-stamp'},
        h('span', {}, '灯下潮汐'), h('span', {}, 'A01 · 水幕起'))),
    form);
}
