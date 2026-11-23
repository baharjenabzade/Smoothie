import { api } from "../api.js";
import { h, setChildren, toast, spinner, errorBox, withBusy, countWords, chip } from "../ui.js";
import { evaluationView, vocabCard } from "../components.js";

const PARTS = [
  { n: 1, title: "Part 1", desc: "Short answers about familiar topics. Aim for 2 to 4 sentences." },
  { n: 2, title: "Part 2", desc: "A cue card. Speak for 1 to 2 minutes without stopping." },
  { n: 3, title: "Part 3", desc: "Abstract questions. Give your opinion, a reason and an example." },
];
const LENGTH_HINT = { 1: "20 to 50 words", 2: "120 to 250 words", 3: "40 to 90 words" };
const SAMPLE_BANDS = [5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9];

function fullQuestionText(q) {
  const cues = q.cue_points && q.cue_points.length ? ` You should say: ${q.cue_points.join("; ")}.` : "";
  return `${q.text}${cues}`.slice(0, 1000);
}

function makeTimer() {
  const out = h("span", { class: "timer" }, "0:00");
  let started = 0;
  let handle = null;
  const button = h("button", { type: "button", class: "btn btn-quiet" }, "Start timer");
  const tick = () => {
    if (!out.isConnected) {
      clearInterval(handle);
      return;
    }
    const secs = Math.floor((Date.now() - started) / 1000);
    out.textContent = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;
  };
  button.addEventListener("click", () => {
    if (handle) {
      clearInterval(handle);
      handle = null;
      button.textContent = "Start timer";
    } else {
      started = Date.now();
      out.textContent = "0:00";
      handle = setInterval(tick, 500);
      button.textContent = "Stop timer";
    }
  });
  return { out, button };
}

export async function render(root, ctx) {
  const st = { part: 1, topic: "", question: null, session: null, answer: "" };
  let topics = [];
  try {
    topics = await api.topics();
  } catch {
    /* the topic list is optional; questions can still be fetched */
  }

  // --- containers (pages must keep references; root's children are moved after render) ---
  const partButtons = h("div", { class: "seg", role: "group", "aria-label": "IELTS part" });
  const partDesc = h("p", { class: "muted small seg-desc" });
  const topicSelect = h("select", { id: "topic" });
  const genTopic = h("input", { id: "gen-topic", type: "text", maxlength: 100, placeholder: "e.g. Weekends" });
  const browseBox = h("div", {});
  const workBox = h("div", {});

  function drawParts() {
    setChildren(partButtons, PARTS.map((p) => h("button", { type: "button", "aria-pressed": String(p.n === st.part), onclick: () => setPart(p.n) }, p.title)));
    partDesc.textContent = PARTS[st.part - 1].desc;
  }

  function drawTopics() {
    const options = topics.filter((t) => t.parts.includes(st.part));
    setChildren(topicSelect, h("option", { value: "" }, "Any topic"), options.map((t) => h("option", { value: t.topic, selected: t.topic === st.topic }, t.topic)));
  }

  function setPart(n) {
    if (n === st.part) return;
    st.part = n;
    st.topic = "";
    st.question = null;
    st.session = null;
    drawParts();
    drawTopics();
    browseBox.replaceChildren();
    workBox.replaceChildren();
  }

  topicSelect.addEventListener("change", () => {
    st.topic = topicSelect.value;
    genTopic.value = st.topic;
  });

  // --- choosing a question ---
  function choose(q) {
    st.question = q;
    browseBox.replaceChildren();
    drawWork();
    workBox.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const randomBtn = h("button", { class: "btn btn-primary", type: "button" }, "Random question");
  const browseBtn = h("button", { class: "btn", type: "button" }, "Browse questions");
  const genBtn = h("button", { class: "btn", type: "button" }, "Generate with AI");

  function questionList(items, intro) {
    return h(
      "section",
      { class: "section" },
      intro ? h("p", { class: "muted" }, intro) : null,
      items.length
        ? h(
            "ul",
            { class: "rows" },
            items.map((q) =>
              h(
                "li",
                {},
                h("div", { class: "row-main" }, h("div", {}, h("div", { class: "row-title" }, q.text), h("div", { class: "row-meta" }, chip(q.topic), q.is_ai_generated ? chip("AI generated", "chip-blue") : null)), h("button", { class: "btn", type: "button", onclick: () => choose(q) }, "Practise this")),
              ),
            ),
          )
        : h("p", { class: "muted" }, "No questions match. Try another topic, or generate new ones."),
    );
  }

  randomBtn.addEventListener("click", () =>
    withBusy(randomBtn, "Finding…", async () => {
      try {
        choose(await api.randomQuestion({ part: st.part, topic: st.topic }));
      } catch (err) {
        toast(err.status === 404 ? "No questions for that topic yet. Try another topic or generate some." : err.message, "error");
      }
    }),
  );

  browseBtn.addEventListener("click", () =>
    withBusy(browseBtn, "Loading…", async () => {
      try {
        const items = await api.questions({ part: st.part, topic: st.topic, limit: 30 });
        browseBox.replaceChildren(questionList(items));
      } catch (err) {
        browseBox.replaceChildren(errorBox(err));
      }
    }),
  );

  genBtn.addEventListener("click", () => {
    const topic = genTopic.value.trim();
    if (!topic) {
      toast("Enter a topic to generate questions about.", "error");
      genTopic.focus();
      return;
    }
    return withBusy(genBtn, "Generating…", async () => {
      browseBox.replaceChildren(spinner("The local model is writing questions. This can take a minute."));
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
    const timer = makeTimer();
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
        sampleBox.replaceChildren(spinner("The local model is writing a sample answer. This can take a minute."));
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
        status.replaceChildren(spinner("The local model is reading your answer. This can take a minute."));
        try {
          if (!st.session || st.session.part !== st.part) {
            st.session = await api.createSession({ part: st.part, topic: q.topic || null });
          }
          const body = q.id ? { question_id: q.id, answer_text: text } : { question_text: fullQuestionText(q), answer_text: text };
          const saved = await api.submitAnswer(st.session.id, body);
          status.replaceChildren();
          const followBtn = h("button", { class: "btn", type: "button" }, "Get follow-up questions");
          followBtn.addEventListener("click", () => showFollowUps(followBtn, text));
          const nextBtn = h("button", { class: "btn btn-primary", type: "button", onclick: () => randomBtn.click() }, "Next random question");
          resultBox.replaceChildren(
            h("section", { class: "section" }, evaluationView(saved.evaluation, text), h("div", { class: "btn-row", style: "margin-top:18px" }, followBtn, nextBtn), followBox),
          );
          resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (err) {
          status.replaceChildren(errorBox(err));
        }
      });
    });

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
        h("label", { for: "answer" }, "Your answer"),
        answer,
        h("div", { class: "counter", id: "count-line" }, h("span", {}, wordCount, ` · aim for ${LENGTH_HINT[st.part]}`), h("span", {}, timer.out, " ", timer.button)),
        h("div", { class: "btn-row" }, evalBtn),
        h("p", { class: "muted small", style: "margin-top:10px" }, "Type or paste a transcript of what you said, for example from your phone's voice typing. Audio recording is not supported yet."),
        status,
        h("div", { class: "inline-fields", style: "margin-top:18px" }, h("div", { class: "field" }, h("label", { for: "sample-band" }, "Sample answer at band"), bandSelect), sampleBtn),
      ),
      sampleBox,
      resultBox,
    );
    answer.focus({ preventScroll: true });
  }

  root.append(
    h("div", { class: "page-head" }, h("h1", {}, "Practice"), h("p", { class: "lede" }, "Choose a part and a question, then answer it in writing.")),
    h(
      "section",
      { class: "section" },
      partButtons,
      partDesc,
      h("div", { class: "inline-fields", style: "margin-top:16px" }, h("div", { class: "field", style: "min-width:220px" }, h("label", { for: "topic" }, "Topic"), topicSelect)),
      h("div", { class: "btn-row", style: "margin-top:16px" }, randomBtn, browseBtn),
      h(
        "div",
        { class: "inline-fields", style: "margin-top:22px" },
        h("div", { class: "field", style: "min-width:220px" }, h("label", { for: "gen-topic" }, "Need something new? Topic for new questions"), genTopic),
        genBtn,
      ),
    ),
    browseBox,
    workBox,
  );
  drawParts();
  drawTopics();
}
