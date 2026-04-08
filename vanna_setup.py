"""
vanna_setup.py
Initializes the Vanna 2.0 Agent.
Written against vanna 2.0.2 actual source.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "clinic.db")

# ─── Vanna 2.0 imports ───────────────────────────────────────────────────────

from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
)
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory

# ─── DB Schema (system prompt for the LLM) ───────────────────────────────────

DB_SCHEMA = """
You are a SQL expert working with a clinic management SQLite database.
The database has the following tables:

patients(id, first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
doctors(id, name, specialization, department, phone)
appointments(id, patient_id, doctor_id, appointment_date, status, notes)
  -- status: 'Scheduled' | 'Completed' | 'Cancelled' | 'No-Show'
  -- appointment_date is a DATETIME string like '2024-06-15 10:30:00'
treatments(id, appointment_id, treatment_name, cost, duration_minutes)
invoices(id, patient_id, invoice_date, total_amount, paid_amount, status)
  -- status: 'Paid' | 'Pending' | 'Overdue'

Foreign keys:
  appointments.patient_id -> patients.id
  appointments.doctor_id  -> doctors.id
  treatments.appointment_id -> appointments.id
  invoices.patient_id -> patients.id

Always use strftime() for date operations in SQLite.
For "last month":   strftime('%Y-%m', appointment_date) = strftime('%Y-%m', 'now', '-1 month')
For "last quarter": appointment_date >= date('now', '-3 months')
For "this year":    strftime('%Y', appointment_date) = strftime('%Y', 'now')
Always alias aggregate columns for readability.
Only generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, or ALTER.
"""


# ─── Default user resolver ───────────────────────────────────────────────────

class SingleUserResolver(UserResolver):
    """Maps every request to a single default user."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="default", name="Clinic User")


# ─── LLM factory ─────────────────────────────────────────────────────────────

def _build_llm_service():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from vanna.integrations.google import GeminiLlmService
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY is not set in your .env file.")
        return GeminiLlmService(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            api_key=api_key,
        )

    if provider == "groq":
        from vanna.integrations.openai import OpenAILlmService
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY is not set in your .env file.")
        return OpenAILlmService(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    if provider == "ollama":
        from vanna.integrations.openai import OpenAILlmService
        return OpenAILlmService(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            api_key="ollama",
            base_url="http://localhost:11434/v1",
        )

    raise ValueError(f"Unknown LLM_PROVIDER='{provider}'. Choose: gemini | groq | ollama")


# ─── Agent factory ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_agent() -> Agent:
    """Build and return the singleton Vanna 2.0 Agent."""

    llm_service = _build_llm_service()

    db_runner = SqliteRunner(database_path=DB_PATH)
    memory = DemoAgentMemory()
    run_sql_tool = RunSqlTool(sql_runner=db_runner)

    # SaveQuestionToolArgsTool and SearchSavedCorrectToolUsesTool take no args —
    # memory is wired through AgentConfig, not the tool constructors.
    registry = ToolRegistry()
    registry.register_local_tool(run_sql_tool, [])
    registry.register_local_tool(VisualizeDataTool(), [])
    registry.register_local_tool(SaveQuestionToolArgsTool(), [])
    registry.register_local_tool(SearchSavedCorrectToolUsesTool(), [])

    user_resolver = SingleUserResolver()

    agent = Agent(
        llm_service=llm_service,
        tool_registry=registry,
        user_resolver=user_resolver,
        agent_memory=memory,
    )
    print(f"✅  Vanna 2.0 Agent initialized (provider={os.getenv('LLM_PROVIDER','gemini')})")
    return agent


if __name__ == "__main__":
    agent = get_agent()
    print("Agent ready:", agent)
