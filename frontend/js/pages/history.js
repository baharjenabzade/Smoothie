import { api } from "../api.js";
import { h, toast, formatBand, formatDate, plural, emptyState, chip, errorBox } from "../ui.js";
import { PART_LABELS, evaluationView } from "../components.js";

const PAGE = 20;

export async function render(root, ctx, sessionId) {
  if (sessionId) return renderDetail(root, ctx, sessionId);

  root.append(h("div", { class: "page-head" }, h("h1", {}, "History"), h("p", { class: "lede" }, "Every practice session, newest first.")));
  const list = h("ul", { class: "rows" });
  const moreHost = h("div", {});
  let offset = 0;

  async function load() {
    const items = await api.sessions({ limit: PAGE, offset });
    offset += items.length;
    for (const sess of items) {
      list.append(
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
      );
    }
    moreHost.replaceChildren();
    if (items.length === PAGE) {
      const more = h("button", { class: "btn", type: "button" }, "Show older sessions");
      more.addEventListener("click", async () => {
        more.disabled = true;
        try {
          await load();
        } catch (err) {
          toast(err.message, "error");
          more.disabled = false;
        }
      });
      moreHost.append(more);
    }
    return items.length;
  }

  const first = await load();
  if (!first) {
    root.append(emptyState("No sessions yet", "Your sessions are saved here as soon as you submit an answer.", h("a", { class: "btn btn-primary", href: "#/practice" }, "Start practising")));
    return;
  }
  root.append(list, moreHost);
}

async function renderDetail(root, ctx, id) {
  let session;
  try {
    session = await api.session(id);
  } catch (err) {
    root.append(h("p", {}, h("a", { href: "#/history" }, "Back to history")), errorBox(err));
    return;
  }

  const del = h("button", { class: "btn btn-danger", type: "button" }, "Delete session");
  del.addEventListener("click", async () => {
    if (!window.confirm("Delete this session and its answers? This cannot be undone.")) return;
    del.disabled = true;
    try {
      await api.deleteSession(id);
      toast("Session deleted.", "success");
      ctx.go("#/history");
    } catch (err) {
      toast(err.message, "error");
      del.disabled = false;
    }
  });

  root.append(
    h("p", { class: "small" }, h("a", { href: "#/history" }, "Back to history")),
    h(
      "div",
      { class: "page-head" },
      h("h1", {}, `${PART_LABELS[session.part]}${session.topic ? `: ${session.topic}` : ""}`),
      h("p", { class: "lede" }, `${formatDate(session.created_at)}. ${plural(session.answer_count, "answer", "answers")}, average band ${formatBand(session.average_band)}.`),
    ),
  );

  if (!session.answers.length) {
    root.append(emptyState("No answers in this session", "Answers you submit will be listed here.", h("a", { class: "btn btn-primary", href: "#/practice" }, "Practise now")));
  }
  for (const a of session.answers) {
    root.append(
      h(
        "section",
        { class: "section" },
        h("div", { class: "row-main" }, h("h3", { style: "max-width:60ch; white-space:pre-wrap" }, a.question_text), a.evaluation ? h("span", { class: "band", style: "font-size:1.75rem" }, formatBand(a.evaluation.overall_band)) : null),
        h("div", { class: "row-meta muted small", style: "margin-bottom:10px" }, formatDate(a.created_at), chip(plural(a.word_count, "word", "words"))),
        a.evaluation
          ? h("details", { class: "more" }, h("summary", {}, "Show marked answer and feedback"), evaluationView(a.evaluation, a.answer_text))
          : h("div", { class: "script" }, h("p", { class: "transcript" }, a.answer_text)),
      ),
    );
  }
  root.append(h("div", { class: "section" }, del));
}
