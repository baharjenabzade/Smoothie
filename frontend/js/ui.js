// Small DOM helpers. Everything is built with createElement/textContent, never innerHTML,
// because answers and AI feedback are untrusted text.

const SVG_NS = "http://www.w3.org/2000/svg";

function appendChildren(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

function applyProps(node, props) {
  for (const [key, value] of Object.entries(props || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.setAttribute("class", value);
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, String(value));
  }
}

/** h("div", {class: "x"}, "text", childNode) */
export function h(tag, props, ...children) {
  const node = document.createElement(tag);
  applyProps(node, props);
  appendChildren(node, children);
  return node;
}

/** Same as h() but for SVG elements. */
export function s(tag, props, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  applyProps(node, props);
  appendChildren(node, children);
  return node;
}

/** Replace a node's children. Unlike node.replaceChildren(), accepts arrays and skips null/false. */
export function setChildren(node, ...children) {
  node.replaceChildren();
  appendChildren(node, children);
}

/** The Smoothies cup-and-straw mark. */
export function brandMark(size = 26) {
  return s(
    "svg",
    { viewBox: "0 0 24 24", width: size, height: size, "aria-hidden": "true" },
    s("path", { d: "M5 8h14l-1.6 12.2a1.4 1.4 0 0 1-1.4 1.2H8a1.4 1.4 0 0 1-1.4-1.2z", fill: "#f6665c" }),
    s("rect", { x: 4, y: 6, width: 16, height: 3.4, rx: 1.7, fill: "#fff1dc" }),
    s("path", { d: "M13.5 6l2.6-4", stroke: "#fff1dc", "stroke-width": 2, "stroke-linecap": "round", fill: "none" }),
  );
}

export function toast(message, kind = "info", ms = 5000) {
  const host = document.getElementById("toasts");
  if (!host) return;
  const node = h("div", { class: `toast ${kind}` }, message);
  host.append(node);
  setTimeout(() => node.remove(), ms);
}

export function formatDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function formatBand(value) {
  return value === null || value === undefined ? "–" : Number(value).toFixed(1);
}

export function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

export function countWords(text) {
  return (text.match(/[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g) || []).length;
}

export function debounce(fn, ms = 300) {
  let handle;
  return (...args) => {
    clearTimeout(handle);
    handle = setTimeout(() => fn(...args), ms);
  };
}

export function spinner(label = "Loading…") {
  return h("div", { class: "loading" }, h("span", { class: "spinner", "aria-hidden": "true" }), label);
}

export function errorBox(err) {
  const message = err && err.message ? err.message : String(err);
  return h("div", { class: "callout error", role: "alert" }, h("strong", {}, "Something went wrong. "), message);
}

export function emptyState(title, text, ...actions) {
  return h("div", { class: "empty" }, h("h3", {}, title), h("p", {}, text), actions.length ? h("div", { class: "btn-row" }, actions) : null);
}

export function chip(text, kind = "") {
  return h("span", { class: `chip ${kind}`.trim() }, text);
}

/** Disable a button and show a label while an async action runs. */
export async function withBusy(button, label, fn) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try {
    return await fn();
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}
