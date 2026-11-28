"""List the Gemini models your API key can use, and check that Google is reachable from here.

    python -m app.gemini_models

Copy a name from the list (without the "models/" prefix) into GEMINI_MODEL in .env.
"""

import sys

import httpx

from app.core.config import get_settings


def main() -> int:
    settings = get_settings()
    key = settings.gemini_api_key.strip()
    if not key:
        print("GEMINI_API_KEY is empty. Create a key at https://aistudio.google.com/apikey and put it in .env.")
        return 1

    url = f"{settings.gemini_base_url.rstrip('/')}/models"
    try:
        response = httpx.get(url, params={"pageSize": 100}, headers={"x-goog-api-key": key}, timeout=20.0)
    except httpx.HTTPError as exc:
        print(f"Could not reach the Gemini API: {exc}")
        print("Check your internet connection and any proxy settings.")
        return 1

    if response.status_code != 200:
        try:
            message = response.json().get("error", {}).get("message", "")
        except ValueError:
            message = ""
        print(f"Google answered with HTTP {response.status_code}: {message or response.text[:200]}")
        return 1

    names = sorted(
        m["name"].removeprefix("models/")
        for m in response.json().get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    )
    print(f"Models that support generateContent ({len(names)}):")
    for name in names:
        marker = "  <- current GEMINI_MODEL" if name == settings.gemini_model else ""
        print(f"  {name}{marker}")
    if settings.gemini_model not in names:
        print(f"\nNote: GEMINI_MODEL={settings.gemini_model!r} is not in this list. Pick one from above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
