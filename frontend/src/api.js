import {authenticate, store} from './store.js';

export class ServiceError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : detail?.message || '暂时无法加载，请重试');
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, method = 'GET', data) {
  const headers = {};
  if (store.session) headers.Authorization = 'Bearer ' + store.session.token;
  if (data != null) headers['Content-Type'] = 'application/json';
  const response = await fetch('/api' + path, {
    method, headers, body: data != null ? JSON.stringify(data) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401 && path !== '/auth/login') {
      authenticate(null);
      location.hash = 'login';
    }
    throw new ServiceError(response.status, error.detail);
  }
  return response;
}

const json = async (...args) => (await request(...args)).json();
const encoded = encodeURIComponent;

export const api = {
  login: (form) => json('/auth/login', 'POST', form),
  sources: () => json('/catalogue/sources'),
  terms: () => json('/catalogue/terms'),
  addSource: (form) => json('/catalogue/sources', 'POST', form),
  addTerm: (form) => json('/catalogue/terms', 'POST', form),
  revoke: (code) => json('/catalogue/sources/' + encoded(code) + '/revoke', 'POST'),
  scans: () => json('/matching/scans'),
  inspectScan: (id) => json('/matching/scans/' + encoded(id)),
  enqueue: (form) => json('/matching/scans', 'POST', form),
  pairs: () => json('/matching/pairs'),
  approve: (form) => json('/matching/pairs', 'POST', form),
  editions: () => json('/glossaries'),
  openEdition: (form) => json('/glossaries', 'POST', form),
  edition: (code) => json('/glossaries/' + encoded(code)),
  arrange: (code, origin_codes) => json('/glossaries/' + encoded(code) + '/order', 'PUT', {origin_codes}),
  publish: (code) => json('/glossaries/' + encoded(code) + '/publish', 'POST'),
  exportEdition: async (code) => (await request('/glossaries/' + encoded(code) + '/export')).blob(),
};
