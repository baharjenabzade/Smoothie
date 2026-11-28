// Turns pasted text, CSV or JSON into question objects. Pure functions: no DOM, easy to test.

const NUMBERING = /^\s*(?:q(?:uestion)?\s*\d+\s*[.):-]|\d+\s*[.):-]|[-*•▪●]\s+)\s*/i;
const PART_HEADING = /^\W*part\s*([123])\b.*$/i;
const TOPIC_HEADING = /^\W*(?:topic|theme|category)\s*[:：-]\s*(.+)$/i;
const MD_HEADING = /^#{1,4}\s+(.+)$/;
const SAY_LINE = /^\W*you\s+should\s+say\b/i;

function asItem(o) {
  const text = String(o.text ?? o.question ?? o.q ?? "").trim();
  const cues = o.cue_points ?? o.cues ?? o.points ?? [];
  return { part: Number(o.part) || 0, text, topic: String(o.topic ?? o.category ?? "").trim(), cue_points: Array.isArray(cues) ? cues.map(String) : String(cues).split("|").map((c) => c.trim()).filter(Boolean) };
}

function parseJson(raw) {
  let data = JSON.parse(raw);
  if (!Array.isArray(data)) data = data.questions ?? data.items ?? [];
  return data.filter((o) => o && typeof o === "object").map(asItem);
}

function parseCsv(raw) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < raw.length; i++) {
    const c = raw[i];
    if (quoted) {
      if (c === '"' && raw[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === "," ) { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && raw[i + 1] === "\n") i++; row.push(cell); rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  row.push(cell); rows.push(row);
  const header = rows[0].map((h) => h.trim().toLowerCase());
  return rows.slice(1).filter((r) => r.some((x) => x.trim())).map((r) => asItem(Object.fromEntries(header.map((h, i) => [h, r[i] ?? ""]))));
}

function looksLikeCsv(raw) {
  const first = raw.split(/\r?\n/, 1)[0].toLowerCase();
  return first.includes(",") && /(^|,)\s*"?(question|text)"?\s*(,|$)/.test(first);
}

/** Free text: headings like "Part 2" and "Topic: Hometown", numbered or bulleted questions, and cue cards. */
function parseText(raw, defaultPart) {
  const items = [];
  const lines = raw.split(/\r?\n/).map((l) => l.trim());
  let part = 0, topic = "", card = null;
  const flush = () => { if (card) { items.push(card); card = null; } };
  for (const line of lines) {
    if (!line) { flush(); continue; }
    const ph = line.match(PART_HEADING);
    if (ph && line.length < 60 && !line.includes("?")) { flush(); part = Number(ph[1]); continue; }
    const th = line.match(TOPIC_HEADING) || (line.match(MD_HEADING) && !line.includes("?") ? [null, line.match(MD_HEADING)[1]] : null);
    if (th && !/^describe\b/i.test(th[1])) { flush(); topic = th[1].trim().replace(/[:：]$/, ""); continue; }
    if (SAY_LINE.test(line)) continue;
    const body = line.replace(NUMBERING, "").trim();
    if (/^describe\b/i.test(body)) {
      flush();
      card = { part: 2, text: body, topic, cue_points: [] };
      continue;
    }
    if (card && body.endsWith("?")) flush(); // a question, not a cue point
    if (card && card.cue_points.length < 6) { card.cue_points.push(body); continue; }
    if (body.length < 8) continue;
    items.push({ part: part || defaultPart || 0, text: body, topic, cue_points: [] });
  }
  flush();
  return items;
}

/**
 * @param {string} raw
 * @param {{defaultPart?: number}} [opts] defaultPart 0 = guess (Part 1 unless a heading or "Describe" says otherwise)
 * @returns {{items: Array<{part:number,text:string,topic:string,cue_points:string[]}>, assumedPart: number}}
 */
export function parseQuestions(raw, { defaultPart = 0 } = {}) {
  const text = String(raw || "").replace(/^﻿/, "").trim();
  if (!text) return { items: [], assumedPart: 0 };
  let items;
  if (/^[[{]/.test(text)) items = parseJson(text);
  else if (looksLikeCsv(text)) items = parseCsv(text);
  else items = parseText(text, defaultPart);
  let assumed = 0;
  items = items
    .map((it) => {
      let part = defaultPart || it.part;
      if (!part) part = /^describe\b/i.test(it.text) ? 2 : (assumed++, 1);
      return { ...it, part, text: it.text.replace(/\s+/g, " ").trim(), cue_points: part === 2 ? it.cue_points.filter(Boolean) : [] };
    })
    .filter((it) => it.text.length >= 5);
  const seen = new Set();
  items = items.filter((it) => { const k = `${it.part}|${it.text.toLowerCase()}`; if (seen.has(k)) return false; seen.add(k); return true; });
  return { items, assumedPart: assumed };
}
