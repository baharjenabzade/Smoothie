// Voice recorder. Audio stays in the browser: it is recorded and played back here, never uploaded.
// (Scoring from audio is planned. For now the answer box is what gets evaluated.)
import { h } from "./ui.js";
import { icon } from "./art.js";

const fmt = (secs) => `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;

/**
 * @param {{onText?: (text: string) => void, targetSeconds?: number}} opts
 *   onText receives finished dictated phrases when the browser's speech-to-text is available and enabled.
 */
export function makeRecorder({ onText, targetSeconds = 120 } = {}) {
  const supported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  const clock = h("span", { class: "rec-clock", "aria-live": "off" }, "0:00");
  const status = h("p", { class: "rec-status muted small", role: "status" }, supported ? "Press the microphone and speak. Your recording stays on this device." : "Recording is not supported in this browser. Type your answer instead.");
  const micBtn = h("button", { class: "rec-btn", type: "button", "aria-label": "Start recording", disabled: !supported }, icon("mic", 26));
  const player = h("div", { class: "rec-player" });
  const dictBox = h("input", { type: "checkbox", id: "rec-dictate" });
  const dictLabel = h("label", { class: "check small", for: "rec-dictate" }, dictBox, "Also type what I say (uses your browser's speech service)");
  const root = h("div", { class: "recorder", "data-state": "idle" }, h("div", { class: "rec-main" }, micBtn, h("div", {}, clock, status)), player, onText && Recognition ? dictLabel : null);

  let stream = null, media = null, chunks = [], timer = null, startedAt = 0, url = null, recog = null;

  const setState = (state) => root.setAttribute("data-state", state);

  function cleanup() {
    clearInterval(timer);
    timer = null;
    if (recog) {
      try { recog.stop(); } catch { /* already stopped */ }
      recog = null;
    }
    if (stream) stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }

  function startDictation() {
    if (!(onText && Recognition && dictBox.checked)) return;
    recog = new Recognition();
    recog.lang = "en-GB";
    recog.continuous = true;
    recog.interimResults = false;
    recog.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++) if (e.results[i].isFinal) onText(e.results[i][0].transcript.trim());
    };
    recog.onerror = (e) => {
      status.textContent = e.error === "network" || e.error === "service-not-allowed" ? "Speech-to-text is not available here. Your recording still works; type your answer in the box." : "Speech-to-text stopped.";
    };
    recog.onend = () => { if (recog && root.dataset.state === "recording") { try { recog.start(); } catch { /* ignore */ } } };
    try { recog.start(); } catch { recog = null; }
  }

  async function start() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      status.textContent = err && err.name === "NotAllowedError" ? "Microphone access was blocked. Allow it in your browser's address bar, then try again." : "No microphone was found.";
      return;
    }
    if (url) { URL.revokeObjectURL(url); url = null; }
    player.replaceChildren();
    chunks = [];
    media = new MediaRecorder(stream);
    media.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    media.onstop = () => {
      const blob = new Blob(chunks, { type: media.mimeType || "audio/webm" });
      url = URL.createObjectURL(blob);
      player.replaceChildren(h("audio", { controls: true, src: url, "aria-label": "Your recording" }), h("button", { class: "btn btn-quiet btn-small", type: "button", onclick: discard }, "Delete recording"));
      status.textContent = "Listen back and notice where you hesitate, then check your answer in the box.";
      setState("recorded");
    };
    media.start();
    startedAt = Date.now();
    clock.textContent = "0:00";
    timer = setInterval(() => {
      if (!root.isConnected) { stop(); return; }
      const secs = Math.floor((Date.now() - startedAt) / 1000);
      clock.textContent = fmt(secs);
      root.classList.toggle("over", secs > targetSeconds);
    }, 250);
    setState("recording");
    micBtn.setAttribute("aria-label", "Stop recording");
    micBtn.replaceChildren(icon("stop", 26));
    status.textContent = "Recording… press again to stop.";
    startDictation();
  }

  function stop() {
    if (media && media.state !== "inactive") media.stop();
    cleanup();
    micBtn.setAttribute("aria-label", "Record again");
    micBtn.replaceChildren(icon("mic", 26));
  }

  function discard() {
    if (url) URL.revokeObjectURL(url);
    url = null;
    player.replaceChildren();
    clock.textContent = "0:00";
    status.textContent = "Press the microphone and speak. Your recording stays on this device.";
    micBtn.setAttribute("aria-label", "Start recording");
    setState("idle");
  }

  micBtn.addEventListener("click", () => (root.dataset.state === "recording" ? stop() : start()));
  return root;
}
