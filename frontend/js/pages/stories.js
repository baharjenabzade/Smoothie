import { api } from "../api.js";
import { h, setChildren, toast, spinner, errorBox, withBusy, chip, emptyState, countWords, plural } from "../ui.js";
import { vocabCard } from "../components.js";
import { banner, pic, scene, icon } from "../art.js";
import { LIBRARY } from "../stories-data.js";

const FIT = { strong: ["Strong fit", "chip-green"], partial: ["Partial fit", "chip-accent"], weak: ["Weak fit", "chip-red"] };
const list = (items) => (items && items.length ? h("ul", {}, items.map((i) => h("li", {}, i))) : null);

function adaptView(r) {
  const [label, kind] = FIT[r.fit] || FIT.partial;
  return h(
    "div",
    { class: "adapt" },
    h("div", { class: "row-meta", style: "margin:0 0 8px" }, chip(label, kind)),
    h("p", {}, h("strong", {}, "Angle: "), r.angle),
    h("p", { class: "improved" }, `“${r.opening_line}”`),
    h("div", { class: "cols" }, h("div", {}, h("h4", {}, "Give more time to"), list(r.emphasise)), h("div", {}, h("h4", {}, "Change or drop"), list(r.details_to_change))),
    r.cue_point_plan.length ? h("div", { style: "margin-top:14px" }, h("h4", { style: "margin-bottom:6px" }, "Cue card plan"), h("ul", { class: "rows" }, r.cue_point_plan.map((c) => h("li", {}, h("div", {}, h("span", { class: "row-title" }, c.cue_point), h("p", { style: "margin:2px 0 0" }, c.what_to_say)))))) : null,
    r.useful_collocations.length ? h("div", { class: "vocab-grid", style: "margin-top:14px" }, r.useful_collocations.map(vocabCard)) : null,
    r.watch_out.length ? h("div", { class: "callout info", style: "margin-top:14px" }, h("strong", {}, "Watch out: "), r.watch_out.join(" ")) : null,
    h("p", { class: "muted small", style: "margin-bottom:0" }, "Use this as a guide, then tell the story in your own words. Memorised scripts score worse than real, flexible answers."),
  );
}

// ---------------------------------------------------------------- My stories (Story Studio)

async function studio(host, ctx) {
  let clusters = [];
  let stories = [];
  const clusterName = (slug) => (clusters.find((c) => c.slug === slug) || {}).name || slug;
  const detail = h("div", {});
  const formHost = h("div", {});
  const grid = h("div", { class: "story-grid" });

  async function reload() {
    stories = await api.stories();
    drawGrid();
  }

  function drawGrid() {
    if (!stories.length) {
      setChildren(grid, h("div", { class: "empty-hero" }, pic("mascot-books", "", "empty-pic-img"), emptyState("Your story bank is empty", "Write one real experience, tag it with topic groups, and see which Part 2 cue cards it can answer.", h("button", { class: "btn btn-primary", type: "button", onclick: () => openForm() }, "Write your first story"))));
      return;
    }
    setChildren(
      grid,
      stories.map((st) =>
        h(
          "article",
          { class: "story-card" },
          h("h3", {}, st.title),
          h("p", { class: "muted clamp" }, st.body),
          h("div", { class: "row-meta" }, st.clusters.map((c) => chip(clusterName(c)))),
          h("div", { class: "btn-row" }, h("button", { class: "btn btn-primary btn-small", type: "button", onclick: () => openStory(st) }, "Open"), h("span", { class: "muted small" }, plural(st.word_count, "word", "words"))),
        ),
      ),
    );
  }

  function openForm(existing) {
    const title = h("input", { id: "st-title", type: "text", maxlength: 200, placeholder: "e.g. Learning graphic design online" });
    const body = h("textarea", { id: "st-body", rows: 7, placeholder: "Write the real experience in your own words: what happened, who was involved, how you felt, what you learned." });
    const picked = new Set(existing ? existing.clusters : []);
    const boxes = h(
      "div",
      { class: "cluster-pick" },
      clusters.map((c) => {
        const cb = h("input", { type: "checkbox", id: `cl-${c.slug}`, checked: picked.has(c.slug) });
        cb.addEventListener("change", () => (cb.checked ? picked.add(c.slug) : picked.delete(c.slug)));
        return h("label", { class: "check", for: `cl-${c.slug}` }, cb, c.name);
      }),
    );
    if (existing) {
      title.value = existing.title;
      body.value = existing.body;
    }
    const counter = h("span", { class: "muted small" }, `${countWords(body.value)} words`);
    body.addEventListener("input", () => (counter.textContent = `${countWords(body.value)} words`));
    const save = h("button", { class: "btn btn-primary", type: "button" }, existing ? "Save changes" : "Save story");
    save.addEventListener("click", () =>
      withBusy(save, "Saving…", async () => {
        const payload = { title: title.value.trim(), body: body.value.trim(), clusters: [...picked] };
        try {
          const saved = existing ? await api.updateStory(existing.id, payload) : await api.createStory(payload);
          formHost.replaceChildren();
          toast("Story saved.", "success");
          await reload();
          openStory(saved);
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
        h("h2", { style: "margin-bottom:14px" }, existing ? "Edit story" : "New story"),
        h("div", { class: "field" }, h("label", { for: "st-title" }, "Title"), title),
        h("div", { class: "field" }, h("label", { for: "st-body" }, "Your story"), body, h("div", { class: "counter" }, counter, h("span", { class: "muted small" }, "At least 15 words; 80 to 200 works well"))),
        h("fieldset", { class: "plain" }, h("legend", {}, "Topic groups this story belongs to (up to 5)"), boxes),
        h("div", { class: "btn-row" }, save, h("button", { class: "btn btn-quiet", type: "button", onclick: () => formHost.replaceChildren() }, "Cancel")),
      ),
    );
    formHost.scrollIntoView({ behavior: "smooth", block: "start" });
    title.focus({ preventScroll: true });
  }

  async function openStory(st) {
    const matchHost = h("div", {}, spinner("Finding cue cards this story can answer…"));
    const del = h("button", { class: "btn btn-quiet btn-danger btn-small", type: "button" }, "Delete");
    del.addEventListener("click", async () => {
      if (!window.confirm(`Delete “${st.title}”?`)) return;
      try {
        await api.deleteStory(st.id);
        detail.replaceChildren();
        toast("Story deleted.", "success");
        await reload();
      } catch (err) {
        toast(err.message, "error");
      }
    });
    setChildren(
      detail,
      h(
        "section",
        { class: "section" },
        h("div", { class: "section-head" }, h("h2", {}, st.title), h("div", { class: "btn-row" }, h("button", { class: "btn btn-small", type: "button", onclick: () => openForm(st) }, "Edit"), del)),
        h("div", { class: "row-meta" }, st.clusters.map((c) => chip(clusterName(c)))),
        h("p", { class: "story-body" }, st.body),
      ),
      h("section", { class: "section" }, h("h2", { style: "margin-bottom:6px" }, "Cue cards this story can answer"), h("p", { class: "muted" }, "Matched by shared topic groups and key words. Adapt the story, then practise it without reading."), matchHost),
    );
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const m = await api.storyMatches(st.id);
      if (!m.matches.length) {
        matchHost.replaceChildren(h("p", { class: "muted" }, "No cue cards match yet. Add more topic groups to this story, or write more detail."));
        return;
      }
      matchHost.replaceChildren(
        h("p", { class: "muted small" }, `${m.matches.length} compatible · ${m.practised_count} practised`),
        h(
          "ul",
          { class: "rows" },
          m.matches.map((x) => {
            const out = h("div", {});
            const adaptBtn = h("button", { class: "btn btn-small", type: "button" }, "Adapt this story");
            adaptBtn.addEventListener("click", () =>
              withBusy(adaptBtn, "Adapting…", async () => {
                out.replaceChildren(spinner("The AI is planning how to adapt your story. This can take up to a minute."));
                try {
                  out.replaceChildren(adaptView(await api.adaptStory(st.id, x.question.id)));
                } catch (err) {
                  out.replaceChildren(errorBox(err));
                }
              }),
            );
            const go = h("button", { class: "btn btn-primary btn-small", type: "button", onclick: () => { ctx.pending = { question: x.question }; ctx.go("#/practice"); } }, "Practise");
            return h("li", {}, h("div", { class: "row-main" }, h("div", {}, h("div", { class: "row-title" }, x.question.text), h("div", { class: "row-meta" }, chip(x.question.topic), x.practised ? chip("Practised", "chip-green") : null)), h("div", { class: "btn-row" }, adaptBtn, go)), out);
          }),
        ),
      );
    } catch (err) {
      matchHost.replaceChildren(errorBox(err));
    }
  }

  try {
    clusters = await api.clusters();
  } catch {
    /* tagging is optional if the list cannot load */
  }
  await reload();
  host.append(
    h("div", { class: "btn-row", style: "margin-bottom:16px" }, h("button", { class: "btn btn-primary", type: "button", onclick: () => openForm() }, "New story")),
    formHost,
    grid,
    detail,
  );
}

// ---------------------------------------------------------------- Listen & learn

const synth = window.speechSynthesis;
const sentences = (text) => text.match(/[^.!?]+[.!?]+/g) || [text];

function readerView(story, back) {
  const parts = sentences(story.text).map((t) => h("span", { class: "sent" }, t.trim() + " "));
  let index = -1;
  let playing = false;
  const rate = h("select", { id: "tts-rate", "aria-label": "Speed" }, [["0.8", "Slow"], ["1", "Normal"], ["1.2", "Fast"]].map(([v, l]) => h("option", { value: v, selected: v === "1" }, l)));
  const playBtn = h("button", { class: "btn btn-primary", type: "button" }, icon("play", 18), " Listen");

  const voice = () => {
    const voices = synth ? synth.getVoices() : [];
    return voices.find((v) => /^en-(GB|US)/i.test(v.lang)) || voices.find((v) => /^en/i.test(v.lang)) || null;
  };
  function mark(i) {
    parts.forEach((p, n) => p.classList.toggle("on", n === i));
  }
  function speak(i) {
    if (!playing || i >= parts.length || !playBtn.isConnected) {
      stop();
      return;
    }
    index = i;
    mark(i);
    const u = new SpeechSynthesisUtterance(parts[i].textContent);
    u.rate = Number(rate.value);
    const v = voice();
    if (v) u.voice = v;
    u.lang = v ? v.lang : "en-GB";
    u.onend = () => speak(i + 1);
    u.onerror = () => stop();
    synth.speak(u);
  }
  function stop() {
    playing = false;
    if (synth) synth.cancel();
    mark(-1);
    playBtn.replaceChildren(icon("play", 18), " Listen");
  }
  playBtn.addEventListener("click", () => {
    if (playing) {
      stop();
      return;
    }
    playing = true;
    playBtn.replaceChildren(icon("stop", 18), " Stop");
    speak(0);
  });
  const stopOnLeave = () => {
    if (!playBtn.isConnected) {
      stop();
      window.removeEventListener("hashchange", stopOnLeave);
    }
  };
  window.addEventListener("hashchange", stopOnLeave);

  return h(
    "article",
    { class: "reader" },
    h("button", { class: "btn btn-quiet btn-small", type: "button", onclick: () => { stop(); back(); } }, "← All stories"),
    h("div", { class: "reader-art" }, scene(story.scene, story.title)),
    h("h2", {}, story.title),
    h("div", { class: "row-meta" }, chip(story.tag), chip(story.level, "chip-accent"), chip(`${story.minutes} min`)),
    synth ? h("div", { class: "inline-fields", style: "margin:14px 0" }, playBtn, h("div", { class: "field" }, h("label", { for: "tts-rate" }, "Speed"), rate)) : h("p", { class: "callout info" }, "Listening needs a browser with text-to-speech. You can still read the story."),
    h("p", { class: "story-body" }, parts),
    h("h3", { style: "margin:18px 0 8px" }, "Useful expressions"),
    h("div", { class: "vocab-grid" }, story.expressions.map(([term, meaning]) => h("div", { class: "vocab" }, h("div", { class: "term" }, term), h("p", {}, meaning)))),
    h("p", { class: "muted small" }, "Audio is read aloud by your device. Try retelling the story in your own words, then use one expression in your next practice answer."),
  );
}

function library(host) {
  const show = () => {
    setChildren(
      host,
      h("p", { class: "muted" }, "Short illustrated stories to read and listen to. Notice the expressions, then reuse them in your own answers."),
      h("div", { class: "lib-grid" }, LIBRARY.map((st) => h("button", { class: "lib-card", type: "button", onclick: () => setChildren(host, readerView(st, show)) }, h("div", { class: "lib-art" }, scene(st.scene, "")), h("div", { class: "lib-text" }, h("strong", {}, st.title), h("span", { class: "muted small" }, `${st.tag} · ${st.level} · ${st.minutes} min`))))),
    );
  };
  show();
}

// ---------------------------------------------------------------- page

export async function render(root, ctx) {
  const tabs = [["mine", "My stories", "book"], ["listen", "Listen & learn", "headphones"]];
  const body = h("div", {});
  const seg = h("div", { class: "seg", role: "group", "aria-label": "Stories" });
  let current = "mine";
  async function show(key) {
    current = key;
    setChildren(seg, tabs.map(([k, label, ic]) => h("button", { type: "button", "aria-pressed": String(k === current), onclick: () => show(k) }, icon(ic, 16), " ", label)));
    body.replaceChildren(spinner());
    const inner = h("div", {});
    try {
      if (key === "mine") await studio(inner, ctx);
      else library(inner);
      body.replaceChildren(inner);
    } catch (err) {
      body.replaceChildren(errorBox(err));
    }
  }
  root.append(
    banner({ title: "Stories", lede: "Prepare a few real stories you can reuse across Part 2 cue cards, and learn expressions from short illustrated ones.", image: "stories-hero", compact: true }),
    h("section", { class: "section tight" }, seg),
    body,
  );
  await show("mine");
}
