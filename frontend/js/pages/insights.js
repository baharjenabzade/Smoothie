import { api } from "../api.js";
import { h, setChildren, toast, spinner, errorBox, withBusy, plural, emptyState, chip } from "../ui.js";
import { CRITERIA, GRAMMAR_CATEGORIES, criterionBars } from "../components.js";

const PAGE = 20;

export async function render(root, ctx) {
  const report = await api.weaknesses();
  root.append(h("div", { class: "page-head" }, h("h1", {}, "Insights"), h("p", { class: "lede" }, "What your evaluated answers say about where to focus.")));

  if (report.evaluations_analyzed === 0) {
    root.append(emptyState("Nothing to analyse yet", "Insights are built from your evaluated answers. Submit one and come back.", h("a", { class: "btn btn-primary", href: "#/practice" }, "Start practising")));
    return;
  }

  const weakest = (CRITERIA.find(([k]) => k === report.weakest_criterion) || [])[1];
  root.append(
    h(
      "section",
      { class: "section" },
      h("h2", { style: "margin-bottom:6px" }, "Average by criterion"),
      h("p", { class: "muted small" }, `Based on ${plural(report.evaluations_analyzed, "evaluated answer", "evaluated answers")}.${weakest ? ` Lowest: ${weakest.toLowerCase()}.` : ""}`),
      criterionBars(report.criterion_averages, report.weakest_criterion),
    ),
  );

  // ---- practice plan ----
  const planHost = h("div", {});
  const planBtn = h("button", { class: "btn btn-primary", type: "button" }, "Create my practice plan");
  planBtn.addEventListener("click", () =>
    withBusy(planBtn, "Writing your plan…", async () => {
      planHost.replaceChildren(spinner("The local model is building a plan from your results. This can take a minute."));
      try {
        const r = await api.recommendations();
        setChildren(
          planHost,
          h("p", { style: "margin-top:14px; max-width:68ch" }, r.summary),
          r.focus_areas.map((f) =>
            h(
              "div",
              { class: "criterion" },
              h("h3", { style: "margin-bottom:4px" }, f.area),
              h("p", { class: "muted" }, f.why_it_matters),
              f.exercises.map((ex) =>
                h("div", { style: "margin:12px 0 0" }, h("h4", {}, ex.title), h("p", { style: "margin:2px 0 6px" }, ex.instructions), ex.practice_items.length ? h("ol", {}, ex.practice_items.map((i) => h("li", {}, i))) : null),
              ),
            ),
          ),
          r.weekly_routine.length ? h("div", { class: "criterion" }, h("h3", { style: "margin-bottom:6px" }, "This week"), h("ul", {}, r.weekly_routine.map((l) => h("li", {}, l)))) : null,
        );
      } catch (err) {
        planHost.replaceChildren(errorBox(err));
      }
    }),
  );
  root.append(h("section", { class: "section" }, h("h2", { style: "margin-bottom:6px" }, "Practice plan"), h("p", { class: "muted" }, "Exercises and a weekly routine, based on your weakest criterion and your most frequent mistakes."), planBtn, planHost));

  // ---- recurring grammar ----
  if (report.top_grammar_categories.length) {
    root.append(
      h(
        "section",
        { class: "section" },
        h("h2", { style: "margin-bottom:14px" }, "Mistakes that keep coming back"),
        h(
          "ul",
          { class: "rows" },
          report.top_grammar_categories.map((c) =>
            h(
              "li",
              {},
              h("div", { class: "row-main" }, h("span", { class: "row-title" }, c.category), chip(plural(c.count, "time", "times"), "chip-red")),
              c.examples.map((e) => h("p", { class: "example" }, `“${e.original}” → “${e.corrected}”`)),
            ),
          ),
        ),
      ),
    );
  }

  // ---- full grammar log ----
  const catSel = h("select", { id: "g-cat" }, h("option", { value: "" }, "All categories"), GRAMMAR_CATEGORIES.map((c) => h("option", { value: c }, c)));
  const list = h("div", {});
  const moreHost = h("div", {});
  let offset = 0;

  async function load(reset) {
    if (reset) {
      offset = 0;
      list.replaceChildren();
    }
    const items = await api.grammarIssues({ category: catSel.value, limit: PAGE, offset });
    offset += items.length;
    for (const g of items) {
      list.append(h("div", { class: "issue" }, h("div", { class: "pair" }, h("del", {}, g.original), " ", h("ins", {}, g.corrected), " ", chip(g.category, "chip-blue")), h("p", { class: "muted", style: "margin:4px 0 0" }, g.explanation)));
    }
    if (!list.children.length) list.append(h("p", { class: "muted" }, "No corrections in this category."));
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
  catSel.addEventListener("change", () => load(true).catch((err) => list.replaceChildren(errorBox(err))));
  root.append(
    h("section", { class: "section" }, h("h2", { style: "margin-bottom:14px" }, "Every correction"), h("div", { class: "field", style: "max-width:300px" }, h("label", { for: "g-cat" }, "Category"), catSel), list, moreHost),
  );
  await load(true);
}
