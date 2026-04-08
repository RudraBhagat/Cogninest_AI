"""
main.py
FastAPI NL2SQL application.

Endpoints:
  POST /chat   – ask a question in plain English, get SQL + results + chart
  GET  /health – system health check

Run:
  uvicorn main:app --reload --port 8000
"""

import asyncio
import hashlib
import logging
import os
import re
import sqlite3
import time
from functools import lru_cache
from typing import Any

import plotly
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

try:
    from seed_memory import QA_PAIRS
except Exception:
    QA_PAIRS = []

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "clinic.db")
_SEED_SQL_BY_QUESTION = {
    pair["question"].strip().lower(): pair["sql"] for pair in QA_PAIRS
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("nl2sql")

# ─── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class ChatResponse(BaseModel):
    message: str
    sql_query: str | None = None
    columns: list[str] | None = None
    rows: list[list[Any]] | None = None
    row_count: int | None = None
    chart: dict | None = None
    chart_type: str | None = None
    cached: bool = False


class HealthResponse(BaseModel):
    status: str
    database: str
    agent_memory_items: int
    uptime_seconds: float


# ─── SQL Validation ────────────────────────────────────────────────────────────

_DANGEROUS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|"
    r"EXEC|EXECUTE|GRANT|REVOKE|SHUTDOWN|xp_|sp_)\b",
    re.IGNORECASE,
)
_SYSTEM_TABLES = re.compile(
    r"\b(sqlite_master|sqlite_sequence|information_schema|pg_catalog)\b",
    re.IGNORECASE,
)


def validate_sql(sql: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    if _DANGEROUS.search(sql):
        return False, "Query contains a disallowed keyword."
    if _SYSTEM_TABLES.search(sql):
        return False, "Queries against system tables are not allowed."
    return True, ""


# ─── Database helper ───────────────────────────────────────────────────────────

def run_sql(sql: str) -> tuple[list[str], list[list[Any]]]:
    """Execute a validated SELECT query and return (columns, rows)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = [list(row) for row in cur.fetchall()]
        return columns, rows
    finally:
        conn.close()


def count_memory_items() -> int:
    try:
        from vanna_setup import get_agent
        agent = get_agent()
        memory = getattr(agent, "agent_memory", None)
        if memory is None:
            return 0
        items = getattr(memory, "_memories", None)
        if isinstance(items, list):
            return len(items)
        return 0
    except Exception:
        return 0


# ─── Chart generation ─────────────────────────────────────────────────────────

def generate_chart(columns: list[str], rows: list[list[Any]]) -> tuple[dict | None, str | None]:
    """Try to produce a Plotly chart from query results."""
    if not rows or len(columns) < 2:
        return None, None
    try:
        df = pd.DataFrame(rows, columns=columns)
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols     = [c for c in df.columns if c not in numeric_cols]

        if not numeric_cols:
            return None, None

        x_col = cat_cols[0] if cat_cols else columns[0]
        y_col = numeric_cols[0]

        if len(df) <= 15:
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            chart_type = "bar"
        else:
            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
            chart_type = "line"

        chart_dict = plotly.io.to_json(fig, validate=False)
        import json
        return json.loads(chart_dict), chart_type
    except Exception as e:
        log.warning(f"Chart generation failed: {e}")
        return None, None


# ─── Simple in-memory cache ────────────────────────────────────────────────────

_cache: dict[str, ChatResponse] = {}
MAX_CACHE = 200


def cache_key(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode()).hexdigest()


# ─── Rate limiting (simple token bucket per IP) ───────────────────────────────

_rate: dict[str, list[float]] = {}
RATE_LIMIT = 10       # requests
RATE_WINDOW = 60.0    # seconds


def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    bucket = _rate.get(client_ip, [])
    bucket = [t for t in bucket if now - t < RATE_WINDOW]
    if len(bucket) >= RATE_LIMIT:
        return False
    bucket.append(now)
    _rate[client_ip] = bucket
    return True


# ─── Core NL2SQL pipeline ──────────────────────────────────────────────────────

async def nl_to_sql_and_run(question: str) -> ChatResponse:
    """Main pipeline: question → SQL → validate → execute → chart → response."""
    from vanna_setup import get_agent

    log.info(f"Question: {question!r}")

    seeded_sql = _SEED_SQL_BY_QUESTION.get(question.strip().lower())
    if seeded_sql:
        log.info("Using seeded SQL fallback")
        return await _execute_sql_response(question, seeded_sql)

    agent = get_agent()

    # 1. Ask the agent for a SQL query
    try:
        response_parts = []
        from vanna.core.user import User, RequestContext

        request_context = RequestContext(
            request_id=str(time.time_ns()),
            user=User(id="default", name="Clinic User"),
            metadata={},
        )
        async for part in agent.send_message(request_context, question):
            response_parts.append(part)
    except Exception as exc:
        log.error(f"Agent error: {exc}")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")

    # 2. Extract SQL from agent response
    sql = _extract_sql(response_parts)
    if not sql:
        return ChatResponse(message="I could not generate a SQL query for that question.", sql_query=None)

    return await _execute_sql_response(question, sql)


async def _execute_sql_response(question: str, sql: str) -> ChatResponse:
    """Validate, execute, and format a SQL response."""

    log.info(f"Generated SQL: {sql}")

    # 3. Validate SQL
    valid, err = validate_sql(sql)
    if not valid:
        log.warning(f"SQL validation failed: {err}")
        return ChatResponse(
            message=f"The generated query was rejected for safety reasons: {err}",
            sql_query=sql,
        )

    # 4. Execute
    try:
        columns, rows = run_sql(sql)
    except sqlite3.Error as exc:
        log.error(f"DB error: {exc}")
        return ChatResponse(
            message=f"Database error: {exc}",
            sql_query=sql,
        )

    if not rows:
        return ChatResponse(
            message="No data found for your question.",
            sql_query=sql,
            columns=columns,
            rows=[],
            row_count=0,
        )

    # 5. Chart
    chart, chart_type = generate_chart(columns, rows)

    # 6. Summary message
    summary = _make_summary(question, columns, rows)

    return ChatResponse(
        message=summary,
        sql_query=sql,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        chart=chart,
        chart_type=chart_type,
    )


def _extract_sql(response: Any) -> str | None:
    """Pull the SQL string out of whatever the agent returned."""
    if isinstance(response, list):
        for item in response:
            sql = _extract_sql(item)
            if sql:
                return sql
        return None

    if isinstance(response, str):
        # Look for ```sql ... ``` block
        m = re.search(r"```sql\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # Maybe the whole string is SQL
        stripped = response.strip()
        if stripped.upper().startswith("SELECT"):
            return stripped
        return None

    # If agent returns a structured object
    if hasattr(response, "sql"):
        return response.sql
    if hasattr(response, "tool_args") and isinstance(response.tool_args, dict):
        return response.tool_args.get("sql")
    if isinstance(response, dict):
        return response.get("sql") or response.get("query")

    return None


def _make_summary(question: str, columns: list[str], rows: list[list[Any]]) -> str:
    n = len(rows)
    if n == 1 and len(columns) == 1:
        return f"Result: {rows[0][0]}"
    return (
        f"Here are the results for your question. "
        f"Found {n} row{'s' if n != 1 else ''} with columns: {', '.join(columns)}."
    )


# ─── FastAPI app ───────────────────────────────────────────────────────────────

_start_time = time.time()

app = FastAPI(
    title="NL2SQL Clinic API",
    description="Ask questions in plain English; get SQL results from the clinic database.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    """
    Convert a natural-language question to SQL, execute it, and return results.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment before trying again.",
        )

    # Input validation (beyond pydantic min_length)
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Cache lookup
    key = cache_key(question)
    if key in _cache:
        log.info("Cache hit")
        cached_resp = _cache[key].model_copy()
        cached_resp.cached = True
        return cached_resp

    result = await nl_to_sql_and_run(question)

    # Store in cache (simple LRU eviction)
    if len(_cache) >= MAX_CACHE:
        oldest = next(iter(_cache))
        del _cache[oldest]
    _cache[key] = result

    return result


@app.get("/chat", include_in_schema=False)
async def chat_page():
        return HTMLResponse(
                """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NL2SQL Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }
        .card { max-width: 760px; margin: 0 auto; background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; }
        textarea { width: 100%; min-height: 120px; margin: 1rem 0; padding: 0.75rem; border-radius: 10px; border: 1px solid #475569; background: #0b1220; color: #e2e8f0; }
        button { background: #38bdf8; color: #082f49; border: 0; padding: 0.75rem 1rem; border-radius: 999px; font-weight: 700; cursor: pointer; }
        pre { white-space: pre-wrap; background: #0b1220; padding: 1rem; border-radius: 12px; border: 1px solid #334155; overflow: auto; }
        a { color: #7dd3fc; }
    </style>
</head>
<body>
    <div class="card">
        <h1>NL2SQL Chat</h1>
        <p>Type a question about the clinic data and click Ask. Example: <strong>How many patients do we have?</strong></p>
        <textarea id="question" placeholder="Ask a question..."></textarea>
        <button id="ask">Ask</button>
        <p>API docs: <a href="/docs">/docs</a></p>
        <pre id="result">Ready.</pre>
    </div>
    <script>
        const askButton = document.getElementById('ask');
        const questionInput = document.getElementById('question');
        const resultBox = document.getElementById('result');

        askButton.addEventListener('click', async () => {
            const question = questionInput.value.trim();
            if (!question) {
                resultBox.textContent = 'Enter a question first.';
                return;
            }
            resultBox.textContent = 'Loading...';
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question })
                });
                const data = await response.json();
                resultBox.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultBox.textContent = 'Request failed: ' + error;
            }
        });
    </script>
</body>
</html>"""
        )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Check database connectivity and agent memory status."""
    # Check DB
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "error"

    mem_items = count_memory_items()

    return HealthResponse(
        status="ok",
        database=db_status,
        agent_memory_items=mem_items,
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.get("/")
async def root():
    return {
        "service": "NL2SQL Clinic API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Ask a question",
            "GET /health": "System health",
            "GET /docs": "Swagger UI",
        },
    }
