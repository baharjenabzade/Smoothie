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

//** Line chart of overall bands, oldest first. Plain SVG, no library. */
export function trendChart(points, target) {
  const W = 680;
  const H = 240;
  const pad = { l: 36, r: 22, t: 22, b: 32 };
  const bands = points.map((p) => p.overall_band);
  let lo = Math.floor(Math.min(...bands, target ?? 9) - 1);
  let hi = Math.ceil(Math.max(...bands, target ?? 0) + 0.5);
  lo = Math.max(0, Math.min(lo, 4));
  hi = Math.min(9, Math.max(hi, lo + 3));

  const x = (i) =>
    pad.l + (points.length === 1 ? (W - pad.l - pad.r) / 2 : (i * (W - pad.l - pad.r)) / (points.length - 1));
  const y = (v) => pad.t + ((hi - v) / (hi - lo)) * (H - pad.t - pad.b);

  const coords = points.map((p, i) => ({
    ...p,
    cx: x(i),
    cy: y(p.overall_band),
    dateStr: new Date(p.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
  }));

  const buildSmoothPath = (pts) => {
    let d = `M ${pts[0].cx} ${pts[0].cy}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p1 = pts[i + 1];
      const midX = (p0.cx + p1.cx) / 2;
      d += ` C ${midX} ${p0.cy}, ${midX} ${p1.cy}, ${p1.cx} ${p1.cy}`;
    }
    return d;
  };

  const uid = Math.random().toString(36).slice(2, 7);
  const lineGradId = `trend-line-grad-${uid}`;
  const areaGradId = `trend-area-grad-${uid}`;

  const svg = s("svg", {
    class: "chart trend-svg",
    viewBox: `0 0 ${W} ${H}`,
    role: "img",
    "aria-label": `Overall band for your last ${points.length} answers`,
  });

  // Gradients
  svg.append(
    s(
      "defs",
      {},
      s(
        "linearGradient",
        { id: lineGradId, x1: "0%", y1: "0%", x2: "100%", y2: "0%" },
        s("stop", { offset: "0%", "stop-color": "#c4b5fd" }),
        s("stop", { offset: "55%", "stop-color": "#f472b6" }),
        s("stop", { offset: "100%", "stop-color": "#ff6b57" }),
      ),
      s(
        "linearGradient",
        { id: areaGradId, x1: "0%", y1: "0%", x2: "0%", y2: "100%" },
        s("stop", { offset: "0%", "stop-color": "#ff6b57", "stop-opacity": "0.24" }),
        s("stop", { offset: "65%", "stop-color": "#8b5cf6", "stop-opacity": "0.07" }),
        s("stop", { offset: "100%", "stop-color": "#1f1247", "stop-opacity": "0" }),
      ),
    ),
  );

  // Horizontal grid + Y-axis labels
  for (let v = lo; v <= hi; v++) {
    svg.append(s("line", { class: "grid-line", x1: pad.l, x2: W - pad.r, y1: y(v), y2: y(v) }));
    svg.append(s("text", { class: "axis-label", x: pad.l - 10, y: y(v) + 4, "text-anchor": "end" }, String(v)));
  }

  // Target dashed line + frosted pill badge on the right
  if (target && target >= lo && target <= hi) {
    const ty = y(target);
    const pillW = 78;
    svg.append(s("line", { class: "trend-target", x1: pad.l, x2: W - pad.r, y1: ty, y2: ty }));
    svg.append(
      s(
        "g",
        { class: "target-pill", transform: `translate(${W - pad.r - pillW}, ${ty - 24})` },
        s("rect", { width: pillW, height: 20, rx: 10 }),
        s("text", { x: pillW / 2, y: 13.5, "text-anchor": "middle" }, `Target ${formatBand(target)}`),
      ),
    );
  }

  // Smooth curve + gradient area fill
  if (coords.length > 1) {
    const lineD = buildSmoothPath(coords);
    const baseY = y(lo);
    const areaD = `${lineD} L ${coords[coords.length - 1].cx} ${baseY} L ${coords[0].cx} ${baseY} Z`;
    svg.append(s("path", { class: "trend-area", d: areaD, fill: `url(#${areaGradId})` }));
    svg.append(s("path", { class: "trend-line", d: lineD, stroke: `url(#${lineGradId})` }));
  }

  // Floating glass tooltip
  const tooltip = h("div", { class: "trend-tooltip", "aria-hidden": "true" });

  // Data points + hover events
  coords.forEach((p, i) => {
    const isLast = i === coords.length - 1;
    if (isLast) {
      svg.append(s("circle", { class: "trend-pulse", cx: p.cx, cy: p.cy, r: 6 }));
    }

    const dot = s(
      "circle",
      { class: `trend-dot${isLast ? " latest" : ""}`, cx: p.cx, cy: p.cy, r: isLast ? 6 : 5 },
      s("title", {}, `Band ${formatBand(p.overall_band)}, Part ${p.part}, ${p.dateStr}`),
    );

    dot.addEventListener("mouseenter", () => {
      tooltip.replaceChildren(
        h("div", { class: "trend-tooltip-meta" }, `Part ${p.part} · ${p.dateStr}`),
        h("strong", {}, `Band ${formatBand(p.overall_band)}`),
      );
      tooltip.style.left = `${(p.cx / W) * 100}%`;
      tooltip.style.top = `${(p.cy / H) * 100}%`;
      tooltip.classList.add("visible");
    });

    dot.addEventListener("mouseleave", () => {
      tooltip.classList.remove("visible");
    });

    svg.append(dot);
  });

  // X-axis edge labels
  const firstLabel = coords[0]?.dateStr ?? "Older";
  const lastLabel = coords.length > 1 ? "Latest" : firstLabel;
  svg.append(s("text", { class: "axis-label", x: pad.l, y: H - 6 }, firstLabel));
  if (coords.length > 1) {
    svg.append(s("text", { class: "axis-label", x: W - pad.r, y: H - 6, "text-anchor": "end" }, lastLabel));
  }

  return h("div", { class: "trend-card" }, svg, tooltip);
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

  if (fb.calibration_notes && fb.calibration_notes.length) {
    root.append(h("section", { class: "section" }, h("h3", {}, "Why some scores are capped"), bulletList(fb.calibration_notes)));
  }

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
