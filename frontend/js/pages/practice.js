import { api } from "../api.js";
import { h, setChildren, toast, spinner, errorBox, withBusy, countWords, chip } from "../ui.js";
import { evaluationView, vocabCard } from "../components.js";
import { makeRecorder } from "../recorder.js";
import { banner, icon } from "../art.js";

const PARTS = [
  { n: 1, title: "Part 1", desc: "Short answers about familiar topics. Aim for 2 to 4 sentences." },
  { n: 2, title: "Part 2", desc: "A cue card. Speak for 1 to 2 minutes without stopping." },
  { n: 3, title: "Part 3", desc: "Abstract questions. Give your opinion, a reason and an example." },
];
const LENGTH_HINT = { 1: "20 to 50 words", 2: "120 to 250 words", 3: "40 to 90 words" };
const SAMPLE_BANDS = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9];
const CLUSTER_ICON = { technology: "technology", people: "people", money: "money", memories: "memories", education: "education", "nature-travel": "nature-travel", work: "work", culture: "culture", lifestyle: "lifestyle", places: "places" };
const TIPS = [
  "Try natural collocations like “in my experience”, “to be honest” or “what really stood out was…”.",
  "Add a reason and a tiny example to every answer: “because…, for instance…”.",
  "For Part 2, one real story can answer several cue cards. Save it in Stories.",
  "Pause and rephrase instead of repeating the same word. Paraphrasing earns lexical marks.",
];

function fullQuestionText(q) {
  const cues = q.cue_points && q.cue_points.length ? ` You should say: ${q.cue_points.join("; ")}.` : "";
  return `${q.text}${cues}`.slice(0, 1000);
}

export async function render(root, ctx) {
  const st = { part: 1, cluster: null, group: null, topic: "", question: null, session: null, answer: "" };
  let clusters = [];
  let myGroups = [];
  let groupQuestions = [];
  try {
    myGroups = await api.groups();
  } catch {
    /* groups are optional */
  }
  try {
    clusters = await api.clusters();
  } catch {
    /* clusters are optional; questions can still be fetched */
  }
  const clustersOf = (topic) => clusters.filter((c) => c.topics.some((t) => t.topic === topic));
  const pending = ctx.pending && ctx.pending.question ? ctx.pending.question : null;
  ctx.pending = null;
  if (pending) {
    st.part = pending.part;
    st.topic = pending.topic;
    st.cluster = (clustersOf(pending.topic)[0] || {}).slug || null;
  }

  // --- containers ---
  const partButtons = h("div", { class: "seg", role: "group", "aria-label": "IELTS part" });
  const partDesc = h("p", { class: "muted small seg-desc" });
  const clusterList = h("ul", { class: "cluster-list" });
  const topicBox = h("div", { class: "topic-tiles" });
  const genTopic = h("input", { id: "gen-topic", type: "text", maxlength: 100, placeholder: "e.g. Weekends" });
  const browseBox = h("div", {});
  const workBox = h("div", {});
  const relatedBox = h("div", { class: "chips" });
  const storiesBox = h("div", {});
  const randomBtn = h("button", { class: "btn btn-primary", type: "button" }, "Random question");
  const genBtn = h("button", { class: "btn btn-small", type: "button" }, "Generate with AI");
  const currentCluster = () => clusters.find((c) => c.slug === st.cluster) || null;

  function drawParts() {
    setChildren(partButtons, PARTS.map((p) => h("button", { type: "button", "aria-pressed": String(p.n === st.part), onclick: () => setPart(p.n) }, p.title)));
    partDesc.textContent = PARTS[st.part - 1].desc;
  }

  function drawClusters() {
    setChildren(
      clusterList,
      myGroups.length ? h("li", { class: "list-label" }, "My groups") : null,
      myGroups.map((g) => h("li", {}, h("button", { type: "button", class: "cluster-btn", "aria-pressed": String(!!st.group && st.group.id === g.id), onclick: () => selectGroup(g) }, h("span", { class: "cluster-ico" }, icon("book", 20)), h("span", { class: "cluster-txt" }, h("strong", {}, g.name), h("small", {}, `${g.question_count} questions`))))),
      myGroups.length ? h("li", { class: "list-label" }, "Topic groups") : null,
      clusters.map((c) =>
        h("li", {}, h("button", { type: "button", class: "cluster-btn", "aria-pressed": String(c.slug === st.cluster), onclick: () => selectCluster(c.slug) }, h("span", { class: "cluster-ico" }, icon(CLUSTER_ICON[c.slug] || "spark", 20)), h("span", { class: "cluster-txt" }, h("strong", {}, c.name), h("small", {}, `${c.topics.length} topics`)))),
      ),
    );
  }

  function drawTopics() {
    const c = currentCluster();
    if (st.group) {
      setChildren(topicBox, h("p", { class: "muted small" }, `Your group “${st.group.name}”: ${st.group.topics.length ? st.group.topics.join(", ") : "individual questions"}.`, " ", h("a", { href: "#/library" }, "Edit in Library")));
      return;
    }
    if (!c) {
      setChildren(topicBox, h("p", { class: "muted small" }, clusters.length ? "Pick a topic group to see its topics, or press Random question for anything." : "Press Random question to start."));
      return;
    }
    setChildren(
      topicBox,
      h("p", { class: "muted small" }, c.blurb),
      h("div", { class: "chips" }, c.topics.map((t) => h("button", { type: "button", class: "tchip", "aria-pressed": String(t.topic === st.topic), onclick: () => selectTopic(t.topic) }, t.topic, h("small", {}, String(t.counts[st.part] || 0))))),
    );
  }

  function drawRelated() {
    const base = st.question ? st.question.topic : st.topic;
    const own = base ? clustersOf(base) : [];
    const score = new Map();
    for (const c of own) for (const t of c.topics) if (t.topic !== base) score.set(t.topic, (score.get(t.topic) || 0) + 1);
    const items = [...score.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    setChildren(relatedBox, items.length ? items.map(([t]) => h("button", { type: "button", class: "tchip", onclick: () => { st.cluster = (own.find((c) => c.topics.some((x) => x.topic === t)) || own[0]).slug; selectTopic(t); } }, t)) : h("p", { class: "muted small" }, "Choose a topic to see related ones."));
  }

  async function drawSuggestions(q) {
    storiesBox.replaceChildren();
    if (!q || !q.id || q.part !== 2) return;
    try {
      const items = await api.suggestStories(q.id);
      if (st.question !== q) return;
      setChildren(
        storiesBox,
        h("h3", {}, "Your stories that fit"),
        items.length ? h("ul", { class: "rows" }, items.map((s) => h("li", {}, h("a", { href: "#/stories" }, s.title)))) : h("p", { class: "muted small" }, "No saved story fits this cue card yet. Write one in Stories and reuse it here."),
      );
    } catch {
      /* suggestions are optional */
    }
  }

  function redraw() {
    drawClusters();
    drawTopics();
    drawRelated();
  }

  function setPart(n) {
    if (n === st.part) return;
    st.part = n;
    st.topic = "";
    st.question = null;
    st.session = null;
    drawParts();
    redraw();
    browseBox.replaceChildren();
    workBox.replaceChildren();
    storiesBox.replaceChildren();
    if (st.group) loadGroup();
  }

  async function loadGroup() {
    browseBox.replaceChildren(spinner());
    try {
      const d = await api.group(st.group.id, st.part);
      groupQuestions = d.questions;
      browseBox.replaceChildren(questionList(groupQuestions));
    } catch (err) {
      browseBox.replaceChildren(errorBox(err));
    }
  }

  function selectGroup(g) {
    st.group = g;
    st.cluster = null;
    st.topic = "";
    redraw();
    loadGroup();
  }

  function selectCluster(slug) {
    st.group = null;
    st.cluster = slug;
    st.topic = "";
    redraw();
    browseBox.replaceChildren();
  }

  async function selectTopic(topic) {
    st.group = null;
    st.topic = topic;
    genTopic.value = topic;
    redraw();
    browseBox.replaceChildren(spinner());
    try {
      const items = await api.questions({ part: st.part, topic, limit: 30 });
      browseBox.replaceChildren(questionList(items));
    } catch (err) {
      browseBox.replaceChildren(errorBox(err));
    }
  }

  function choose(q) {
    st.question = q;
    browseBox.replaceChildren();
    drawWork();
    drawRelated();
    workBox.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function questionList(items, intro) {
    return h(
      "section",
      { class: "section" },
      intro ? h("p", { class: "muted" }, intro) : null,
      items.length
        ? h("ul", { class: "rows" }, items.map((q) => h("li", {}, h("div", { class: "row-main" }, h("div", {}, h("div", { class: "row-title" }, q.text), h("div", { class: "row-meta" }, chip(q.topic), q.is_ai_generated ? chip("AI generated", "chip-accent") : null)), h("button", { class: "btn", type: "button", onclick: () => choose(q) }, "Practise this")))))
        : h("p", { class: "muted" }, `No Part ${st.part} questions for this topic yet. Generate some with AI on the right.`),
    );
  }

  async function pickRandom() {
    if (st.group) {
      if (!groupQuestions.length) await loadGroup();
      if (groupQuestions.length) return choose(groupQuestions[Math.floor(Math.random() * groupQuestions.length)]);
      toast(`No Part ${st.part} questions in this group yet.`, "error");
      return;
    }
    let topic = st.topic;
    const c = currentCluster();
    if (!topic && c) {
      const open = c.topics.filter((t) => t.counts[st.part] > 0);
      if (open.length) topic = open[Math.floor(Math.random() * open.length)].topic;
    }
    try {
      choose(await api.randomQuestion({ part: st.part, topic }));
    } catch (err) {
      toast(err.status === 404 ? "No questions for that topic yet. Try another topic or generate some." : err.message, "error");
    }
  }
  randomBtn.addEventListener("click", () => withBusy(randomBtn, "Finding…", pickRandom));

  genBtn.addEventListener("click", () => {
    const topic = genTopic.value.trim();
    if (!topic) {
      toast("Enter a topic to generate questions about.", "error");
      genTopic.focus();
      return;
    }
    return withBusy(genBtn, "Generating…", async () => {
      browseBox.replaceChildren(spinner("The AI is writing questions. This can take up to a minute."));
      try {
        const items = await api.generateQuestions({ part: st.part, topic, count: 3 });
        browseBox.replaceChildren(questionList(items, `New questions on “${topic}” were added to your question bank.`));
      } catch (err) {
        browseBox.replaceChildren(errorBox(err));
      }
    });
  });

  // --- answering ---
  function drawWork() {
    const q = st.question;
    if (!q) {
      workBox.replaceChildren();
      return;
    }
    const answer = h("textarea", { id: "answer", placeholder: "Type or paste what you said…", "aria-describedby": "count-line" });
    answer.value = st.answer = "";
    const wordCount = h("span", {}, "0 words");
    answer.addEventListener("input", () => {
      st.answer = answer.value;
      wordCount.textContent = `${countWords(answer.value)} words`;
    });
    const recorder = makeRecorder({ onText: (t) => { answer.value = `${answer.value} ${t}`.trim(); answer.dispatchEvent(new Event("input")); }, targetSeconds: st.part === 2 ? 120 : 60 });
    const evalBtn = h("button", { class: "btn btn-primary", type: "button" }, "Evaluate answer");
    const status = h("div", {});
    const resultBox = h("div", {});
    const sampleBox = h("div", {});

    const bandSelect = h(
      "select",
      { id: "sample-band" },
      SAMPLE_BANDS.map((b) => h("option", { value: b, selected: b === Math.round(ctx.user.target_band * 2) / 2 }, b.toFixed(1))),
    );
    const sampleBtn = h("button", { class: "btn", type: "button" }, "Write a sample answer");

    sampleBtn.addEventListener("click", () =>
      withBusy(sampleBtn, "Writing…", async () => {
        sampleBox.replaceChildren(spinner("The AI is writing a sample answer. This can take up to a minute."));
        try {
          const r = await api.sampleAnswer({ part: st.part, question_text: fullQuestionText(q), target_band: Number(bandSelect.value) });
          sampleBox.replaceChildren(
            h(
              "section",
              { class: "section" },
              h("h3", {}, `Sample answer at band ${Number(bandSelect.value).toFixed(1)}`),
              h("p", { class: "improved" }, r.sample_answer),
              r.key_features.length ? h("div", { style: "margin-top:14px" }, h("h4", { style: "margin-bottom:6px" }, "Why it works"), h("ul", {}, r.key_features.map((f) => h("li", {}, f)))) : null,
              r.useful_vocabulary.length ? h("div", { class: "vocab-grid", style: "margin-top:14px" }, r.useful_vocabulary.map(vocabCard)) : null,
            ),
          );
        } catch (err) {
          sampleBox.replaceChildren(errorBox(err));
        }
      }),
    );

    async function showFollowUps(button, submittedText) {
      await withBusy(button, "Thinking…", async () => {
        try {
          const r = await api.followUp({ question_text: fullQuestionText(q), answer_text: submittedText });
          followBox.replaceChildren(
            h(
              "div",
              { style: "margin-top:16px" },
              h("h4", { style: "margin-bottom:6px" }, "Follow-up questions"),
              h(
                "ul",
                { class: "rows" },
                r.follow_up_questions.map((text) =>
                  h("li", {}, h("div", { class: "row-main" }, h("span", { class: "row-title" }, text), h("button", { class: "btn", type: "button", onclick: () => choose({ id: null, part: st.part, topic: q.topic, text, cue_points: null }) }, "Answer this"))),
                ),
              ),
            ),
          );
        } catch (err) {
          followBox.replaceChildren(errorBox(err));
        }
      });
    }
    const followBox = h("div", {});

    evalBtn.addEventListener("click", async () => {
      const text = answer.value.trim();
      if (countWords(text) < 3) {
        toast("Write at least a few words before evaluating.", "error");
        answer.focus();
        return;
      }
      resultBox.replaceChildren();
      followBox.replaceChildren();
      await withBusy(evalBtn, "Evaluating…", async () => {
        status.replaceChildren(spinner("The AI is reading your answer. This can take up to a minute."));
        try {
          if (!st.session || st.session.part !== st.part) {
            st.session = await api.createSession({ part: st.part, topic: q.topic || null });
          }
          const body = q.id ? { question_id: q.id, answer_text: text } : { question_text: fullQuestionText(q), answer_text: text };
          const saved = await api.submitAnswer(st.session.id, body);
          status.replaceChildren();
          const followBtn = h("button", { class: "btn", type: "button" }, "Get follow-up questions");
          followBtn.addEventListener("click", () => showFollowUps(followBtn, text));
          const nextBtn = h("button", { class: "btn btn-primary", type: "button", onclick: () => pickRandom() }, "Next random question");
          resultBox.replaceChildren(
            h("section", { class: "section" }, evaluationView(saved.evaluation, text), h("div", { class: "btn-row", style: "margin-top:18px" }, followBtn, nextBtn), followBox),
          );
          resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (err) {
          status.replaceChildren(errorBox(err));
        }
      });
    });

    drawSuggestions(q);
    workBox.replaceChildren(
      h(
        "section",
        { class: "section" },
        h(
          "div",
          { class: "question-card" },
          h("div", { class: "row-meta", style: "margin:0 0 6px" }, chip(`Part ${st.part}`), q.topic ? chip(q.topic) : null),
          h("p", { class: "q-text" }, q.text),
          q.cue_points && q.cue_points.length ? h("ul", {}, q.cue_points.map((c) => h("li", {}, c))) : null,
        ),
        h("h3", { style: "margin:0 0 8px" }, "Speak your answer"),
        recorder,
        h("label", { for: "answer", style: "margin-top:16px" }, "Your answer (this is what gets marked)"),
        answer,
        h("div", { class: "counter", id: "count-line" }, h("span", {}, wordCount, ` · aim for ${LENGTH_HINT[st.part]}`), h("span", {})),
        h("div", { class: "btn-row" }, evalBtn),
        h("p", { class: "muted small", style: "margin-top:10px" }, "Recordings are for listening back. Marking uses the text in the box, so type what you said or turn on “Also type what I say”. Marking your voice directly is coming later."),
        status,
        h("div", { class: "inline-fields", style: "margin-top:18px" }, h("div", { class: "field" }, h("label", { for: "sample-band" }, "Sample answer at band"), bandSelect), sampleBtn),
      ),
      sampleBox,
      resultBox,
    );
  }

  const tip = TIPS[Math.floor(Math.random() * TIPS.length)];
  root.append(
    banner({ title: "Let’s practise your speaking", lede: "Pick a topic group, choose a question, then speak or type your answer.", image: "practice-hero", compact: true }),
    h(
      "div",
      { class: "practice-grid" },
      h("aside", { class: "col-left", "aria-label": "Topic groups" }, h("h2", { class: "col-title" }, "Topic groups"), clusterList),
      h(
        "div",
        { class: "col-main" },
        h("section", { class: "section" }, partButtons, partDesc, topicBox, h("div", { class: "btn-row", style: "margin-top:14px" }, randomBtn)),
        browseBox,
        workBox,
      ),
      h(
        "aside",
        { class: "col-right", "aria-label": "Related" },
        h("section", { class: "side-card" }, h("h3", {}, "Related topics"), relatedBox),
        h("section", { class: "side-card" }, storiesBox, h("a", { href: "#/stories", class: "small" }, "Open my stories")),
        h("section", { class: "side-card tip" }, h("h3", {}, icon("spark", 16), " Tip"), h("p", { class: "small" }, tip)),
        h("section", { class: "side-card" }, h("h3", {}, "Need something new?"), h("div", { class: "field" }, h("label", { for: "gen-topic" }, "Topic for new questions"), genTopic), genBtn),
      ),
    ),
  );
  drawParts();
  redraw();
  if (pending) choose(pending);
}
