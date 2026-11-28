// Original flat illustrations drawn in code: a mascot, story scenes and small topic icons.
import { h, s } from "./ui.js";

const C = { ink: "#2a1a66", deep: "#1d1049", violet: "#5b3f9a", lilac: "#b79cff", pale: "#e9deff", coral: "#f6665c", peach: "#ffb199", cream: "#fff1dc", mint: "#7fe3bd", sun: "#ffd166", sky: "#8fb8ff", skin: "#f2b48c", skin2: "#c98a62", hair: "#3b2352" };

/** Put a generated picture (img/<name>.png) over a drawn fallback. If the file is missing the drawing stays. */
function withPhoto(fallback, name, cls, style) {
  const img = h("img", { class: "photo", src: `/img/${name}.png`, alt: "", decoding: "async" });
  img.addEventListener("load", () => { fallback.style.visibility = "hidden"; });
  img.addEventListener("error", () => img.remove());
  return h("div", { class: cls, style }, fallback, img);
}

const svg = (viewBox, attrs, ...kids) => s("svg", { viewBox, role: "img", ...attrs }, ...kids);
const g = (attrs, ...kids) => s("g", attrs, ...kids);
const rect = (x, y, w, h, fill, rx = 0) => s("rect", { x, y, width: w, height: h, fill, rx });
const circ = (cx, cy, r, fill) => s("circle", { cx, cy, r, fill });
const path = (d, fill, extra = {}) => s("path", { d, fill, ...extra });

/** The Smoothies cup character, wearing headphones. */
export function mascot(size = 160, label = "Smoothies mascot", photo = "mascot") {
  return withPhoto(drawMascot(size, label), photo, "mascot-wrap", `width:${size}px;height:${(size * 180) / 160}px`);
}

function drawMascot(size, label) {
  return svg("0 0 160 180", { width: size, height: (size * 180) / 160, "aria-label": label },
    path("M52 66h56l-8 96a8 8 0 0 1-8 7H68a8 8 0 0 1-8-7z", C.coral),
    path("M58 100h44l-3 38H61z", C.peach, { opacity: 0.55 }),
    rect(46, 54, 68, 16, C.cream, 8),
    path("M92 54l14-34", "none", { stroke: C.cream, "stroke-width": 6, "stroke-linecap": "round" }),
    circle(70, 106), circle(90, 106),
    path("M68 124q12 12 24 0", "none", { stroke: C.ink, "stroke-width": 4, "stroke-linecap": "round" }),
    circ(62, 118, 5, "#ff9a92"), circ(98, 118, 5, "#ff9a92"),
    path("M40 78a40 40 0 0 1 80 0", "none", { stroke: C.lilac, "stroke-width": 7, "stroke-linecap": "round" }),
    rect(30, 70, 16, 28, C.violet, 8), rect(114, 70, 16, 28, C.violet, 8),
    rect(34, 74, 8, 20, C.lilac, 4), rect(118, 74, 8, 20, C.lilac, 4),
  );
  function circle(x, y) { // eye
    return g({}, circ(x, y, 6, C.ink), circ(x + 2, y - 2, 2, "#fff"));
  }
}

function person(x, y, k, top, hairColor = C.hair, skin = C.skin) {
  return g({ transform: `translate(${x} ${y}) scale(${k})` },
    rect(-10, 22, 20, 30, top, 8), circ(0, 10, 11, skin),
    path("M-12 8a12 12 0 0 1 24 0c-4-3-8-4-12-4s-8 1-12 4z", hairColor),
    rect(-9, 50, 7, 16, C.ink, 3), rect(2, 50, 7, 16, C.ink, 3));
}

const SCENES = {
  travel: () => [
    rect(0, 0, 320, 200, "#9ec5ff"), circ(250, 46, 22, C.sun),
    path("M0 150l70-80 50 55 50-70 90 95v50H0z", "#7c5fd0"), path("M120 125l50-70 40 45z", "#a98bf0", { opacity: 0.7 }),
    path("M0 200V160q80-30 160-10t160-12v62z", "#5fcf9b"), path("M110 200q40-40 70-30t40-35", "none", { stroke: C.cream, "stroke-width": 9, "stroke-linecap": "round" }),
    person(165, 112, 1, C.coral), rect(172, 130, 12, 20, C.sun, 4),
  ],
  work: () => [
    rect(0, 0, 320, 200, "#efe6ff"), rect(30, 24, 90, 70, "#bfe0ff", 6), path("M30 70l30-22 30 20 30-14v40H30z", "#8fd1a8"),
    rect(0, 150, 320, 50, "#d9c8ff"), rect(60, 120, 200, 14, "#8c63e0", 4), rect(80, 134, 10, 40, "#6c46c4"), rect(230, 134, 10, 40, "#6c46c4"),
    rect(120, 84, 80, 38, C.ink, 4), rect(126, 90, 68, 26, "#7fe3bd", 2), rect(104, 120, 112, 6, "#4d3a8a", 3),
    person(255, 90, 1, C.coral, C.hair, C.skin2), rect(246, 118, 18, 8, C.cream, 3),
    circ(52, 118, 12, "#5fcf9b"), rect(48, 120, 8, 18, "#8c63e0", 3),
  ],
  nature: () => [
    rect(0, 0, 320, 200, "#d8f5e6"), circ(160, 120, 62, "#5b8cff"),
    path("M118 100q18-20 36-4t20 30q-30 6-50-6z", "#5fcf9b"), path("M164 140q20-6 32 6-6 16-26 10z", "#5fcf9b"),
    path("M70 200c0-40 14-70 14-90 0-16-8-26-14-34 18 6 28 20 28 40s-8 50-8 84z", "#3fae7d"),
    path("M250 200c0-30-10-54-10-68 0-12 6-20 10-26 14 4 20 16 20 30s-6 40-6 64z", "#3fae7d"),
    circ(52, 44, 5, C.sun), circ(268, 38, 4, C.coral),
  ],
  city: () => [
    rect(0, 0, 320, 200, "#ffd9c7"), circ(70, 52, 26, C.sun),
    rect(0, 160, 320, 40, "#6c46c4"), rect(20, 110, 40, 60, "#8c63e0"), rect(250, 100, 46, 70, "#8c63e0"), rect(206, 126, 36, 44, "#a98bf0"),
    rect(138, 40, 44, 128, "#c7a8ff"), path("M134 40l28-26 28 26z", "#8c63e0"), circ(160, 66, 13, C.cream), path("M160 58v9l6 4", "none", { stroke: C.ink, "stroke-width": 3, "stroke-linecap": "round" }),
    rect(150, 100, 20, 28, "#8c63e0", 10), rect(152, 138, 16, 30, "#8c63e0", 8),
    person(92, 128, 0.9, C.sky),
  ],
  kitchen: () => [
    rect(0, 0, 320, 200, "#fff1dc"), rect(0, 140, 320, 60, "#f6a58f"), rect(30, 40, 70, 54, "#ffe3a8", 6), rect(38, 48, 54, 38, "#fff1dc", 3),
    rect(110, 98, 100, 44, C.ink, 6), rect(104, 94, 112, 10, "#6c46c4", 5), rect(214, 112, 36, 8, C.ink, 4),
    path("M130 84q-8-14 2-24t0-22M160 84q-8-14 2-24t0-22M190 84q-8-14 2-24t0-22", "none", { stroke: "#f0c9b4", "stroke-width": 5, "stroke-linecap": "round" }),
    circ(264, 126, 20, C.mint), circ(264, 126, 12, "#fff1dc"), circ(66, 130, 16, C.coral), circ(100, 134, 12, C.sun),
  ],
  study: () => [
    rect(0, 0, 320, 200, "#e9deff"), circ(260, 50, 30, "#cfb9ff"), circ(60, 40, 6, C.coral),
    rect(0, 158, 320, 42, "#8c63e0"),
    rect(70, 126, 110, 16, C.coral, 3), rect(82, 110, 96, 16, "#5b8cff", 3), rect(76, 94, 100, 16, C.sun, 3),
    rect(220, 100, 8, 58, "#4d3a8a"), path("M200 100l48 0-10-26h-28z", C.sun), rect(194, 156, 60, 8, "#4d3a8a", 4),
    person(120, 36, 1, C.sky, C.hair, C.skin), path("M104 40a16 16 0 0 1 32 0", "none", { stroke: C.coral, "stroke-width": 5, "stroke-linecap": "round" }),
  ],
};

/** Story illustration. kind: travel | work | nature | city | kitchen | study */
export function scene(kind, label = "") {
  const draw = SCENES[kind] || SCENES.travel;
  const drawn = svg("0 0 320 200", { class: "scene", preserveAspectRatio: "xMidYMid slice", "aria-label": label || `${kind} illustration` }, ...draw());
  return withPhoto(drawn, `scene-${kind}`, "scene-wrap", "");
}

const ICONS = {
  technology: "M4 5h16v11H4zM9 19h6M12 16v3",
  people: "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20c0-3 3-5 6-5s6 2 6 5M17 11a2.5 2.5 0 1 0 0-5M17 15c2.5 0 4 1.7 4 4",
  money: "M12 21a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM12 8v8M9.5 10.5c0-1 1-1.6 2.5-1.6s2.5.7 2.5 1.7-1 1.4-2.5 1.8-2.5.8-2.5 1.8 1 1.6 2.5 1.6 2.5-.6 2.5-1.6",
  memories: "M12 21a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM12 8v4l3 2",
  education: "M2 9l10-5 10 5-10 5zM6 11.5V16c0 1.5 3 3 6 3s6-1.500 6-3v-4.500",
  "nature-travel": "M3 15l17-9-4 15-4-6zM12 15l-1 5",
  work: "M3 8h18v11H3zM9 8V5h6v3M3 13h18",
  culture: "M9 18V6l10-2v12M9 18a2.500 2.500 0 1 1-5 0 2.500 2.500 0 0 1 5 0zM19 16a2.500 2.500 0 1 1-5 0 2.500 2.500 0 0 1 5 0z",
  lifestyle: "M12 20s-8-5-8-11a4.500 4.500 0 0 1 8-2.500A4.500 4.500 0 0 1 20 9c0 6-8 11-8 11z",
  places: "M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11zM12 12.500a2.500 2.500 0 1 0 0-5 2.500 2.500 0 0 0 0 5z",
  mic: "M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3zM6 11a6 6 0 0 0 12 0M12 17v4",
  play: "M8 5l11 7-11 7z",
  stop: "M7 7h10v10H7z",
  headphones: "M4 14v-2a8 8 0 0 1 16 0v2M4 14h3v6H4zM17 14h3v6h-3z",
  book: "M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 19V5",
  spark: "M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z",
};

export function icon(name, size = 22) {
  return svg("0 0 24 24", { width: size, height: size, fill: "none", stroke: "currentColor", "stroke-width": 1.8, "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true", role: "presentation" }, path(ICONS[name] || ICONS.spark, "none"));
}

/** A picture from frontend/img/. Removes itself if the file is missing. */
export function pic(name, alt = "", cls = "") {
  const img = h("img", { class: `pic ${cls}`.trim(), src: `/img/${name}.webp`, alt, loading: "lazy", decoding: "async" });
  img.addEventListener("error", () => img.remove());
  return img;
}

/** Page banner: text on the left, illustration on the right. */
export function banner({ title, lede, image, alt = "", actions = null, compact = false, level = "h1" }) {
  return h("div", { class: `hero-strip${compact ? " compact" : ""}` }, h("div", { class: "hero-copy" }, h(level, {}, title), lede ? h("p", { class: "lede" }, lede) : null, actions ? h("div", { class: "btn-row" }, actions) : null), image ? pic(image, alt, "hero-pic") : null);
}
