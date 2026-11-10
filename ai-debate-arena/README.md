# AI Debate Arena

A small, responsive web app that sends one task to OpenAI and Google Gemini, collects independent answers, cross-reviews them, and asks an impartial judge to synthesize a final result.

## What it does

### Full debate (default)
1. ChatGPT and Gemini independently answer the same prompt.
2. ChatGPT reviews Gemini's answer.
3. Gemini reviews ChatGPT's answer.
4. ChatGPT acts as the final judge and produces a synthesis, agreement points, valid criticisms, and unresolved points.

This uses **five model API calls** per full debate. The app deliberately uses one review pass to keep API costs controlled. Quick comparison uses three calls.

> The judge is another model call, not a guaranteed objective authority. For high-stakes topics, verify claims independently.

## Requirements

- Python 3.10+
- An OpenAI API key with API billing enabled
- A Google Gemini API key from Google AI Studio

A ChatGPT or Google AI subscription does not automatically include API credits. API usage is billed separately by each provider.

## Run on Windows

Open PowerShell in the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Add your API keys to `.env`. Check the model IDs against the models available to your API accounts. The default Gemini model is `gemini-3.6-flash`; change `GEMINI_MODEL` if your Google AI Studio account does not offer it. Change `OPENAI_MODEL` to a model enabled for your OpenAI API account.

Start the server:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add API keys and supported model IDs.
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Cost controls

Edit `.env`:

```env
MAX_OUTPUT_TOKENS=1200
MAX_INPUT_CHARS=12000
```

- Choose **Quick comparison** to use three calls (two answers + one judge), skipping cross-review.
- Choose **Full debate** for five calls.
- Use concise prompts and avoid pasting huge files.
- Lower `MAX_OUTPUT_TOKENS` to reduce output usage.
- Model prices vary; check each provider's current API pricing before use.

## Project layout

```text
ai-debate-arena/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Security notes

- Never commit `.env` or expose API keys in frontend JavaScript.
- Keep the app bound to localhost while developing.
- Before public deployment, add authentication, rate limiting, CSRF/origin protections, usage quotas, and HTTPS.
- Do not expose this development server directly to the public internet.
- SQLite stores prompts and model outputs locally in `arena.db`. Treat that file as potentially sensitive.
- The app does not execute generated code. Review and test code in a sandbox before running it.

## API endpoints

- `GET /api/health` - health check
- `POST /api/debate` - run a debate; JSON body: `{"prompt":"...", "mode":"full"}`
- `GET /api/history` - list recent debates
- `GET /api/history/{id}` - retrieve one debate

## Troubleshooting

- **503 / missing API keys:** confirm `.env` exists in the project root and restart Uvicorn.
- **401 / authentication:** check the provider key and account.
- **model not found / access denied:** set the model environment variable to a model ID enabled for your API account.
- **429 / rate limit or quota:** check provider billing, usage limits, and rate limits.


## Windows native-DLL policy error

This build calls the Google Gemini generateContent API directly over HTTPS using Python's standard library, so it does not import the Gemini SDK or its `jiter` native extension. It does not disable Windows security policy. After extracting this fixed build, reinstall dependencies and run Uvicorn without auto-reload first.
