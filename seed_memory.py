"""
seed_memory.py
Pre-seeds the Vanna 2.0 DemoAgentMemory with 20 known-good question-SQL pairs.

DemoAgentMemory.save_tool_usage() requires a ToolContext, so we build a
minimal one here using the real Vanna internals.

Run AFTER setup_database.py:
    python seed_memory.py
"""

import asyncio
import logging
import uuid
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

QA_PAIRS = [
    {
        "question": "How many patients do we have?",
        "sql": "SELECT COUNT(*) AS total_patients FROM patients",
    },
    {
        "question": "List all doctors and their specializations",
        "sql": "SELECT name, specialization, department FROM doctors ORDER BY specialization, name",
    },
    {
        "question": "Show me appointments for last month",
        "sql": "SELECT a.id, p.first_name, p.last_name, d.name AS doctor, a.appointment_date, a.status FROM appointments a JOIN patients p ON p.id = a.patient_id JOIN doctors d ON d.id = a.doctor_id WHERE strftime('%Y-%m', a.appointment_date) = strftime('%Y-%m', 'now', '-1 month') ORDER BY a.appointment_date",
    },
    {
        "question": "Which doctor has the most appointments?",
        "sql": "SELECT d.name, d.specialization, COUNT(a.id) AS appointment_count FROM doctors d JOIN appointments a ON a.doctor_id = d.id GROUP BY d.id ORDER BY appointment_count DESC LIMIT 1",
    },
    {
        "question": "What is the total revenue?",
        "sql": "SELECT SUM(total_amount) AS total_revenue FROM invoices",
    },
    {
        "question": "Show revenue by doctor",
        "sql": "SELECT d.name, d.specialization, SUM(i.total_amount) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.id ORDER BY total_revenue DESC",
    },
    {
        "question": "How many cancelled appointments last quarter?",
        "sql": "SELECT COUNT(*) AS cancelled_count FROM appointments WHERE status = 'Cancelled' AND appointment_date >= date('now', '-3 months')",
    },
    {
        "question": "Top 5 patients by total spending",
        "sql": "SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spending FROM patients p JOIN invoices i ON i.patient_id = p.id GROUP BY p.id ORDER BY total_spending DESC LIMIT 5",
    },
    {
        "question": "Average treatment cost by specialization",
        "sql": "SELECT d.specialization, ROUND(AVG(t.cost), 2) AS avg_treatment_cost FROM treatments t JOIN appointments a ON a.id = t.appointment_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.specialization ORDER BY avg_treatment_cost DESC",
    },
    {
        "question": "Show monthly appointment count for the past 6 months",
        "sql": "SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS appointment_count FROM appointments WHERE appointment_date >= date('now', '-6 months') GROUP BY month ORDER BY month",
    },
    {
        "question": "Which city has the most patients?",
        "sql": "SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1",
    },
    {
        "question": "List patients who visited more than 3 times",
        "sql": "SELECT p.first_name, p.last_name, COUNT(a.id) AS visit_count FROM patients p JOIN appointments a ON a.patient_id = p.id GROUP BY p.id HAVING visit_count > 3 ORDER BY visit_count DESC",
    },
    {
        "question": "Show unpaid invoices",
        "sql": "SELECT i.id, p.first_name, p.last_name, i.invoice_date, i.total_amount, i.paid_amount, i.status FROM invoices i JOIN patients p ON p.id = i.patient_id WHERE i.status IN ('Pending', 'Overdue') ORDER BY i.status, i.invoice_date",
    },
    {
        "question": "What percentage of appointments are no-shows?",
        "sql": "SELECT ROUND(100.0 * SUM(CASE WHEN status = 'No-Show' THEN 1 ELSE 0 END) / COUNT(*), 2) AS no_show_percentage FROM appointments",
    },
    {
        "question": "Show the busiest day of the week for appointments",
        "sql": "SELECT CASE CAST(strftime('%w', appointment_date) AS INTEGER) WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday' END AS day_of_week, COUNT(*) AS appointment_count FROM appointments GROUP BY strftime('%w', appointment_date) ORDER BY appointment_count DESC LIMIT 1",
    },
    {
        "question": "Revenue trend by month",
        "sql": "SELECT strftime('%Y-%m', invoice_date) AS month, ROUND(SUM(total_amount), 2) AS monthly_revenue FROM invoices GROUP BY month ORDER BY month",
    },
    {
        "question": "Average appointment duration by doctor",
        "sql": "SELECT d.name, d.specialization, ROUND(AVG(t.duration_minutes), 2) AS avg_appointment_duration FROM treatments t JOIN appointments a ON a.id = t.appointment_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.id ORDER BY avg_appointment_duration DESC",
    },
    {
        "question": "List patients with overdue invoices",
        "sql": "SELECT p.first_name, p.last_name, i.invoice_date, i.total_amount, i.paid_amount, i.status FROM invoices i JOIN patients p ON p.id = i.patient_id WHERE i.status = 'Overdue' ORDER BY i.invoice_date DESC, i.total_amount DESC",
    },
    {
        "question": "Compare revenue between departments",
        "sql": "SELECT d.department, ROUND(SUM(i.total_amount), 2) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.department ORDER BY total_revenue DESC",
    },
    {
        "question": "Show patient registration trend by month",
        "sql": "SELECT strftime('%Y-%m', registered_date) AS month, COUNT(*) AS new_patients FROM patients GROUP BY month ORDER BY month",
    }
]


async def seed():
    {
        "question": "List patients who visited more than 3 times",
        "sql": "SELECT p.first_name, p.last_name, COUNT(a.id) AS visit_count FROM patients p JOIN appointments a ON a.patient_id = p.id GROUP BY p.id HAVING visit_count > 3 ORDER BY visit_count DESC",
    },
    from vanna.core.user import User, RequestContext
    from vanna.core.tool.models import ToolContext
    from vanna_setup import get_agent

    agent = get_agent()
    memory = agent.agent_memory

    # Build a minimal ToolContext — save_tool_usage needs it but only
    # uses it for metadata; our DemoAgentMemory ignores the context entirely.
    dummy_user = User(id="seed-script", name="Seed Script")
    dummy_request_context = RequestContext(
        request_id=str(uuid.uuid4()),
        user=dummy_user,
        metadata={},
    )
    dummy_tool_context = ToolContext(
        user=dummy_user,
        conversation_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        agent_memory=memory,
        metadata={},
    )

    log.info(f"Seeding {len(QA_PAIRS)} Q&A pairs into DemoAgentMemory …")
    for i, pair in enumerate(QA_PAIRS, 1):
        try:
            await memory.save_tool_usage(
                question=pair["question"],
                tool_name="run_sql",
                args={"sql": pair["sql"]},
                context=dummy_tool_context,
                success=True,
            )
            log.info(f"  [{i:02d}/{len(QA_PAIRS)}] ✓ {pair['question'][:65]}")
        except Exception as exc:
            log.warning(f"  [{i:02d}/{len(QA_PAIRS)}] ✗ {exc}")

    total = len(agent.agent_memory._memories)
    log.info(f"✅  Seeding complete. {total} memories stored.")


if __name__ == "__main__":
    asyncio.run(seed())
