import os
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from openai import OpenAI
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = ROOT / "arena.db"
STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1200"))
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "12000"))

app = FastAPI(title="AI Debate Arena", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class DebateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=MAX_INPUT_CHARS)
    mode: str = Field(default="full", pattern="^(full|quick)$")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS debates (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                prompt TEXT NOT NULL,
                openai_answer TEXT,
                gemini_answer TEXT,
                openai_review TEXT,
                gemini_review TEXT,
                verdict TEXT,
                status TEXT NOT NULL
            )
        """)
        # Upgrade an existing database created by the earlier Claude version.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(debates)")}
        if "gemini_answer" not in columns:
            conn.execute("ALTER TABLE debates ADD COLUMN gemini_answer TEXT")
        if "gemini_review" not in columns:
            conn.execute("ALTER TABLE debates ADD COLUMN gemini_review TEXT")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


def get_clients():
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not openai_key or not gemini_key:
        raise HTTPException(
            status_code=503,
            detail="Add OPENAI_API_KEY and GEMINI_API_KEY to your .env file, then restart the server."
        )
    return OpenAI(api_key=openai_key), gemini_key


def ask_openai(client, system_prompt: str, user_prompt: str) -> str:
    model = os.getenv("OPENAI_MODEL", "gpt-6")
    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    return (response.output_text or "").strip()


def ask_gemini(api_key, system_prompt: str, user_prompt: str) -> str:
    # Use Google's REST API via the standard library; no extra SDK/native DLL required.
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS},
    }).encode("utf-8")
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=payload,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {detail or 'Request rejected.'}") from None
    except URLError as exc:
        raise RuntimeError(f"Could not connect to Gemini API: {exc.reason}") from None
    parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    answer = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    if not answer:
        raise RuntimeError("Gemini returned no text. Check GEMINI_MODEL and API access.")
    return answer

def save_debate(debate_id: str, prompt: str, fields: dict, status: str):
    with db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO debates
            (id, created_at, prompt, openai_answer, gemini_answer,
             openai_review, gemini_review, verdict, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            debate_id, datetime.now(timezone.utc).isoformat(), prompt,
            fields.get("openai_answer"), fields.get("gemini_answer"),
            fields.get("openai_review"), fields.get("gemini_review"),
            fields.get("verdict"), status
        ))


@app.post("/api/debate")
def debate(req: DebateRequest):
    prompt = req.prompt.strip()
    if len(prompt) < 3:
        raise HTTPException(status_code=400, detail="Please enter a more specific task.")

    openai_client, gemini_client = get_clients()
    debate_id = str(uuid.uuid4())
    results = {
        "openai_answer": "", "gemini_answer": "",
        "openai_review": "", "gemini_review": "", "verdict": ""
    }
    save_debate(debate_id, prompt, results, "running")

    try:
        base_system = (
            "You are an expert assistant. Solve the user's task carefully. "
            "Be explicit about assumptions, uncertainty, and limitations. "
            "Do not invent facts, sources, test results, or capabilities. "
            "Give a useful, structured answer."
        )

        # Stage 1: independent first answers.
        results["openai_answer"] = ask_openai(
            openai_client, base_system,
            "Solve this independently. Do not assume another AI has answered.\n\nTASK:\n" + prompt
        )
        results["gemini_answer"] = ask_gemini(
            gemini_client, base_system,
            "Solve this independently. Do not assume another AI has answered.\n\nTASK:\n" + prompt
        )

        if req.mode == "full":
            # Stage 2: each model reviews the other's answer.
            review_system = (
                "You are a rigorous but fair reviewer. Identify concrete errors, "
                "unsupported claims, omissions, security risks, and better alternatives. "
                "Do not disagree just to disagree. Separate critical issues from preferences."
            )
            results["openai_review"] = ask_openai(
                openai_client, review_system,
                f"TASK:\n{prompt}\n\nGEMINI'S ANSWER:\n{results['gemini_answer']}\n\n"
                "Review Gemini's answer. Give specific, actionable criticism."
            )
            results["gemini_review"] = ask_gemini(
                gemini_client, review_system,
                f"TASK:\n{prompt}\n\nCHATGPT'S ANSWER:\n{results['openai_answer']}\n\n"
                "Review ChatGPT's answer. Give specific, actionable criticism."
            )

        # Stage 3: final judge. Use OpenAI as default judge to avoid another model call.
        judge_system = (
            "You are the final impartial judge in an AI debate. Evaluate correctness, "
            "relevance, completeness, clarity, and practical usefulness. Do not choose "
            "a winner based on brand. Resolve disagreements using reasoning and evidence. "
            "If neither answer is fully reliable, say so. Produce one coherent final answer, "
            "then briefly explain the strongest points, valid criticisms, and unresolved uncertainty."
        )
        judge_input = (
            f"USER TASK:\n{prompt}\n\n"
            f"CHATGPT INITIAL ANSWER:\n{results['openai_answer']}\n\n"
            f"GEMINI INITIAL ANSWER:\n{results['gemini_answer']}\n\n"
            f"CHATGPT REVIEW OF GEMINI:\n{results['openai_review'] or 'Not requested'}\n\n"
            f"GEMINI REVIEW OF CHATGPT:\n{results['gemini_review'] or 'Not requested'}\n\n"
            "Return sections: FINAL ANSWER, WHERE THEY AGREE, VALID CRITICISMS, "
            "UNRESOLVED POINTS. Do not claim code was executed or facts were verified unless evidence is provided."
        )
        results["verdict"] = ask_openai(openai_client, judge_system, judge_input)
        save_debate(debate_id, prompt, results, "completed")
        return {"id": debate_id, "status": "completed", **results}

    except HTTPException:
        raise
    except Exception as exc:
        save_debate(debate_id, prompt, results, "failed")
        # Avoid returning secrets or full provider error payloads to the browser.
        raise HTTPException(
            status_code=502,
            detail=f"An AI provider request failed ({type(exc).__name__}). Check your API keys, model names, account access, and provider billing."
        )


@app.get("/api/history")
def history():
    with db() as conn:
        rows = conn.execute("""
            SELECT id, created_at, prompt, status
            FROM debates ORDER BY created_at DESC LIMIT 50
        """).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/history/{debate_id}")
def get_history_item(debate_id: str):
    with db() as conn:
        row = conn.execute("SELECT * FROM debates WHERE id = ?", (debate_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Debate not found.")
    return dict(row)


@app.get("/api/health")
def health():
    return {"ok": True, "app": "AI Debate Arena"}
