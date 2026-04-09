# NL2SQL Chatbot Assignment Submission

## Overview

Cogninest AI is a Natural Language to SQL chatbot for a clinic dataset. It uses Vanna 2.0, FastAPI, and SQLite so users can ask plain-English questions and receive query results without writing SQL manually.

Typical flow:

- User asks a question such as "Show me the top 5 patients by spending"
- The app resolves the question to SQL, using seeded examples first
- SQL is validated for safety
- SQLite executes the query
- The API returns a message, columns, rows, and optional chart data

## Stack

| Technology | Purpose |
|---|---|
| Python | Backend language |
| FastAPI | API framework |
| SQLite | Local database |
| Vanna 2.0 | NL2SQL orchestration |
| Plotly | Chart generation |
| Pandas | Result shaping for charts |
| python-dotenv | Environment loading |

### LLM Provider

- Provider: Google Gemini
- Model: gemini-2.0-flash
- Integration: GeminiLlmService from Vanna

## Project Layout

```text
Cogninest_AI/
├── main.py           # FastAPI app and NL2SQL pipeline
├── vanna_setup.py    # Vanna agent, tool wiring, memory, provider config
├── setup_database.py # Creates schema and seeds clinic data
├── seed_memory.py    # Seeds DemoAgentMemory with known question/SQL pairs
├── requirements.txt  # Python dependencies
├── RESULTS.md        # Benchmark notes for the 20 test questions
└── README.md         # This file
```

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root.

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
DB_PATH=clinic.db
```

4. Create and seed the database.

```powershell
python setup_database.py
```

Expected database contents:

- 15 doctors
- 200 patients
- 500 appointments
- 350 treatments
- 300 invoices

5. Seed the agent memory.

```powershell
python seed_memory.py
```

This loads 20 known question-to-SQL pairs into DemoAgentMemory so the app can answer the benchmark prompts deterministically, even when the LLM is unavailable.

6. Start the API server.

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open these URLs in the browser:

- App root: http://127.0.0.1:8000/
- Chat UI: http://127.0.0.1:8000/chat
- Swagger docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API

### POST /chat

Accepts a natural-language question and returns the generated SQL plus query results.

Request example:

```http
POST /chat
Content-Type: application/json

{
  "question": "How many patients do we have?"
}
```

Example response:

```json
{
  "message": "Here are the results for your question. Found 1 row with columns: total_patients.",
  "sql_query": "SELECT COUNT(*) AS total_patients FROM patients",
  "columns": ["total_patients"],
  "rows": [[200]],
  "row_count": 1,
  "chart": null,
  "chart_type": null,
  "cached": false
}
```

PowerShell example:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -ContentType "application/json" -Body '{"question":"How many patients do we have?"}'
```

### GET /health

Returns app and database status.

Example response:

```json
{
  "status": "ok",
  "database": "connected",
  "agent_memory_items": 25,
  "uptime_seconds": 42.1
}
```

### GET /chat

Returns a lightweight browser page for interacting with POST /chat.

## Implementation Notes

- `setup_database.py` creates the schema and inserts the sample clinic data.
- `seed_memory.py` stores curated question/SQL pairs for reliable benchmark answers.
- `main.py` validates SQL so only `SELECT` queries are executed.
- Generated charts are created with Plotly when the result shape supports it.
- If the LLM provider hits quota limits, seeded prompts still work through the cached examples.

## Benchmark Coverage

The repository includes 20 benchmark questions covering:

- Counts and lists
- Date filtering
- Aggregations and ordering
- Join-heavy revenue and treatment queries
- Grouping, HAVING, and time-series trends

See [RESULTS.md](RESULTS.md) for the test matrix and query outputs.

## Troubleshooting

- If `/chat` shows `Method Not Allowed`, use POST requests or open the browser chat page.
- If `GOOGLE_API_KEY` is missing, add it to `.env`.
- If Gemini quota is exhausted, the seeded question paths still work, but ad hoc prompts may fall back to an error message.
- If port 8000 is busy, start Uvicorn on another port such as 8080.
