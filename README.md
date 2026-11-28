# Smoothies: IELTS Speaking Coach 🎯

An AI-powered backend for personalised IELTS Speaking practice: question banks for all three parts, AI-generated questions and sample answers, criterion-based answer evaluation, grammar and vocabulary analysis, and progress tracking.

Built with **FastAPI**, **SQLAlchemy 2 + PostgreSQL**, **Alembic**, **Pydantic**, **JWT auth**, and a local LLM (**Qwen3 via Ollama**).

> **Scope of the current version.** Learners submit the *text* of what they said (a transcript). Audio recording and pronunciation assessment are planned for a later phase. Because pronunciation is one of the four official criteria, the band returned is a **provisional text-based estimate** from three criteria (Fluency & Coherence, Lexical Resource, Grammatical Range & Accuracy). It is practice feedback, not an official IELTS result.

## Features

| Area | What it does |
|---|---|
| Practice | Question bank for Parts 1, 2 (cue cards) and 3 by topic · random question · AI-generated questions · AI sample answers calibrated to a target band · examiner-style follow-up questions |
| Evaluation | Scores for the 3 text-assessable criteria, strengths and improvements per criterion, provisional overall band, an improved version of the answer |
| Grammar | Errors with corrections, explanations and a category · well-used structures recognised |
| Vocabulary | Collocations, idioms, phrasal verbs and words extracted from answers (used + suggested upgrades) · a personal notebook · AI topic word lists |
| Personalisation | Recurring weaknesses (weakest criterion, most frequent grammar categories) · AI-generated targeted exercises and weekly routine |
| Dashboard | Totals, average/best/latest band, trend over time, weaknesses, recent sessions |

## Quick start

### Option A: Docker (API + PostgreSQL)

```bash
ollama pull qwen3:8b          # on your host; or use the bundled Ollama service, see below
cp .env.example .env          # optional for local use
docker compose up --build
```

Open **http://localhost:8000/docs** for the interactive API docs. Migrations and the starter question bank are applied automatically on start.

To run Ollama in Docker too: `docker compose --profile ollama up --build`, then `docker compose exec ollama ollama pull qwen3:8b`, and set `OLLAMA_BASE_URL=http://ollama:11434` in `.env`.

### Option B: local development

Requires Python 3.11+, PostgreSQL and Ollama.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # then edit DATABASE_URL / SECRET_KEY
ollama pull qwen3:8b

alembic upgrade head            # create tables
python -m app.seed              # load starter questions (safe to re-run)
uvicorn app.main:app --reload
```

Check that the model is reachable: `GET /health/ai` returns `{"reachable": true, "model_available": true, ...}`.

## Web interface

The product is called **Smoothies**. The API serves the whole website (no Node, npm or CDN needed; it is plain HTML, CSS and JavaScript in `frontend/`):

- **http://localhost:8000/** is the front page, with the animated word-smoothie hero.
- **http://localhost:8000/app/** is the practice app (sign up, practise, dashboard).

The look is a purple-and-coral flat-illustration theme. Colours live as variables at the top of `frontend/css/styles.css`; the front page is `frontend/index.html` with `css/landing.css`, and the animation is `js/smoothie.js`.

- **Practice**: pick a part and topic, get a random or AI-generated question, type or paste what you said, and get your answer back *marked*: each grammar error struck through with the correction beside it, plus criterion scores, vocabulary and a stronger version of the answer. Also a sample answer at any band, and follow-up questions.
- **Dashboard**: band trend against your target, criterion averages, recurring mistakes, recent sessions.
- **History**, **Vocabulary** (notebook and AI topic lists), **Insights** (weaknesses, every correction, an AI practice plan) and **Account** (target band).

To work on the UI, just edit the files in `frontend/` and refresh the browser. The interactive API docs remain at `/docs`.

## Try it

```bash
BASE=http://localhost:8000/api/v1

# 1. Register and log in (the OAuth2 form field is called "username" but takes your e-mail)
curl -X POST $BASE/auth/register -H 'Content-Type: application/json' \
     -d '{"email":"me@example.com","password":"a-long-password","target_band":7}'
TOKEN=$(curl -s -X POST $BASE/auth/login -d 'username=me@example.com&password=a-long-password' \
        | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"

# 2. Get a Part 1 question and open a practice session
curl -H "$AUTH" "$BASE/questions/random?part=1"
curl -X POST -H "$AUTH" -H 'Content-Type: application/json' \
     -d '{"part":1,"topic":"Hometown"}' $BASE/practice/sessions

# 3. Submit your answer (transcript) for evaluation. Local models can take a while.
curl -X POST -H "$AUTH" -H 'Content-Type: application/json' \
     -d '{"question_id":1,"answer_text":"I come from a small town near the coast..."}' \
     $BASE/practice/sessions/1/answers

# 4. See your progress and personalised exercises
curl -H "$AUTH" $BASE/dashboard
curl -H "$AUTH" $BASE/learning/recommendations
```

## API overview

All routes are under `/api/v1` and (except register/login) need `Authorization: Bearer <token>`.

| Method & path | Purpose |
|---|---|
| `POST /auth/register` · `POST /auth/login` · `GET/PATCH /auth/me` | Accounts and target band |
| `GET /questions` · `/questions/topics` · `/questions/random` · `/questions/{id}` | Browse the question bank (`part`, `topic`, `q` filters) |
| `POST /questions/generate` | AI-generate and save new questions for a part and topic |
| `POST /practice/sessions` · `GET /practice/sessions` · `GET/DELETE /practice/sessions/{id}` | Practice sessions and history |
| `POST /practice/sessions/{id}/answers` | Submit an answer transcript: evaluate and save |
| `POST /practice/sample-answer` | Model answer for a question at a target band |
| `POST /practice/follow-up` | Examiner-style follow-up questions |
| `GET /learning/vocabulary` · `DELETE /learning/vocabulary/{id}` | Personal vocabulary notebook |
| `POST /learning/topic-vocabulary` | AI topic word list (optionally saved to the notebook) |
| `GET /learning/grammar-issues` | Every grammar issue found, filterable by category |
| `GET /learning/weaknesses` | Recurring weaknesses (no AI call) |
| `GET /learning/recommendations` | AI exercises and weekly routine from your weaknesses |
| `GET /dashboard` | Progress overview |
| `GET /health` · `GET /health/ai` | Liveness · Ollama reachability and model availability |

## How evaluation works

1. The answer is wrapped in `<transcript>` tags and sent to Qwen3 with a system prompt based on the public IELTS band descriptors. The prompt tells the model to treat the transcript as data, not instructions.
2. Ollama is given the Pydantic **JSON schema** as `format`, so the output is constrained to the expected structure. If it still fails validation, the client retries once, telling the model what was wrong.
3. **Grounding:** grammar issues and quoted structures must be verbatim excerpts of the learner's answer. Anything the model invented is dropped before saving.
4. Criterion scores are snapped to half bands. The **overall band is computed in code** (mean of the three, rounded the IELTS way: .25 → .5, .75 → next whole band), never taken from the model.
5. The answer, scores, full feedback, grammar issues and vocabulary are saved in one transaction. If the model call fails, nothing is saved.

## Project layout

```
app/
  main.py            FastAPI app, CORS, error handling, health checks
  api/               deps (auth, DB, LLM) and routes (auth, questions, practice, learning, dashboard)
  core/              settings, security (bcrypt + JWT), scoring helpers, errors
  db/                engine/session, declarative base, JSON column type
  models/            SQLAlchemy models
  schemas/           Pydantic request/response models
  ai/                Ollama client, prompts, LLM output schemas, JSON extraction
  services/          evaluation, grounding, vocabulary, progress, questions, learning
  seed.py, seed_data.py   starter question bank (48 original questions)
frontend/            web UI (index.html, css/, js/ with one module per page)
alembic/             migrations
tests/               unit + API tests
```

## Configuration

Set via environment variables or `.env` (see `.env.example`).

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://ielts:ielts@localhost:5432/ielts` | |
| `SECRET_KEY` | placeholder | **Required in production** (≥ 32 random chars; the app refuses to start otherwise). `openssl rand -hex 32` |
| `ENVIRONMENT` | `development` | `development` · `test` · `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | |
| `CORS_ORIGINS` | localhost:3000, localhost:5173 | JSON list |
| `LLM_PROVIDER` | `ollama` | `ollama` or `gemini` |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | empty / `gemini-2.5-flash` | Used when `LLM_PROVIDER=gemini` |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `qwen3:8b` | Any Ollama model that supports structured outputs |
| `OLLAMA_TIMEOUT_SECONDS` | `180` | Raise this on slow hardware |
| `OLLAMA_THINK` | `false` | Qwen3 thinking mode: slower, usually not needed |

## Using Gemini instead of the local model

1. Create a free key at https://aistudio.google.com/apikey.
2. In `.env` set:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-key
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. Run `python -m app.gemini_models` to list the models your key can use, and pick one for `GEMINI_MODEL`.
4. Restart the server and open `/health/ai`; it should report `"provider": "gemini"` and `"model_available": true`.

Set `LLM_PROVIDER=ollama` to switch back at any time.

Notes: the free tier has rate limits (the client retries briefly on 429, but a daily quota error is reported as-is); Google may not offer the API in every country (the check is on the request location, so a key alone does not fix that); on the free tier Google may use submitted content to improve its products, so check their current terms before sending anything private; model names change over time.

## Topic clusters, Story Studio, recording and listening

After updating, run `alembic upgrade head` (adds the `stories` table) and `python -m app.seed` (adds 34 more Part 2 cue cards; existing ones are skipped).

- **Topic clusters** (`app/clusters.py`): 10 themes grouping topics; a topic can sit in several. The Practice page uses them for navigation and related topics.
- **Story Studio**: save real stories, tag them with clusters, see compatible Part 2 cue cards (shared clusters plus shared key words, no AI call) and ask the AI how to adapt a story to a card (`POST /stories/{id}/adapt`).
- **Voice recording**: recorded in the browser and played back locally; audio is never uploaded. The optional "also type what I say" uses the browser's own speech service and may be unavailable in some regions.
- **Listen & learn**: six short illustrated stories (`frontend/js/stories-data.js`) read aloud with the device's text-to-speech.

## Library: your own groups, importing questions, similar questions

Run `alembic upgrade head` again (adds `topic_groups`).

- **My groups**: pick any topics (and later individual questions) to make your own group. Groups appear in the Practice page, and you can generate sample answers for several questions at once.
- **Import questions** (`POST /questions/import`): paste text or open a .txt/.csv/.json file. Headings such as `Part 2` and `Topic: Hometown`, numbered lists and cue cards with bullet points are understood. Duplicates are skipped. The parser is `frontend/js/importer.js` (test: `node frontend/tests/importer.test.mjs`). Only import material you are allowed to use; this project does not include commercial question banks.
- **Similar questions**: questions that ask about the same thing are grouped by shared key words (no AI call). It is lexical, so review groups before relying on them; save a group to My groups with one click.
- Questions you import go into the shared question bank of this installation.

Pictures live in `frontend/img/` (WebP). Replace a file with the same name to change it.

## Strict scoring and reference answers (RAG)

- **Strict scoring** (`SCORING_STRICTNESS=strict`, default): the prompt tells the model to start at band 5, choose the lower band when unsure and cite evidence first. After that, code only ever lowers scores: short answers cap Fluency, the density of verified grammar errors caps Grammar, no criterion may sit more than 1.5 bands above the lowest, and the overall band rounds down to the half band. The UI lists any caps applied. These rules are heuristics from the public descriptors, not official IELTS rules; tune the tables in `app/services/calibration.py`.
- **Reference answers**: put your graded answers in `knowledge/samples/` (see `knowledge/README.md`). Each evaluation retrieves up to 3 of the same part (BM25 on question, topic and answer, preferring different bands) and shows them to the model as calibration. Check with `python -m app.rag_check`.

## Tests

```bash
pytest
```

- Pure unit tests (scoring, schemas, JSON extraction, grounding, seed data) need only `pydantic` and `pytest`.
- The Ollama client tests and the end-to-end API tests (in-memory SQLite + a fake LLM, no Ollama needed) run once the full requirements are installed; they are skipped automatically if a dependency is missing.

## Known limitations and production notes

- **Text-only assessment.** Fluency is judged from the transcript (development, linking, visible hesitation), not from timing, and pronunciation is not assessed. Treat bands as indicative.
- **Model consistency.** A small local model can be generous or inconsistent. Prompts and grounding reduce this but do not remove it; try larger Qwen3 variants for better calibration.
- **Latency.** Evaluation runs synchronously and can take tens of seconds on CPU. The DB connection is released while the model works, but for many concurrent users move evaluation to a background job queue.
- **Abuse protection.** AI endpoints are expensive. Add rate limiting (e.g. at a reverse proxy) before exposing the API publicly.
- Passwords are hashed with bcrypt (pre-hashed with SHA-256 to avoid bcrypt's 72-byte limit). There is no e-mail verification, password reset or token refresh yet.

## Roadmap

- Audio recording and speech-to-text
- Pronunciation assessment and speaking-rate/pause metrics for fluency
- Background evaluation jobs and rate limiting
- Spaced-repetition review for the vocabulary notebook
