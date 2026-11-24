import { api, setToken } from "../api.js";
import { h, errorBox, withBusy, brandMark } from "../ui.js";

const BAND_OPTIONS = [];
for (let b = 4; b <= 9; b += 0.5) BAND_OPTIONS.push(b);

export function renderAuth(app, ctx, initialMode = "login") {
  let mode = initialMode;
  const formHost = h("div", {});
  const tabs = h("div", { class: "seg", role: "group", "aria-label": "Account" });

  function drawTabs() {
    tabs.replaceChildren(
      h("button", { type: "button", "aria-pressed": String(mode === "login"), onclick: () => setMode("login") }, "Log in"),
      h("button", { type: "button", "aria-pressed": String(mode === "register"), onclick: () => setMode("register") }, "Create account"),
    );
  }

  function setMode(next) {
    mode = next;
    drawTabs();
    drawForm();
  }

  function drawForm() {
    const isRegister = mode === "register";
    const errorHost = h("div", {});
    const email = h("input", { id: "email", type: "email", required: true, autocomplete: "email" });
    const password = h("input", { id: "password", type: "password", required: true, minlength: isRegister ? 8 : null, autocomplete: isRegister ? "new-password" : "current-password" });
    const name = h("input", { id: "name", type: "text", autocomplete: "name", maxlength: 120 });
    const band = h("select", { id: "band" }, BAND_OPTIONS.map((b) => h("option", { value: b, selected: b === 7 }, b.toFixed(1))));
    const submit = h("button", { class: "btn btn-primary", type: "submit" }, isRegister ? "Create account" : "Log in");

    const form = h(
      "form",
      { novalidate: true },
      isRegister ? h("div", { class: "field" }, h("label", { for: "name" }, "Name (optional)"), name) : null,
      h("div", { class: "field" }, h("label", { for: "email" }, "Email"), email),
      h("div", { class: "field" }, h("label", { for: "password" }, "Password"), password, isRegister ? h("div", { class: "hint" }, "At least 8 characters.") : null),
      isRegister
        ? h("div", { class: "field" }, h("label", { for: "band" }, "Target band"), band, h("div", { class: "hint" }, "Sample answers and advice are pitched at this level. You can change it later."))
        : null,
      errorHost,
      h("div", { class: "btn-row", style: "margin-top:12px" }, submit),
    );

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorHost.replaceChildren();
      if (!email.value.trim() || !password.value) {
        errorHost.append(errorBox(new Error("Enter your email and password.")));
        return;
      }
      await withBusy(submit, isRegister ? "Creating account…" : "Logging in…", async () => {
        try {
          if (isRegister) {
            await api.register({
              email: email.value.trim(),
              password: password.value,
              full_name: name.value.trim() || null,
              target_band: Number(band.value),
            });
          }
          const { access_token } = await api.login(email.value.trim(), password.value);
          setToken(access_token);
          ctx.user = null;
          window.location.hash = "#/dashboard";
        } catch (err) {
          errorHost.replaceChildren(errorBox(err));
        }
      });
    });
    formHost.replaceChildren(form);
  }

  app.replaceChildren(
    h(
      "div",
      { class: "auth" },
      h(
        "div",
        { class: "pitch" },
        h("a", { class: "brand", href: "../" }, h("span", { class: "brand-mark" }, brandMark(30)), "Smoothies"),
        h("h1", {}, "Practise speaking. See exactly what to fix."),
        h("p", {}, "Answer questions from all three parts of the test, then get your answer back marked: each grammar slip struck through with the correction beside it."),
        h("ul", {}, h("li", {}, "Scores for fluency and coherence, vocabulary, and grammar"), h("li", {}, "A vocabulary notebook built from your own answers"), h("li", {}, "A record of the mistakes that keep coming back")),
        h("p", { class: "small", style: "margin-top:14px" }, "Bands are estimates from the text of your answer. Pronunciation is not assessed yet."),
      ),
      h("div", { class: "auth-form" }, tabs, formHost),
    ),
  );
  drawTabs();
  drawForm();
}
