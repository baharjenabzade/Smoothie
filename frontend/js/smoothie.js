// The "word smoothie" animation: words fall into a cup, blend into juice, and a tiny learner
// sips it through a straw. Adapted from the supplied IELTS_Word_Smoothie.html:
//  - runs on the SVG element you pass in (no globals, no external font),
//  - the background is transparent so it sits on the page's own scene,
//  - the words are the things this app actually works on,
//  - it pauses while off-screen, and shows a still frame for reduced-motion users.

export function startSmoothie(svg) {
  const NS = "http://www.w3.org/2000/svg";
  const $ = (id) => svg.querySelector("#" + id);
  const el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const smooth = (x) => {
    x = clamp(x, 0, 1);
    return x * x * (3 - 2 * x);
  };
  const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const mix = (a, b, k) => {
    const A = hex(a);
    const B = hex(b);
    return "rgb(" + A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(",") + ")";
  };
  const outBack = (x) => {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  };
  const inBack = (x) => {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return c3 * x * x * x - c1 * x * x;
  };

  const T = 14.4; // loop length in seconds
  const BOT = 706;
  const TOP = 470;
  const G = 1300;
  const Y0 = -50;

  /* plants, recoloured to the site palette */
  const leafSpecs = [
    { x: 105, y: 700, r: -28, s: 1, c: "#8E72D6" },
    { x: 88, y: 704, r: -52, s: 0.8, c: "#6A4DB8" },
    { x: 132, y: 704, r: -8, s: 1.15, c: "#FF8F8C" },
    { x: 495, y: 700, r: 30, s: 1, c: "#6A4DB8" },
    { x: 512, y: 704, r: 54, s: 0.8, c: "#B9A6EE" },
    { x: 468, y: 704, r: 10, s: 1.1, c: "#F6665C" },
  ];
  const leafHost = $("leaves");
  const leaves = leafSpecs.map((L, i) => {
    const g = el("g", {}, leafHost);
    el("path", { d: "M0 0 C-24 -40 -20 -110 0 -150 C24 -110 20 -40 0 0 Z", fill: L.c }, g);
    el("path", { d: "M0 -6 L0 -128", stroke: "rgba(0,0,0,.18)", "stroke-width": 2, fill: "none" }, g);
    return { g, L, ph: i * 1.1 };
  });

  /* words: [text, pill colour, text colour, x] */
  const data = [
    ["vocabulary", "#F7B733", "#2B2A57", 300],
    ["fluency", "#B9D96C", "#2B2A57", 262],
    ["grammar", "#3C4A9E", "#FFF1DC", 338],
    ["idioms", "#F28A2E", "#2B2A57", 284],
    ["coherence", "#5E9A6B", "#FFF1DC", 322],
    ["speaking", "#FFD2A8", "#2B2A57", 250],
    ["collocations", "#5A2A55", "#FFF1DC", 350],
    ["Band 8", "#9ED8C0", "#2B2A57", 300],
  ];
  const N = data.length;
  const step = (BOT - TOP) / N;
  const inside = $("inside");
  const outside = $("outside");
  const words = data.map((d, i) => {
    const w = d[0].length * 9.4 + 30;
    const h = 34;
    const g = el("g", {}, outside);
    const rect = el("rect", { x: -w / 2, y: -h / 2, width: w, height: h, rx: h / 2, fill: d[1] }, g);
    const tx = el("text", { x: 0, y: 1, "text-anchor": "middle", "dominant-baseline": "central", "font-size": 16, fill: d[2] }, g);
    tx.textContent = d[0];
    const ripple = el("ellipse", { fill: "none", stroke: "#FFF1DC", "stroke-width": 3, opacity: 0 }, inside);
    const drops = [];
    for (let j = 0; j < 5; j++) drops.push(el("circle", { r: 3, fill: d[1], opacity: 0 }, inside));
    const hit = BOT - i * step;
    const start = 0.7 + i * 0.7;
    const dur = Math.sqrt((2 * (hit - Y0)) / G);
    return { i, g, rect, tx, ripple, drops, w, h, color: d[1], x: d[3], start, hit, dur, hitT: start + dur, parent: "out" };
  });

  /* bubbles */
  const bubHost = $("bubbles");
  const bubs = [];
  for (let b = 0; b < 9; b++) {
    const dark = b % 4 === 3;
    const c = dark
      ? el("circle", { r: 2.6, fill: "#2B2A57" }, bubHost)
      : el("circle", { r: 3 + (b % 3) * 1.6, fill: "none", stroke: "#FFF1DC", "stroke-width": 2 }, bubHost);
    bubs.push({ c, x: 205 + ((b * 47) % 190), ph: (b * 0.173) % 1, sp: 22 + (b % 4) * 6 });
  }

  const sips = [9.0, 10.35, 11.7];
  const SIPDUR = 1.15;
  const SIPDROP = 12;

  const liq = $("liq");
  const foam = $("foam");
  const cupG = $("cupG");
  const girl = $("girl");
  const head = $("head");
  const arms = $("arms");
  const straw = $("straw");
  const strawJuice = $("strawJuice");
  const eyeL = $("eyeL");
  const eyeR = $("eyeR");
  const happyL = $("happyL");
  const happyR = $("happyR");
  const chL = $("chL");
  const chR = $("chR");
  const GS = 0.88;

  function levelAt(t) {
    let fill = 0;
    for (let i = 0; i < N; i++) fill += step * smooth((t - words[i].hitT) / 0.55);
    let sip = 0;
    for (let i = 0; i < sips.length; i++) sip += SIPDROP * smooth((t - (sips[i] + 0.25)) / 0.6);
    const L = BOT - fill + sip;
    const dr = smooth((t - 12.9) / 1.0);
    return { level: L + (BOT - L) * dr, fill: fill * (1 - dr) };
  }
  function bumpAt(t) {
    let s = 0;
    for (let i = 0; i < N; i++) {
      const u = t - words[i].hitT;
      if (u > 0 && u < 2.5) s += 6 * Math.exp(-u * 2.6) * Math.cos(u * 14);
    }
    return s;
  }
  function presence(t) {
    if (t < 7 || t >= 13.7) return 170;
    if (t < 8) return (1 - outBack(t - 7)) * 170;
    if (t < 13) return 0;
    return 170 * inBack((t - 13) / 0.7);
  }

  function render(t) {
    const lv = levelAt(t);
    const level = lv.level;
    const bump = bumpAt(t);

    /* cup squash on landing */
    const sq = bump * 0.0016;
    cupG.setAttribute("transform", "translate(300 " + BOT + ") scale(" + (1 + sq) + " " + (1 - sq) + ") translate(-300 -" + BOT + ")");

    /* liquid */
    const A = 2.2 + Math.abs(bump) * 0.5;
    let d = "";
    let fd = "";
    let first = true;
    for (let x = 112; x <= 488; x += 12) {
      const y = level + A * Math.sin(x * 0.045 + t * 2.6);
      const pt = x + " " + y.toFixed(1);
      d += (first ? "M" : "L") + pt;
      fd += (first ? "M" : "L") + pt;
      first = false;
    }
    liq.setAttribute("d", d + "L488 780L112 780Z");
    foam.setAttribute("d", fd);
    const frac = clamp(lv.fill / (BOT - TOP), 0, 1);
    liq.setAttribute("fill", mix("#FFE1DC", "#FF9490", smooth(frac * 1.15)));
    foam.setAttribute("opacity", frac > 0.02 ? 0.7 : 0);

    /* bubbles */
    const span = Math.max(BOT - level, 1);
    bubs.forEach((b) => {
      const yy = BOT - 10 - ((t * b.sp + b.ph * span) % span);
      b.c.setAttribute("cx", b.x + 4 * Math.sin(t * 1.7 + b.ph * 9));
      b.c.setAttribute("cy", yy);
      b.c.setAttribute("opacity", frac > 0.06 && yy > level + 8 ? 0.75 : 0);
    });

    /* words */
    words.forEach((W) => {
      const s = t - W.start;
      const u = t - W.hitT;
      const sgn = W.i % 2 ? 1 : -1;
      if (s < 0 || u > 2.0) {
        W.g.setAttribute("opacity", 0);
        W.ripple.setAttribute("opacity", 0);
        W.drops.forEach((c) => c.setAttribute("opacity", 0));
        return;
      }
      let px;
      let py;
      let rot;
      let sc = 1;
      let txtO = 1;
      let blobO = 1;
      let blur = 0;
      let w = W.w;
      if (u < 0) {
        if (W.parent !== "out") {
          outside.appendChild(W.g);
          W.parent = "out";
        }
        py = Y0 + 0.5 * G * s * s;
        px = W.x + 10 * sgn * Math.sin(s * 6 + W.i) * (1 - (s / W.dur) * 0.5);
        rot = sgn * (16 * (1 - s / W.dur) + 4 * Math.sin(s * 7));
      } else {
        if (W.parent !== "in") {
          inside.appendChild(W.g);
          W.parent = "in";
        }
        const k = clamp(u / 1.9, 0, 1);
        const bl = smooth(u / 0.55);
        const m = smooth(u / 0.9);
        const surf = level;
        const ex = W.x;
        const ey = surf + 14 + 26 * (1 - Math.exp(-u * 4));
        const th = W.i * 1.3 + u * 4.2;
        const R = 64 * (1 - k);
        const cy = Math.min(level + 52, 668);
        const sx = 300 + R * Math.cos(th);
        const sy = cy + R * 0.38 * Math.sin(th);
        px = ex + (sx - ex) * bl;
        py = ey + (sy - ey) * bl;
        rot = sgn * u * 120 * bl;
        sc = 1 - 0.55 * k;
        w = W.w + (W.h - W.w) * m;
        txtO = 1 - smooth(u / 0.5);
        blobO = 1 - smooth((k - 0.55) / 0.45);
        blur = 3.5 * k;
        /* ripple */
        const ro = u < 0.8 ? (1 - u / 0.8) * 0.8 : 0;
        W.ripple.setAttribute("cx", W.x);
        W.ripple.setAttribute("cy", surf);
        W.ripple.setAttribute("rx", 10 + u * 60);
        W.ripple.setAttribute("ry", 2.5 + u * 10);
        W.ripple.setAttribute("opacity", ro);
        /* droplets */
        W.drops.forEach((c, j) => {
          const ang = (j - 2) * 0.5;
          const vx = Math.sin(ang) * 130;
          const vy = -(190 + j * 14);
          const dx = W.x + vx * u;
          const dy = surf + vy * u + 0.5 * 900 * u * u;
          const vis = u < 0.6 && dy < surf + 1;
          c.setAttribute("cx", dx);
          c.setAttribute("cy", dy);
          c.setAttribute("r", Math.max(0, 3.4 * (1 - u / 0.6))); // the original went negative here
          c.setAttribute("opacity", vis ? 1 : 0);
        });
      }
      W.rect.setAttribute("x", -w / 2);
      W.rect.setAttribute("width", w);
      W.tx.setAttribute("opacity", txtO);
      W.rect.setAttribute("opacity", blobO);
      W.g.setAttribute("opacity", 1);
      W.g.setAttribute("transform", "translate(" + px.toFixed(1) + " " + py.toFixed(1) + ") rotate(" + rot.toFixed(1) + ") scale(" + sc.toFixed(3) + ")");
      W.g.style.filter = blur > 0.2 ? "blur(" + blur.toFixed(1) + "px)" : "none";
    });

    /* girl */
    const off = presence(t);
    const present = off < 165;
    const idle = t > 8 && t < 13 ? 2 * Math.sin(t * 2.6) : 0;
    const tr = "translate(0 " + (off + idle).toFixed(1) + ") translate(300 330) scale(" + GS + ") translate(-300 -330)";
    girl.setAttribute("transform", tr);
    arms.setAttribute("transform", tr);
    arms.setAttribute("opacity", clamp((140 - off) / 50, 0, 1));
    girl.setAttribute("opacity", present ? 1 : 0);

    let amt = 0;
    sips.forEach((ts) => {
      const q = (t - ts) / SIPDUR;
      if (q > 0 && q < 1) amt = Math.max(amt, Math.sin(Math.PI * q));
    });
    head.setAttribute("transform", "rotate(" + (-7 * amt).toFixed(2) + " 300 262)");
    const happy = amt > 0.15;
    const blink = t % 3.4 < 0.1;
    eyeL.setAttribute("opacity", happy ? 0 : 1);
    eyeR.setAttribute("opacity", happy ? 0 : 1);
    eyeL.setAttribute("ry", blink ? 0.5 : 2.6);
    eyeR.setAttribute("ry", blink ? 0.5 : 2.6);
    happyL.setAttribute("opacity", happy ? 1 : 0);
    happyR.setAttribute("opacity", happy ? 1 : 0);
    chL.setAttribute("r", 6 + 2.5 * amt);
    chR.setAttribute("r", 6 + 2.5 * amt);

    /* straw */
    const my = 330 + (241 - 330) * GS + off + idle;
    const sd = "M301 " + my.toFixed(1) + " Q338 " + (my + 6).toFixed(1) + " 346 330 L358 640";
    straw.setAttribute("d", sd);
    strawJuice.setAttribute("d", sd);
    straw.setAttribute("opacity", present ? 1 : 0);
    const Ls = 400;
    let q2 = -1;
    sips.forEach((ts) => {
      const q = (t - ts) / SIPDUR;
      if (q > 0 && q < 1) q2 = q;
    });
    if (q2 >= 0 && present) {
      strawJuice.setAttribute("stroke-dasharray", "70 800");
      strawJuice.setAttribute("stroke-dashoffset", -((Ls - 70) * (1 - q2)).toFixed(1));
      strawJuice.setAttribute("opacity", 1);
    } else strawJuice.setAttribute("opacity", 0);

    /* plants */
    leaves.forEach((l) => {
      const r = l.L.r + 3 * Math.sin(t * 1.3 + l.ph);
      l.g.setAttribute("transform", "translate(" + l.L.x + " " + l.L.y + ") rotate(" + r.toFixed(2) + ") scale(" + l.L.s + ")");
    });
  }

  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    render(10.0); // a still frame mid-sip
    return;
  }

  render(0);
  let elapsed = 0;
  let last = 0;
  let raf = 0;
  function frame(now) {
    elapsed += Math.min((now - last) / 1000, 0.1);
    last = now;
    render(elapsed % T);
    raf = requestAnimationFrame(frame);
  }
  function play() {
    if (raf) return;
    last = performance.now();
    raf = requestAnimationFrame(frame);
  }
  function pause() {
    cancelAnimationFrame(raf);
    raf = 0;
  }
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((entries) => (entries[0].isIntersecting ? play() : pause())).observe(svg);
  } else {
    play();
  }
}
