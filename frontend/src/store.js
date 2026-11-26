const sessionKey = 'floatbridge-access-clerk';

function readSession() {
  try {
    return JSON.parse(sessionStorage.getItem(sessionKey) ?? 'null');
  } catch {
    return null;
  }
}

export const store = {
  session: readSession(),
  sources: [],
  terms: [],
  scans: [],
  pairs: [],
  editions: [],
  selectedScan: null,
  pairSuggestion: null,
  editionCode: 'FB-WINTER',
};

export function authenticate(session) {
  store.session = session;
  if (session) sessionStorage.setItem(sessionKey, JSON.stringify(session));
  else sessionStorage.removeItem(sessionKey);
}

export function sourceTerm(code) {
  return store.terms.find((term) => term.code === code);
}
