export function h(tag, props = {}, ...contents) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value == null || value === false) continue;
    if (key.startsWith('on')) node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === 'className') node.className = value;
    else if (['checked', 'disabled', 'required', 'selected'].includes(key)) node[key] = value;
    else node.setAttribute(key, value);
  }
  for (const child of contents.flat(Infinity)) {
    if (child == null || child === false) continue;
    node.append(child);
  }
  return node;
}

export function replace(inHost, ...contents) {
  inHost.replaceChildren(...contents.flat(Infinity).filter(Boolean));
}

export function field(label, ...controls) {
  return h('label', { className: 'field' }, h('span', {}, label), controls);
}

export function select(name, rows, value) {
  const node = h('select', {name, required: true},
    rows.map(([key, label]) => h('option', {value: key, selected: key === value}, label)));
  if (value) node.value = value;
  return node;
}

export function formValues(form) {
  return Object.fromEntries(new FormData(form));
}
