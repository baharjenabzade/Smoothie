import { api } from "../api.js";
import { h, toast, spinner, errorBox, withBusy, debounce, emptyState, chip } from "../ui.js";
import { vocabCard } from "../components.js";

const PAGE = 20;
const TYPES = ["word", "collocation", "idiom", "phrasal verb", "expression"];
const SOURCES = [
  ["answer", "From my answers"],
  ["suggestion", "Suggested upgrades"],
  ["topic", "Topic lists"],
];

export async function render(root, ctx) {
  root.append(h("div", { class: "page-head" }, h("h1", {}, "Vocabulary"), h("p", { class: "lede" }, "Words and phrases collected from your answers, plus topic lists you generate.")));

  // ---- notebook ----
  const search = h("input", { id: "v-q", type: "text", placeholder: "Search terms", maxlength: 100 });
  const typeSel = h("select", { id: "v-type" }, h("option", { value: "" }, "All types"), TYPES.map((t) => h("option", { value: t }, t)));
  const srcSel = h("select", { id: "v-src" }, h("option", { value: "" }, "All sources"), SOURCES.map(([v, l]) => h("option", { value: v }, l)));
  const list = h("ul", { class: "rows" });
  const moreHost = h("div", {});
  const emptyHost = h("div", {});
  let offset = 0;

  function row(item) {
    const del = h("button", { class: "btn btn-quiet btn-danger", type: "button", "aria-label": `Remove ${item.term}` }, "Remove");
    const li = h(
      "li",
      {},
      h(
        "div",
        { class: "row-main" },
        h("div", {}, h("div", { class: "row-title" }, item.term, " ", chip(item.item_type)), h("p", { style: "margin:2px 0 0" }, item.definition), item.example ? h("p", { class: "example" }, item.example) : null, h("div", { class: "row-meta" }, item.topic ? chip(item.topic) : null, item.times_seen > 1 ? chip(`Seen ${item.times_seen} times`, "chip-blue") : null, item.source === "suggestion" ? chip("Suggested", "chip-green") : null)),
        del,
      ),
    );
    del.addEventListener("click", async () => {
      del.disabled = true;
      try {
        await api.deleteVocabulary(item.id);
        li.remove();
        toast("Removed from your notebook.", "success");
      } catch (err) {
        toast(err.message, "error");
        del.disabled = false;
      }
    });
    return li;
  }

  async function load(reset) {
    if (reset) {
      offset = 0;
      list.replaceChildren();
    }
    const items = await api.vocabulary({ q: search.value.trim(), item_type: typeSel.value, source: srcSel.value, limit: PAGE, offset });
    offset += items.length;
    items.forEach((it) => list.append(row(it)));
    emptyHost.replaceChildren();
    if (!list.children.length) {
      const filtered = search.value || typeSel.value || srcSel.value;
      emptyHost.append(
        filtered
          ? emptyState("Nothing matches those filters", "Clear the search or choose a different type.")
          : emptyState("Your notebook is empty", "Useful words and suggested upgrades are saved here after each evaluated answer.", h("a", { class: "btn btn-primary", href: "#/practice" }, "Practise now")),
      );
    }
    moreHost.replaceChildren();
    if (items.length === PAGE) {
      const more = h("button", { class: "btn", type: "button" }, "Show more");
      more.addEventListener("click", () =>
        withBusy(more, "Loading…", async () => {
          try {
            await load(false);
          } catch (err) {
            toast(err.message, "error");
          }
        }),
      );
      moreHost.append(more);
    }
  }
  const reload = () => load(true).catch((err) => emptyHost.replaceChildren(errorBox(err)));
  search.addEventListener("input", debounce(reload, 300));
  typeSel.addEventListener("change", reload);
  srcSel.addEventListener("change", reload);

  // ---- topic word lists ----
  const topicInput = h("input", { id: "tv-topic", type: "text", maxlength: 100, placeholder: "e.g. Technology" });
  const countSel = h("select", { id: "tv-count" }, [8, 10, 15].map((n) => h("option", { value: n, selected: n === 10 }, String(n))));
  const saveBox = h("input", { id: "tv-save", type: "checkbox" });
  const genBtn = h("button", { class: "btn btn-primary", type: "button" }, "Generate word list");
  const genResult = h("div", {});
  genBtn.addEventListener("click", () => {
    const topic = topicInput.value.trim();
    if (!topic) {
      toast("Enter a topic first.", "error");
      topicInput.focus();
      return;
    }
    return withBusy(genBtn, "Generating…", async () => {
      genResult.replaceChildren(spinner("The local model is writing your word list. This can take a minute."));
      try {
        const r = await api.topicVocabulary({ topic, count: Number(countSel.value), save: saveBox.checked });
        genResult.replaceChildren(
          h("p", { class: "muted", style: "margin-top:14px" }, r.saved ? `${r.saved} items saved to your notebook.` : "Not saved. Tick “Save to my notebook” before generating to keep a list."),
          h("div", { class: "vocab-grid" }, r.items.map(vocabCard)),
        );
        if (r.saved) reload();
      } catch (err) {
        genResult.replaceChildren(errorBox(err));
      }
    });
  });

  root.append(
    h(
      "section",
      { class: "section" },
      h("h2", { style: "margin-bottom:14px" }, "Topic word lists"),
      h(
        "div",
        { class: "inline-fields" },
        h("div", { class: "field", style: "min-width:220px" }, h("label", { for: "tv-topic" }, "Topic"), topicInput),
        h("div", { class: "field" }, h("label", { for: "tv-count" }, "Items"), countSel),
        h("label", { class: "check", for: "tv-save", style: "padding-bottom:8px" }, saveBox, "Save to my notebook"),
        genBtn,
      ),
      genResult,
    ),
    h(
      "section",
      { class: "section" },
      h("h2", { style: "margin-bottom:14px" }, "My notebook"),
      h("div", { class: "inline-fields", style: "margin-bottom:10px" }, h("div", { class: "field", style: "min-width:200px" }, h("label", { for: "v-q" }, "Search"), search), h("div", { class: "field" }, h("label", { for: "v-type" }, "Type"), typeSel), h("div", { class: "field" }, h("label", { for: "v-src" }, "Source"), srcSel)),
      list,
      emptyHost,
      moreHost,
    ),
  );
  await load(true);
}
