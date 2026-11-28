import { api } from "../api.js";
import { h, setChildren, toast, spinner, errorBox, withBusy, chip, emptyState, plural, debounce } from "../ui.js";
import { banner, icon } from "../art.js";
import { parseQuestions } from "../importer.js";

const BANDS = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9];
const fullText = (q) => `${q.text}${q.cue_points && q.cue_points.length ? ` You should say: ${q.cue_points.join("; ")}.` : ""}`.slice(0, 1000);

function sampleView(r, band) {
  return h(
    "div",
    { class: "adapt" },
    h("p", { class: "muted small" }, `Sample answer at band ${Number(band).toFixed(1)}`),
    h("p", { class: "improved" }, r.sample_answer),
    r.key_features.length ? h("ul", { style: "margin-top:10px" }, r.key_features.map((f) => h("li", {}, f))) : null,
  );
}

// ------------------------------------------------------------------ My groups

async function groupsTab(host, ctx, go) {
  let groups = await api.groups();
  const topics = await api.topics().catch(() => []);
  const list = h("div", { class: "story-grid" });
  const formHost = h("div", {});
  const detailHost = h("div", {});

  async function reload() {
    groups = await api.groups();
    draw();
  }

  function draw() {
    if (!groups.length) {
      setChildren(list, emptyState("No groups yet", "Group the topics you want to practise together, like “Travel and places” or “Work week”. Then practise them and generate sample answers for the whole group.", h("button", { class: "btn btn-primary", type: "button", onclick: () => openForm() }, "Create a group")));
      return;
    }
    setChildren(
      list,
      groups.map((g) =>
        h(
          "article",
          { class: "story-card" },
          h("h3", {}, g.name),
          h("div", { class: "row-meta" }, g.topics.slice(0, 6).map((t) => chip(t)), g.topics.length > 6 ? chip(`+${g.topics.length - 6}`) : null, g.question_ids.length ? chip(plural(g.question_ids.length, "extra question", "extra questions"), "chip-accent") : null),
          h("div", { class: "btn-row" }, h("button", { class: "btn btn-primary btn-small", type: "button", onclick: () => openGroup(g) }, "Open"), h("span", { class: "muted small" }, plural(g.question_count, "question", "questions"))),
        ),
      ),
    );
  }

  function openForm(existing) {
    const name = h("input", { id: "g-name", type: "text", maxlength: 100, placeholder: "e.g. Travel and places" });
    const filter = h("input", { id: "g-filter", type: "text", placeholder: "Filter topics", "aria-label": "Filter topics" });
    const picked = new Set(existing ? existing.topics : []);
    const grid = h("div", { class: "cluster-pick" });
    const drawTopics = () => {
      const q = filter.value.trim().toLowerCase();
      setChildren(
        grid,
        topics
          .filter((t) => !q || t.topic.toLowerCase().includes(q))
          .map((t) => {
            const cb = h("input", { type: "checkbox", id: `gt-${t.topic}`, checked: picked.has(t.topic) });
            cb.addEventListener("change", () => (cb.checked ? picked.add(t.topic) : picked.delete(t.topic)));
            return h("label", { class: "check", for: `gt-${t.topic}` }, cb, `${t.topic} `, h("span", { class: "muted small" }, `(${t.question_count})`));
          }),
      );
    };
    filter.addEventListener("input", debounce(drawTopics, 150));
    if (existing) name.value = existing.name;
    drawTopics();
    const save = h("button", { class: "btn btn-primary", type: "button" }, existing ? "Save changes" : "Create group");
    save.addEventListener("click", () =>
      withBusy(save, "Saving…", async () => {
        const body = { name: name.value.trim(), topics: [...picked], question_ids: existing ? existing.question_ids : [] };
        try {
          const saved = existing ? await api.updateGroup(existing.id, body) : await api.createGroup(body);
          formHost.replaceChildren();
          toast("Group saved.", "success");
          await reload();
          openGroup(saved);
        } catch (err) {
          toast(err.message, "error");
        }
      }),
    );
    setChildren(
      formHost,
      h(
        "section",
        { class: "section" },
        h("h2", { style: "margin-bottom:14px" }, existing ? "Edit group" : "New group"),
        h("div", { class: "field" }, h("label", { for: "g-name" }, "Group name"), name),
        h("div", { class: "field" }, h("label", { for: "g-filter" }, "Choose topics"), filter),
        grid,
        topics.length ? null : h("p", { class: "muted" }, "No topics found yet. Seed or import questions first."),
        h("div", { class: "btn-row", style: "margin-top:14px" }, save, h("button", { class: "btn btn-quiet", type: "button", onclick: () => formHost.replaceChildren() }, "Cancel")),
      ),
    );
    formHost.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function openGroup(g) {
    let part = 0;
    const qHost = h("div", {});
    const results = new Map();
    const bandSel = h("select", { id: "gb", "aria-label": "Band" }, BANDS.map((b) => h("option", { value: b, selected: b === Math.round(ctx.user.target_band * 2) / 2 }, b.toFixed(1))));
    const countSel = h("select", { id: "gc", "aria-label": "How many" }, [3, 5, 8].map((n) => h("option", { value: n }, String(n))));
    const genAll = h("button", { class: "btn btn-primary btn-small", type: "button" }, "Generate sample answers");
    const status = h("p", { class: "muted small", role: "status" });
    let current = g;
    let questions = [];

    const del = h("button", { class: "btn btn-quiet btn-danger btn-small", type: "button" }, "Delete group");
    del.addEventListener("click", async () => {
      if (!window.confirm(`Delete the group “${g.name}”? Your questions stay in the bank.`)) return;
      try {
        await api.deleteGroup(g.id);
        detailHost.replaceChildren();
        await reload();
      } catch (err) {
        toast(err.message, "error");
      }
    });

    async function sampleFor(q, button) {
      const out = qHost.querySelector(`[data-q="${q.id}"]`);
      const band = Number(bandSel.value);
      out.replaceChildren(spinner("Writing…"));
      try {
        const r = await api.sampleAnswer({ part: q.part, question_text: fullText(q), target_band: band });
        results.set(q.id, r);
        out.replaceChildren(sampleView(r, band));
      } catch (err) {
        out.replaceChildren(errorBox(err));
        throw err;
      } finally {
        if (button) button.disabled = false;
      }
    }

    function drawQuestions() {
      const shown = questions.filter((q) => !part || q.part === part);
      if (!shown.length) {
        setChildren(qHost, h("p", { class: "muted" }, "No questions in this part yet."));
        return;
      }
      setChildren(
        qHost,
        h(
          "ul",
          { class: "rows" },
          shown.map((q) => {
            const sampleBtn = h("button", { class: "btn btn-small", type: "button" }, "Sample answer");
            sampleBtn.addEventListener("click", () => withBusy(sampleBtn, "Writing…", () => sampleFor(q).catch(() => {})));
            const practise = h("button", { class: "btn btn-primary btn-small", type: "button", onclick: () => { ctx.pending = { question: q }; ctx.go("#/practice"); } }, "Practise");
            const removable = current.question_ids.includes(q.id);
            const remove = removable
              ? h("button", { class: "btn btn-quiet btn-small", type: "button", onclick: async () => { try { current = await api.updateGroup(g.id, { name: current.name, topics: current.topics, question_ids: current.question_ids.filter((i) => i !== q.id) }); await refresh(); await reload(); } catch (err) { toast(err.message, "error"); } } }, "Remove")
              : null;
            const saved = results.get(q.id);
            return h("li", {}, h("div", { class: "row-main" }, h("div", {}, h("div", { class: "row-title" }, q.text), h("div", { class: "row-meta" }, chip(`Part ${q.part}`), chip(q.topic))), h("div", { class: "btn-row" }, sampleBtn, practise, remove)), h("div", { "data-q": q.id }, saved ? sampleView(saved, bandSel.value) : null));
          }),
        ),
      );
    }

    async function refresh() {
      const d = await api.group(g.id);
      questions = d.questions;
      current = { ...current, question_ids: d.question_ids, topics: d.topics, name: d.name, question_count: d.question_count };
      drawQuestions();
    }

    genAll.addEventListener("click", async () => {
      const todo = questions.filter((q) => (!part || q.part === part) && !results.has(q.id)).slice(0, Number(countSel.value));
      if (!todo.length) {
        toast("Every question shown already has a sample answer.", "info");
        return;
      }
      genAll.disabled = true;
      let done = 0;
      for (const q of todo) {
        status.textContent = `Writing answer ${done + 1} of ${todo.length}…`;
        try {
          await sampleFor(q);
        } catch (err) {
          status.textContent = `Stopped after ${done} of ${todo.length}: ${err.message}`;
          genAll.disabled = false;
          return;
        }
        done++;
      }
      status.textContent = `Wrote ${plural(done, "sample answer", "sample answers")}. Use them as models, then practise in your own words.`;
      genAll.disabled = false;
    });

    const seg = h("div", { class: "seg", role: "group", "aria-label": "Part" });
    const drawSeg = () => setChildren(seg, [[0, "All"], [1, "Part 1"], [2, "Part 2"], [3, "Part 3"]].map(([n, l]) => h("button", { type: "button", "aria-pressed": String(part === n), onclick: () => { part = n; drawSeg(); drawQuestions(); } }, l)));
    drawSeg();

    setChildren(
      detailHost,
      h(
        "section",
        { class: "section" },
        h("div", { class: "section-head" }, h("h2", {}, g.name), h("div", { class: "btn-row" }, h("button", { class: "btn btn-small", type: "button", onclick: () => openForm(current) }, "Edit"), del)),
        h("div", { class: "row-meta" }, g.topics.map((t) => chip(t))),
        h("div", { class: "inline-fields", style: "margin:14px 0" }, seg, h("div", { class: "field" }, h("label", { for: "gb" }, "Sample band"), bandSel), h("div", { class: "field" }, h("label", { for: "gc" }, "How many"), countSel), genAll),
        status,
        qHost,
      ),
    );
    qHost.replaceChildren(spinner());
    detailHost.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      await refresh();
    } catch (err) {
      qHost.replaceChildren(errorBox(err));
    }
  }

  draw();
  host.append(h("div", { class: "btn-row", style: "margin-bottom:16px" }, h("button", { class: "btn btn-primary", type: "button", onclick: () => openForm() }, "New group")), formHost, list, detailHost);
}

// ------------------------------------------------------------------ Import

function importTab(host, ctx, go) {
  const text = h("textarea", { id: "imp-text", rows: 12, placeholder: "Paste questions here, one per line.\n\nPart 1\nTopic: Hometown\n1. Where is your hometown?\n\nPart 2\nDescribe a place you like.\nYou should say:\n- where it is\n- why you like it" });
  const file = h("input", { id: "imp-file", type: "file", accept: ".txt,.csv,.json,.md,text/plain,text/csv,application/json" });
  const partSel = h("select", { id: "imp-part" }, [["0", "Detect from headings"], ["1", "All Part 1"], ["2", "All Part 2"], ["3", "All Part 3"]].map(([v, l]) => h("option", { value: v }, l)));
  const topic = h("input", { id: "imp-topic", type: "text", maxlength: 100, value: "Imported" });
  const auto = h("input", { id: "imp-auto", type: "checkbox", checked: true });
  const preview = h("div", {});
  const result = h("div", {});
  const previewBtn = h("button", { class: "btn", type: "button" }, "Preview");

  file.addEventListener("change", async () => {
    const f = file.files && file.files[0];
    if (!f) return;
    if (f.size > 2_000_000) {
      toast("That file is too large (2 MB limit).", "error");
      return;
    }
    text.value = await f.text();
    previewBtn.click();
  });

  previewBtn.addEventListener("click", () => {
    result.replaceChildren();
    let parsed;
    try {
      parsed = parseQuestions(text.value, { defaultPart: Number(partSel.value) });
    } catch {
      preview.replaceChildren(h("div", { class: "callout error", role: "alert" }, "That text could not be read as JSON or CSV. Check the format, or paste plain lines."));
      return;
    }
    const { items, assumedPart } = parsed;
    if (!items.length) {
      preview.replaceChildren(h("p", { class: "muted" }, "No questions found. Paste at least one full question."));
      return;
    }
    const byPart = [1, 2, 3].map((p) => items.filter((i) => i.part === p).length);
    const go = h("button", { class: "btn btn-primary", type: "button" }, `Import ${plural(items.length, "question", "questions")}`);
    go.addEventListener("click", () =>
      withBusy(go, "Importing…", async () => {
        const totals = { created: 0, skipped_duplicates: 0, skipped_invalid: 0, topics: {} };
        try {
          for (let i = 0; i < items.length; i += 400) {
            const r = await api.importQuestions({ items: items.slice(i, i + 400), default_topic: topic.value.trim() || "Imported", auto_topic: auto.checked });
            totals.created += r.created;
            totals.skipped_duplicates += r.skipped_duplicates;
            totals.skipped_invalid += r.skipped_invalid;
            for (const [t, n] of Object.entries(r.topics)) totals.topics[t] = (totals.topics[t] || 0) + n;
          }
          preview.replaceChildren();
          setChildren(
            result,
            h("div", { class: "callout info" }, h("strong", {}, `${plural(totals.created, "question", "questions")} added. `), `${totals.skipped_duplicates} already existed, ${totals.skipped_invalid} could not be used.`),
            Object.keys(totals.topics).length ? h("div", { class: "row-meta", style: "margin-top:12px" }, Object.entries(totals.topics).sort((a, b) => b[1] - a[1]).map(([t, n]) => chip(`${t} · ${n}`))) : null,
            h("div", { class: "btn-row", style: "margin-top:14px" }, h("button", { class: "btn btn-primary", type: "button", onclick: () => go_("similar") }, "Group similar questions"), h("a", { class: "btn", href: "#/practice" }, "Practise now")),
          );
        } catch (err) {
          result.replaceChildren(errorBox(err));
        }
      }),
    );
    setChildren(
      preview,
      h("div", { class: "callout info", style: "margin-top:14px" }, h("strong", {}, `Found ${plural(items.length, "question", "questions")}: `), `Part 1 · ${byPart[0]}, Part 2 · ${byPart[1]}, Part 3 · ${byPart[2]}.`, assumedPart ? ` ${assumedPart} had no part heading and were set to Part 1; choose a part above to change that.` : ""),
      h("ul", { class: "rows" }, items.slice(0, 8).map((i) => h("li", {}, h("div", { class: "row-title" }, i.text), h("div", { class: "row-meta" }, chip(`Part ${i.part}`), i.topic ? chip(i.topic) : null, i.cue_points.length ? chip(`${i.cue_points.length} cue points`) : null)))),
      items.length > 8 ? h("p", { class: "muted small" }, `…and ${items.length - 8} more.`) : null,
      h("div", { class: "btn-row" }, go),
    );
  });
  const go_ = go;

  host.append(
    h(
      "section",
      { class: "section" },
      h("h2", { style: "margin-bottom:6px" }, "Import questions"),
      h("p", { class: "muted" }, "Add questions from your own notes, books or apps: paste text, or open a .txt, .csv or .json file. Headings like “Part 2” and “Topic: Hometown” are understood, and cue cards keep their bullet points. Only import material you have the right to use."),
      h("div", { class: "field" }, h("label", { for: "imp-text" }, "Questions"), text),
      h("div", { class: "inline-fields" }, h("div", { class: "field" }, h("label", { for: "imp-file" }, "…or choose a file"), file), h("div", { class: "field" }, h("label", { for: "imp-part" }, "Part"), partSel), h("div", { class: "field" }, h("label", { for: "imp-topic" }, "Topic for questions without one"), topic)),
      h("label", { class: "check", for: "imp-auto", style: "margin:10px 0" }, auto, "Name topics automatically from similar questions"),
      h("div", { class: "btn-row" }, previewBtn),
      preview,
      result,
    ),
    h("p", { class: "muted small" }, "CSV needs a header row with a “question” (or “text”) column and optional “part”, “topic” and “cue_points” (separated by |) columns. JSON can be a list of objects with the same names."),
  );
}

// ------------------------------------------------------------------ Similar questions

function similarTab(host, ctx, go) {
  let part = 1;
  let threshold = 0.4;
  const out = h("div", {});
  const seg = h("div", { class: "seg", role: "group", "aria-label": "Part" });
  const slider = h("input", { id: "sim-th", type: "range", min: "0.3", max: "0.7", step: "0.05", value: String(threshold) });
  const drawSeg = () => setChildren(seg, [1, 2, 3].map((n) => h("button", { type: "button", "aria-pressed": String(n === part), onclick: () => { part = n; drawSeg(); load(); } }, `Part ${n}`)));

  async function load() {
    out.replaceChildren(spinner("Grouping questions…"));
    try {
      const groups = await api.questionGroups({ part, threshold });
      if (!groups.length) {
        out.replaceChildren(emptyState("No similar questions found", "Try a lower similarity, or import more questions first."));
        return;
      }
      setChildren(
        out,
        h("p", { class: "muted small" }, `${plural(groups.length, "group", "groups")} of questions that ask about the same thing. Matching uses shared key words, so check the groups before you rely on them.`),
        groups.map((g) => {
          const save = h("button", { class: "btn btn-small", type: "button" }, "Save as my group");
          save.addEventListener("click", () =>
            withBusy(save, "Saving…", async () => {
              try {
                await api.createGroup({ name: g.label, topics: [], question_ids: g.questions.map((q) => q.id) });
                toast(`Saved “${g.label}” in My groups.`, "success");
              } catch (err) {
                toast(err.message, "error");
              }
            }),
          );
          return h(
            "details",
            { class: "more" },
            h("summary", {}, `${g.label} · ${plural(g.size, "question", "questions")}`),
            h("div", { class: "row-meta" }, g.topics.map((t) => chip(t))),
            h("ul", { class: "rows" }, g.questions.map((q) => h("li", {}, h("div", { class: "row-main" }, h("span", { class: "row-title" }, q.text), h("button", { class: "btn btn-small", type: "button", onclick: () => { ctx.pending = { question: q }; ctx.go("#/practice"); } }, "Practise"))))),
            h("div", { class: "btn-row", style: "margin-top:10px" }, save),
          );
        }),
      );
    } catch (err) {
      out.replaceChildren(errorBox(err));
    }
  }
  slider.addEventListener("change", () => { threshold = Number(slider.value); load(); });
  drawSeg();
  host.append(
    h("section", { class: "section" }, h("h2", { style: "margin-bottom:6px" }, "Similar questions"), h("p", { class: "muted" }, "Questions that ask about the same thing are grouped together so you can practise them in one go."), h("div", { class: "inline-fields" }, seg, h("div", { class: "field" }, h("label", { for: "sim-th" }, "Grouping strictness (looser ← → stricter)"), slider))),
    out,
  );
  load();
}

// ------------------------------------------------------------------ page

export async function render(root, ctx) {
  const tabs = [["groups", "My groups", "book"], ["import", "Import questions", "spark"], ["similar", "Similar questions", "memories"]];
  const body = h("div", {});
  const seg = h("div", { class: "seg", role: "group", "aria-label": "Library" });
  async function show(key) {
    setChildren(seg, tabs.map(([k, label, ic]) => h("button", { type: "button", "aria-pressed": String(k === key), onclick: () => show(k) }, icon(ic, 16), " ", label)));
    body.replaceChildren(spinner());
    const inner = h("div", {});
    try {
      if (key === "groups") await groupsTab(inner, ctx, show);
      else if (key === "import") importTab(inner, ctx, show);
      else similarTab(inner, ctx, show);
      body.replaceChildren(inner);
    } catch (err) {
      body.replaceChildren(errorBox(err));
    }
  }
  root.append(banner({ title: "Library", lede: "Build your own topic groups, import questions from your notes, and group similar ones to practise together.", image: "mascot-speech", compact: true }), h("section", { class: "section tight" }, seg), body);
  await show("groups");
}
