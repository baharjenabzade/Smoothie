import { api, getToken, setToken, onUnauthorized } from "./api.js";
import { h, brandMark, spinner } from "./ui.js";
import { renderAuth } from "./pages/auth.js";
import { render as dashboard } from "./pages/dashboard.js";
import { render as practice } from "./pages/practice.js";
import { render as stories } from "./pages/stories.js";
import { render as library } from "./pages/library.js";
import { render as history } from "./pages/history.js";
import { render as vocabulary } from "./pages/vocabulary.js";
import { render as insights } from "./pages/insights.js";
import { render as account } from "./pages/account.js";

const app = document.getElementById("app");

const NAV = [
  ["dashboard", "Dashboard"],
  ["practice", "Practice"],
  ["stories", "Stories"],
  ["library", "Library"],
  ["history", "History"],
  ["vocabulary", "Vocabulary"],
  ["insights", "Insights"],
];
const PAGES = { dashboard, practice, stories, library, history, vocabulary, insights, account };

const ctx = {
  user: null,
  go(hash) {
    window.location.hash = hash;
  },
  userChanged() {
    renderUserMenu();
  },
};

let shell = null;
let navSeq = 0;

function logout() {
  setToken(null);
  ctx.user = null;
  shell = null;
  window.location.hash = "#/login";
}

onUnauthorized(() => {
  ctx.user = null;
  shell = null;
  window.location.hash = "#/login";
});

function renderUserMenu() {
  if (!shell) return;
  shell.userMenu.replaceChildren(
    h("a", { href: "#/account" }, ctx.user.full_name || ctx.user.email),
    h("span", { class: "muted" }, `Target ${Number(ctx.user.target_band).toFixed(1)}`),
    h("button", { class: "btn btn-small", type: "button", onclick: logout }, "Log out"),
  );
}

function buildShell() {
  const nav = h("nav", { class: "nav", "aria-label": "Main" }, NAV.map(([key, label]) => h("a", { href: `#/${key}`, "data-key": key }, label)));
  const userMenu = h("div", { class: "user-menu" });
  const main = h("main", { class: "page", id: "view", tabindex: "-1" });
  const header = h(
    "header",
    { class: "topbar" },
    h("div", { class: "topbar-inner" }, h("a", { class: "brand", href: "#/dashboard" }, h("span", { class: "brand-mark" }, brandMark(28)), "Smoothies"), nav, userMenu),
  );
  app.replaceChildren(header, main);
  shell = { nav, userMenu, main };
  renderUserMenu();
}

function setActive(key) {
  for (const link of shell.nav.children) {
    if (link.dataset.key === key) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

async function route() {
  const seq = ++navSeq;
  const hash = window.location.hash || "#/dashboard";
  const match = hash.match(/^#\/([a-z]+)(?:\/(\d+))?/);
  const name = match ? match[1] : "dashboard";
  const arg = match && match[2] ? Number(match[2]) : null;

  if (!getToken()) {
    if (name !== "login" && name !== "register") {
      window.location.hash = "#/login";
      return;
    }
    shell = null;
    document.title = "Smoothies";
    renderAuth(app, ctx, name === "register" ? "register" : "login");
    return;
  }
  if (name === "login" || name === "register") {
    window.location.hash = "#/dashboard";
    return;
  }

  if (!ctx.user) {
    app.replaceChildren(h("div", { class: "page" }, spinner("Signing you in…")));
    try {
      ctx.user = await api.me();
    } catch {
      if (seq !== navSeq) return;
      setToken(null);
      window.location.hash = "#/login";
      return;
    }
    if (seq !== navSeq) return;
  }

  if (!shell || !shell.main.isConnected) buildShell();
  const page = PAGES[name];
  if (!page) {
    window.location.hash = "#/dashboard";
    return;
  }
  setActive(name === "account" ? "" : name);
  shell.main.classList.toggle("wide", name === "practice");
  const view = h("div", {});
  shell.main.replaceChildren(view);
  document.title = `${name.charAt(0).toUpperCase()}${name.slice(1)} · Smoothies`;
  window.scrollTo(0, 0);
  view.append(spinner());
  try {
    const content = h("div", {});
    await page(content, ctx, arg);
    if (seq === navSeq) view.replaceChildren(...content.childNodes);
  } catch (err) {
    if (seq === navSeq) view.replaceChildren(h("div", { class: "callout error", role: "alert" }, h("strong", {}, "This page could not load. "), err.message || String(err)));
  }
}

window.addEventListener("hashchange", route);
route();
