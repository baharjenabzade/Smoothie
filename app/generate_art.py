"""Generate the website illustrations with a Gemini image model, using your own API key.

    python -m app.generate_art                      # make every missing image
    python -m app.generate_art --only mascot        # one image (name without .png)
    python -m app.generate_art --force              # redo images that already exist
    python -m app.generate_art --style-ref ref.png  # copy the look of a picture you like
    python -m app.generate_art --model gemini-3.1-flash-image

Images are saved to frontend/img/ and the site picks them up automatically (it falls back to the
built-in drawings if a file is missing). Image generation may need a paid Google plan; if you see a
quota error with "limit: 0", the free tier does not include image models for your key.
Review every image before publishing: AI images can contain mistakes, and you are responsible for
how you use them under Google's current terms.
"""

import argparse
import base64
import mimetypes
import sys
import time
from pathlib import Path

import httpx

from app.core.config import get_settings

OUT_DIR = Path(__file__).resolve().parents[1] / "frontend" / "img"

STYLE = (
    "Polished 2D flat vector illustration in the style of a modern, friendly language-learning app: "
    "soft gradients, subtle shading, rounded shapes, clean edges, rich purple (#5b3f9a to #b79cff), "
    "coral (#f6665c), cream (#fff1dc) and small mint and yellow accents, a few small sparkles. "
    "No text, no letters, no logos, no watermark."
)
WOMAN = "a friendly young woman with long dark wavy hair"

PROMPTS: dict[str, tuple[str, str]] = {
    "hero-learner": ("1:1", f"{WOMAN} wearing over-ear lilac headphones, eyes closed, gentle smile, chin resting on her hand, holding a coral-pink smoothie cup with a straw, lavender sweater, big purple leaves behind her. Plain soft lavender background."),
    "mascot": ("1:1", "A cute smoothie cup mascot: coral-pink cup, cream lid, bendy straw, happy kawaii face with blushing cheeks, lilac headphones, small sparkles. Centered on a plain soft lavender background."),
    "scene-travel": ("16:9", "A young traveller with a backpack walking a winding path through green hills toward purple mountains, golden sun, light clouds."),
    "scene-work": ("16:9", f"{WOMAN} working on a laptop at a kitchen table at home, a window with a view, a potted plant, a mug, warm cosy light."),
    "scene-nature": ("16:9", "Volunteers of different ages cleaning a sunny beach with bags, a little boy gently carrying a starfish to the sea, blue water, green plants."),
    "scene-city": ("16:9", "A friendly old stone clock tower in a town square at sunset, a bakery, a grandfather and a child sitting on the steps sharing bread, warm peach sky."),
    "scene-kitchen": ("16:9", "A young person learning to cook at a bright kitchen counter, steaming pot, colourful vegetables, phone propped up playing a recipe video."),
    "scene-study": ("16:9", "A language classroom where two friendly students study together at a desk with books, a lamp and headphones, a teacher smiling in the background."),
}


def request(client: httpx.Client, url: str, payload: dict, retries: int = 3) -> httpx.Response:
    for attempt in range(retries + 1):
        response = client.post(url, json=payload)
        quota = "perday" in response.text.lower().replace(" ", "")
        if response.status_code in (429, 503) and attempt < retries and not quota:
            wait = 20 * (attempt + 1)
            print(f"  busy or rate limited ({response.status_code}); waiting {wait}s…")
            time.sleep(wait)
            continue
        return response
    return response  # pragma: no cover


def generate(client: httpx.Client, base: str, model: str, name: str, ratio: str, prompt: str, ref: Path | None) -> bytes | None:
    text = f"{STYLE}\n\nSubject: {prompt}"
    parts: list[dict] = [{"text": text}]
    if ref:
        mime = mimetypes.guess_type(ref.name)[0] or "image/png"
        parts = [{"inlineData": {"mimeType": mime, "data": base64.b64encode(ref.read_bytes()).decode()}},
                 {"text": "Match the visual style (colours, shading, line quality) of the reference image, but draw a new picture; do not copy its layout, characters or text.\n\n" + text}]
    url = f"{base}/models/{model}:generateContent"
    config = {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": ratio}}
    response = request(client, url, {"contents": [{"role": "user", "parts": parts}], "generationConfig": config})
    if response.status_code == 400 and "imageConfig" in response.text:  # older models: no aspect ratio option
        config.pop("imageConfig")
        response = request(client, url, {"contents": [{"role": "user", "parts": parts}], "generationConfig": config})
    if response.status_code != 200:
        try:
            message = response.json().get("error", {}).get("message", "")
        except ValueError:
            message = ""
        print(f"  FAILED ({response.status_code}): {message or response.text[:200]}")
        return None
    for candidate in response.json().get("candidates", []):
        for part in (candidate.get("content") or {}).get("parts", []):
            data = (part.get("inlineData") or part.get("inline_data") or {}).get("data")
            if data:
                return base64.b64decode(data)
    print("  FAILED: the model returned no image (it may have refused the prompt). Try again.")
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", action="append", choices=sorted(PROMPTS), help="make just this image (repeatable)")
    ap.add_argument("--force", action="store_true", help="overwrite existing images")
    ap.add_argument("--model", default="gemini-2.5-flash-image")
    ap.add_argument("--style-ref", type=Path, help="an image whose look should be copied")
    args = ap.parse_args()

    settings = get_settings()
    key = settings.gemini_api_key.strip()
    if not key:
        print("GEMINI_API_KEY is empty. Put your key in .env first.")
        return 1
    if args.style_ref and not args.style_ref.is_file():
        print(f"Style reference not found: {args.style_ref}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = args.only or list(PROMPTS)
    made = failed = 0
    with httpx.Client(headers={"x-goog-api-key": key}, timeout=180.0) as client:
        for name in names:
            target = OUT_DIR / f"{name}.png"
            if target.exists() and not args.force:
                print(f"{name}: already exists (use --force to redo)")
                continue
            print(f"{name}: generating with {args.model}…")
            ratio, prompt = PROMPTS[name]
            try:
                image = generate(client, settings.gemini_base_url.rstrip("/"), args.model, name, ratio, prompt, args.style_ref)
            except httpx.HTTPError as exc:
                print(f"  could not reach Gemini: {exc}")
                return 1
            if image:
                target.write_bytes(image)
                made += 1
                print(f"  saved {target}")
            else:
                failed += 1
            time.sleep(4)
    print(f"\nDone: {made} created, {failed} failed. Refresh the site to see them.")
    return 1 if failed and not made else 0


if __name__ == "__main__":
    sys.exit(main())
