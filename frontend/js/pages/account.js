import { api } from "../api.js";
import { h, toast, errorBox, withBusy } from "../ui.js";

export async function render(root, ctx) {
  const user = ctx.user;
  const name = h("input", { id: "acc-name", type: "text", maxlength: 120 });
  name.value = user.full_name || "";
  const bands = [];
  for (let b = 4; b <= 9; b += 0.5) bands.push(b);
  const band = h("select", { id: "acc-band" }, bands.map((b) => h("option", { value: b, selected: b === Number(user.target_band) }, b.toFixed(1))));
  const save = h("button", { class: "btn btn-primary", type: "submit" }, "Save changes");
  const errorHost = h("div", {});

  const form = h(
    "form",
    { style: "max-width:420px" },
    h("div", { class: "field" }, h("label", { for: "acc-email" }, "Email"), h("input", { id: "acc-email", type: "email", value: user.email, disabled: true })),
    h("div", { class: "field" }, h("label", { for: "acc-name" }, "Name"), name),
    h("div", { class: "field" }, h("label", { for: "acc-band" }, "Target band"), band, h("div", { class: "hint" }, "Sample answers and the practice plan are pitched at this level.")),
    errorHost,
    h("div", { class: "btn-row" }, save),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorHost.replaceChildren();
    await withBusy(save, "Saving…", async () => {
      try {
        ctx.user = await api.updateMe({ full_name: name.value.trim() || null, target_band: Number(band.value) });
        ctx.userChanged();
        toast("Changes saved.", "success");
      } catch (err) {
        errorHost.replaceChildren(errorBox(err));
      }
    });
  });

  root.append(h("div", { class: "page-head" }, h("h1", {}, "Account")), form);
}
