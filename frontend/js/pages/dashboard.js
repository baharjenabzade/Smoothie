import { api } from "../api.js";
import { h, formatBand, formatDate, plural, emptyState, chip } from "../ui.js";
import { CRITERIA, PART_LABELS, criterionBars, trendChart } from "../components.js";

export async function render(root, ctx) {
  const d = await api.dashboard();

  root.append(h("div", { class: "page-head" }, h("h1", {}, "Dashboard"), h("p", { class: "lede" }, "Your progress across every answer you have submitted.")));

  if (d.total_answers === 0) {
    root.append(
      emptyState("No answers yet", "Answer one question and your band, trend and recurring mistakes will appear here.", h("a", { class: "btn btn-primary", href: "#/practice" }, "Start practising")),
    );
    return;
  }

  root.append(
    h(
      "dl",
      { class: "stats" },
      h("div", {}, h("dt", {}, "Average band"), h("dd", {}, formatBand(d.average_band))),
      h("div", {}, h("dt", {}, "Best band"), h("dd", {}, formatBand(d.best_band))),
      h("div", {}, h("dt", {}, "Latest band"), h("dd", {}, formatBand(d.latest_band))),
      h("div", {}, h("dt", {}, "Answers"), h("dd", {}, String(d.total_answers))),
      h("div", {}, h("dt", {}, "Words saved"), h("dd", {}, String(d.vocabulary_count))),
    ),
  );

  root.append(h("section", { class: "section" }, h("div", { class: "section-head" }, h("h2", {}, "Band over time"), h("span", { class: "muted small" }, `Last ${plural(d.trend.length, "answer", "answers")}`)), trendChart(d.trend, ctx.user.target_band)));

  const weakestLabel = (CRITERIA.find(([k]) => k === d.weakest_criterion) || [])[1];
  root.append(
    h(
      "section",
      { class: "section" },
      h(
        "div",
        { class: "cols" },
        h(
          "div",
          {},
          h("h2", { style: "margin-bottom:14px" }, "Where marks are lost"),
          criterionBars(d.criterion_averages, d.weakest_criterion),
          weakestLabel ? h("p", { class: "muted small" }, `Your lowest criterion so far is ${weakestLabel.toLowerCase()}.`) : null,
        ),
        h(
          "div",
          {},
          h("h2", { style: "margin-bottom:14px" }, "Mistakes that keep coming back"),
          d.top_grammar_categories.length
            ? h(
                "ul",
                { class: "rows" },
                d.top_grammar_categories.map((c) =>
                  h("li", {}, h("div", { class: "row-main" }, h("span", { class: "row-title" }, c.category), chip(plural(c.count, "time", "times"), "chip-red")), c.examples[0] ? h("p", { class: "example" }, `“${c.examples[0].original}” → “${c.examples[0].corrected}”`) : null),
                ),
              )
            : h("p", { class: "muted" }, "No recurring grammar categories yet."),
          h("a", { href: "#/insights" }, "See all insights"),
        ),
      ),
    ),
  );

  root.append(
    h(
      "section",
      { class: "section" },
      h("div", { class: "section-head" }, h("h2", {}, "Recent sessions"), h("a", { href: "#/history" }, "All sessions")),
      h(
        "ul",
        { class: "rows" },
        d.recent_sessions.map((sess) =>
          h(
            "li",
            {},
            h(
              "div",
              { class: "row-main" },
              h("div", {}, h("div", { class: "row-title" }, h("a", { href: `#/history/${sess.id}` }, `${PART_LABELS[sess.part]}${sess.topic ? `: ${sess.topic}` : ""}`)), h("div", { class: "row-meta muted small" }, formatDate(sess.created_at), chip(plural(sess.answer_count, "answer", "answers")))),
              h("span", { class: "band", style: "font-size:1.5rem" }, formatBand(sess.average_band)),
            ),
          ),
        ),
      ),
    ),
  );
}
