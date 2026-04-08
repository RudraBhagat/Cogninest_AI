# NL2SQL Chatbot Assignment Submission

## About This Project

This project is a working Natural Language to SQL chatbot built for the AI/ML Developer Intern assignment.

It uses Vanna AI 2.0 with FastAPI and SQLite so users can ask questions in plain English and receive query results without writing SQL manually.

Example flow:

- User asks: "Show me the top 5 patients by total spending"
- System generates SQL
- SQL is validated for safety
- SQL runs against SQLite
- API returns summary, rows, and optional chart data

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend language |
| Vanna | 2.0.x | Agent + NL2SQL orchestration |
| FastAPI | Latest | API framework |
| SQLite | Built-in | Database |
| Plotly | Latest | Chart generation |
| Pandas | Latest | Tabular handling for charts |
| python-dotenv | Latest | Env var loading |

### Chosen LLM Provider

- Provider: Google Gemini
- Model: gemini-2.0-flash
- Vanna integration: `from vanna.integrations.google import GeminiLlmService`

## Project Structure

```text
Cogninest_AI/
├── main.py              # FastAPI app and NL2SQL pipeline
├── vanna_setup.py       # Vanna Agent, tools, memory, resolver, provider wiring
├── setup_database.py    # Creates schema and inserts dummy data
├── seed_memory.py       # Seeds DemoAgentMemory with known good Q&A SQL pairs
├── requirements.txt     # Python dependencies
├── RESULTS.md           # Evaluation results for the 20 test questions
└── README.md            # This file
```

## Step-by-Step Setup Instructions

1. Clone or download the repository and enter project directory.

```bash
cd Cogninest_AI
```

2. Create a virtual environment.

```bash
python -m venv .venv
```

3. Activate virtual environment.

```powershell
.venv\Scripts\Activate.ps1
```

4. Install dependencies.

```bash
pip install -r requirements.txt
```

5. Create `.env` in project root and configure provider.

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
DB_PATH=clinic.db
```

6. Create database and seed dummy clinic data.

```bash
python setup_database.py
```

Expected: script creates `clinic.db` and prints table row summary.

## How to Run the Memory Seeding Script

Run:

```bash
python seed_memory.py
```

What it does:

- Initializes Vanna Agent and DemoAgentMemory
- Inserts pre-defined good question-SQL examples
- Covers patient, doctor, appointment, finance, and time-trend patterns

## How to Start the API Server

Run:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open:

- App root: `http://127.0.0.1:8000/`
- Browser chat page: `http://127.0.0.1:8000/chat`
- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Documentation

### POST /chat

Accepts natural language question and returns SQL + results.

Request:

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
  "message": "Result: 200",
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

Checks app and DB status.

Example response:

```json
{
  "status": "ok",
  "database": "connected",
  "agent_memory_items": 20,
  "uptime_seconds": 42.1
}
```

### GET /chat

Returns a lightweight HTML page for browser-based interaction with POST /chat.

## Architecture Overview (Brief)

```text
User Question (English)
        |
        v
   FastAPI Backend (main.py)
        |
        v
   Vanna 2.0 Agent (vanna_setup.py)
   - GeminiLlmService
   - ToolRegistry
   - RunSqlTool
   - VisualizeDataTool
   - SaveQuestionToolArgsTool
   - SearchSavedCorrectToolUsesTool
   - DemoAgentMemory
        |
        v
   SQL Validation
   - SELECT only
   - Reject dangerous/system-table queries
        |
        v
   SQLite Execution (clinic.db)
        |
        v
   Response Formatter
   - message summary
   - sql_query
   - columns/rows/row_count
   - optional chart payload
```

## Requirement Mapping (Assignment Checklist)

- SQLite schema + dummy data: implemented in `setup_database.py`
- 15 doctors, 200 patients, 500 appointments, 350 treatments, 300 invoices: implemented
- Vanna 2.0 Agent setup: implemented in `vanna_setup.py`
- DemoAgentMemory seeding with 15+ Q&A pairs: implemented in `seed_memory.py`
- FastAPI endpoints (`/chat`, `/health`): implemented in `main.py`
- SQL safety validation (SELECT-only + dangerous keyword filtering): implemented
- Error handling for invalid SQL / DB failures / empty results: implemented
- Documentation and reproducible run steps: provided in this README
- 20-question evaluation: documented in `RESULTS.md`

## Evaluation Notes

The assignment asks for both successful behavior and honest reporting of failures.

- For known seeded patterns, responses are deterministic and reliable.
- For non-seeded NL prompts, output quality depends on LLM provider availability/quota.
- If provider quota is exhausted, check seeded questions or switch to Groq/Ollama.

## Common Troubleshooting

- `Method Not Allowed` on `/chat` in browser:
  - Use `POST /chat` for API calls, or open `GET /chat` web page.
- `GOOGLE_API_KEY` missing:
  - Add key to `.env`.
- Provider quota errors:
  - Wait/reset quota or switch provider to Groq/Ollama.
- `Address already in use` on port 8000:
  - Use another port, e.g. `--port 8080`.
