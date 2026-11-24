import { startSmoothie } from "./smoothie.js";

const svg = document.getElementById("smoothie");
if (svg) startSmoothie(svg);

// If this browser already has a session, point the buttons at the dashboard instead of sign-up.
let signedIn = false;
try {
  signedIn = Boolean(localStorage.getItem("ielts_token"));
} catch {
  /* storage blocked: treat as signed out */
}
if (signedIn) {
  const nav = document.getElementById("nav-cta");
  nav.textContent = "Open dashboard";
  nav.setAttribute("href", "app/#/dashboard");
  const hero = document.getElementById("hero-cta");
  hero.textContent = "Continue practising";
  hero.setAttribute("href", "app/#/practice");
}
