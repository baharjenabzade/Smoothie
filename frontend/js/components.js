import { h, s, formatBand, chip } from "./ui.js";

export const CRITERIA = [
  ["fluency_coherence", "Fluency and coherence"],
  ["lexical_resource", "Lexical resource"],
  ["grammatical_range_accuracy", "Grammatical range and accuracy"],
];

export const GRAMMAR_CATEGORIES = [
  "tense",
  "subject-verb agreement",
  "articles",
  "prepositions",
  "word order",
  "plurals and countability",
  "word form",
  "conditionals",
  "modal verbs",
  "relative clauses",
  "passive voice",
  "comparatives and superlatives",
  "sentence structure",
  "other",
];

export const PART_LABELS = { 1: "Part 1", 2: "Part 2", 3: "Part 3" };

export function bandBar(label, value, { weakest = false } = {}) {
  const pct = value === null || value === undefined ? 0 : Math.max(0, Math.min(100, (value / 9) * 100));
  return h(
    "div",
    { class: `bar-row${weakest ? " weakest" : ""}` },
    h("div", { class: "bar-label" }, h("span", {}, label), h("strong", {}, formatBand(value))),
    h("div", { class: "bar", role: "img", "aria-label": `${label}: ${formatBand(value)} out of 9` }, h("div", { class: "bar-fill", style: `width:${pct}%` })),
  );
}

export function criterionBars(averages, weakestKey) {
  return h("div", {}, CRITERIA.map(([key, label]) => bandBar(label, averages[key], { weakest: key === weakestKey })));
}

export function vocabCard(entry) {
  return h(
    "div",
    { class: "vocab" },
    h("div", {}, h("span", { class: "term" }, entry.term), " ", chip(entry.type)),
    h("p", {}, entry.definition),
    entry.example ? h("p", { class: "example" }, entry.example) : null,
  );
}

/** Line chart of overall bands, oldest first. Plain SVG, no library. */
export function trendChart(points, target) {
  const W = 640;
  const H = 230;
  const pad = { l: 34, r: 16, t: 14, b: 28 };
  const bands = points.map((p) => p.overall_band);
  let lo = Math.floor(Math.min(...bands, target ?? 9) - 1);
  let hi = Math.ceil(Math.max(...bands, target ?? 0) + 0.5);
  lo = Math.max(0, Math.min(lo, 4));
  hi = Math.min(9, Math.max(hi, lo + 3));
  const x = (i) => pad.l + (points.length === 1 ? (W - pad.l - pad.r) / 2 : (i * (W - pad.l - pad.r)) / (points.length - 1));
  const y = (v) => pad.t + ((hi - v) / (hi - lo)) * (H - pad.t - pad.b);

  const svg = s("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `Overall band for your last ${points.length} answers` });
  for (let v = lo; v <= hi; v++) {
    svg.append(s("line", { class: "grid-line", x1: pad.l, x2: W - pad.r, y1: y(v), y2: y(v) }));
    svg.append(s("text", { class: "axis-label", x: pad.l - 8, y: y(v) + 4, "text-anchor": "end" }, String(v)));
  }
  if (target && target >= lo && target <= hi) {
    svg.append(s("line", { class: "trend-target", x1: pad.l, x2: W - pad.r, y1: y(target), y2: y(target) }));
    svg.append(s("text", { class: "target-label", x: pad.l + 6, y: y(target) - 5 }, `Target ${formatBand(target)}`));
  }
  if (points.length > 1) {
    svg.append(s("polyline", { class: "trend-line", points: points.map((p, i) => `${x(i)},${y(p.overall_band)}`).join(" ") }));
  }
  points.forEach((p, i) => {
    const date = new Date(p.created_at).toLocaleDateString(undefined, { dateStyle: "medium" });
    svg.append(
      s("circle", { class: "trend-dot", cx: x(i), cy: y(p.overall_band), r: 5 }, s("title", {}, `Band ${formatBand(p.overall_band)}, Part ${p.part}, ${date}`)),
    );
  });
  svg.append(s("text", { class: "axis-label", x: pad.l, y: H - 6 }, "Older"));
  svg.append(s("text", { class: "axis-label", x: W - pad.r, y: H - 6, "text-anchor": "end" }, "Newer"));
  return svg;
}

/** The learner's answer with each grammar error struck through and the fix beside it. */
export function markedTranscript(text, issues) {
  const lower = text.toLowerCase();
  const spans = [];
  for (const issue of issues) {
    const needle = issue.original.trim().toLowerCase();
    if (!needle) continue;
    const start = lower.indexOf(needle);
    if (start === -1) continue;
    const end = start + needle.length;
    if (spans.some((sp) => start < sp.end && end > sp.start)) continue; // skip overlaps
    spans.push({ start, end, issue });
  }
  spans.sort((a, b) => a.start - b.start);

  const parts = [];
  let pos = 0;
  for (const { start, end, issue } of spans) {
    if (start > pos) parts.push(text.slice(pos, start));
    parts.push(
      h("del", { class: "err" }, text.slice(start, end)),
      " ",
      h("ins", { class: "fix", title: issue.explanation }, issue.corrected),
    );
    pos = end;
  }
  parts.push(text.slice(pos));
  return { node: h("p", { class: "transcript" }, parts), marked: spans.length };
}

function bulletList(items) {
  return items && items.length ? h("ul", {}, items.map((t) => h("li", {}, t))) : h("p", { class: "muted small" }, "Nothing noted.");
}

/** Full feedback for one evaluated answer. */
export function evaluationView(ev, answerText = null) {
  const fb = ev.feedback;
  const root = h("div", { class: "evaluation" });

  root.append(
    h(
      "div",
      { class: "band-hero" },
      h("div", {}, h("span", { class: "band-caption" }, "Provisional band"), h("span", { class: "band band-big" }, formatBand(ev.overall_band))),
      h(
        "dl",
        { class: "mini-scores" },
        h("div", {}, h("dt", {}, "Fluency"), h("dd", {}, formatBand(ev.fluency_score))),
        h("div", {}, h("dt", {}, "Vocabulary"), h("dd", {}, formatBand(ev.lexical_score))),
        h("div", {}, h("dt", {}, "Grammar"), h("dd", {}, formatBand(ev.grammar_score))),
      ),
    ),
  );

  if (answerText) {
    const { node, marked } = markedTranscript(answerText, fb.grammar_issues);
    root.append(
      h(
        "section",
        { class: "section" },
        h("h3", {}, "Your answer, marked"),
        h("div", { class: "script" }, node),
        marked
          ? h("div", { class: "legend" }, h("span", {}, h("del", {}, "Struck through"), " is what you said"), h("span", {}, h("ins", {}, "Green"), " is the suggested fix. Hover for the reason."))
          : h("p", { class: "muted small", style: "margin-top:10px" }, "No clear grammar errors were found in your answer."),
      ),
    );
  }

  root.append(
    h(
      "section",
      { class: "section" },
      h("h3", {}, "How each criterion scored"),
      CRITERIA.map(([key, label]) => {
        const c = fb[key];
        return h(
          "div",
          { class: "criterion" },
          h("div", { class: "criterion-head" }, h("h4", {}, label), h("span", { class: "band" }, formatBand(c.score))),
          h("div", { class: "bar" }, h("div", { class: "bar-fill", style: `width:${(c.score / 9) * 100}%` })),
          h("p", { style: "margin-top:10px" }, c.summary),
          h("div", { class: "pros-cons" }, h("div", {}, h("h4", {}, "What worked"), bulletList(c.strengths)), h("div", {}, h("h4", {}, "What to improve"), bulletList(c.improvements))),
        );
      }),
    ),
  );

  root.append(
    h(
      "section",
      { class: "section" },
      h("div", { class: "cols" }, h("div", {}, h("h3", {}, "Strengths"), bulletList(fb.strengths)), h("div", {}, h("h3", {}, "Focus next"), bulletList(fb.areas_for_improvement))),
    ),
  );

  if (fb.grammar_issues.length) {
    root.append(
      h(
        "section",
        { class: "section" },
        h("h3", {}, "Grammar corrections"),
        fb.grammar_issues.map((g) =>
          h(
            "div",
            { class: "issue" },
            h("div", { class: "pair" }, h("del", {}, g.original), " ", h("ins", {}, g.corrected), " ", chip(g.category, "chip-accent")),
            h("p", { class: "muted", style: "margin:4px 0 0" }, g.explanation),
          ),
        ),
      ),
    );
  }

  if (fb.correct_structures.length) {
    root.append(
      h(
        "section",
        { class: "section" },
        h("h3", {}, "Structures you used well"),
        h("ul", {}, fb.correct_structures.map((c) => h("li", {}, h("strong", {}, c.structure), ": ", h("span", { class: "example" }, `“${c.example}”`)))),
      ),
    );
  }

  if (fb.useful_vocabulary.length || fb.suggested_vocabulary.length) {
    root.append(
      h(
        "section",
        { class: "section" },
        h("h3", {}, "Vocabulary"),
        fb.useful_vocabulary.length ? h("div", {}, h("h4", { style: "margin-bottom:8px" }, "From your answer"), h("div", { class: "vocab-grid" }, fb.useful_vocabulary.map(vocabCard))) : null,
        fb.suggested_vocabulary.length ? h("div", { style: "margin-top:18px" }, h("h4", { style: "margin-bottom:8px" }, "Try adding"), h("div", { class: "vocab-grid" }, fb.suggested_vocabulary.map(vocabCard))) : null,
        h("p", { class: "muted small", style: "margin-top:10px" }, "These are saved to your vocabulary notebook."),
      ),
    );
  }

  root.append(h("section", { class: "section" }, h("h3", {}, "A stronger version"), h("p", { class: "improved" }, fb.improved_answer)));
  root.append(h("p", { class: "muted small" }, ev.disclaimer));
  return root;
}
