import {h, replace} from './dom.js';
import {pageLabels, roles} from './labels.js';
import {authenticate, store} from './store.js';
import {cataloguePage} from './pages/catalogue.js';
import {editionPage} from './pages/edition.js';
import {loginPage} from './pages/login.js';
import {matchingPage} from './pages/matching.js';
import {pairingPage} from './pages/pairing.js';

const app = document.querySelector('#app');
const pages = {catalogue: cataloguePage, matching: matchingPage, pairing: pairingPage, edition: editionPage};
let sequence = 0;

async function draw() {
  const requested = location.hash.slice(1);
  const visit = ++sequence;
  if (!store.session) {
    replace(app, loginPage());
    return;
  }
  const current = Object.hasOwn(pages, requested) ? requested : 'catalogue';
  const user = store.session.user;
  const body = h('main', {id: 'workspace', tabindex: '-1'}, h('p', {role: 'status'}, '正在打开词页…'));
  replace(app,
    h('a', {className: 'skip-link', href: '#workspace', onClick: (event) => {
      event.preventDefault();
      body.focus();
    }}, '跳到工作区'),
    h('header', {className: 'masthead'},
      h('a', {className: 'brand', href: '#catalogue'}, h('span', {className: 'mark'}, '浮桥'), '口述词页'),
      h('nav', {'aria-label': '工作席模块'}, pageLabels.map(([key, label]) => h('a', {
        href: '#' + key, 'aria-current': current === key ? 'page' : null,
      }, label))),
      h('div', {className: 'user-line'}, h('span', {}, user.name + ' · ' + roles[user.role]),
        h('button', {className: 'quiet', type: 'button', onClick: () => {
          authenticate(null);
          location.hash = 'login';
        }}, '退出'))),
    body);
  try {
    const page = await pages[current]();
    if (visit === sequence) {
      replace(body, page);
      window.scrollTo(0, 0);
    }
  } catch (error) {
    if (visit === sequence) replace(body, h('div', {className: 'empty-state', role: 'alert'},
      h('h1', {}, '词页暂时无法打开'), h('p', {}, error.message),
      h('button', {type: 'button', onClick: draw}, '重新加载')));
  }
}

window.addEventListener('hashchange', draw);
draw();
