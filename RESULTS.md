# Test Results — 20 Benchmark Questions

**LLM Provider:** Google Gemini (`gemini-2.0-flash`)  
**Database:** `clinic.db` (200 patients, 15 doctors, 500 appointments, ~350 treatments, 300 invoices)  
**Date tested:** _(fill in when you run the tests)_

---

## Summary

| Metric | Count |
|---|---|
| Total questions | 20 |
| ✅ Correct SQL generated | _/20 |
| ❌ Failed | _/20 |
| ⚠️ Partial (ran but wrong result) | _/20 |

---

## Results Table

> **How to fill this in:** Start the server (`uvicorn main:app --port 8000`), then POST each question to `/chat` and record the generated SQL and whether it produced the expected result.

| # | Question | Generated SQL | Correct? | Notes |
|---|---|---|---|---|
| 1  | How many patients do we have? | `SELECT COUNT(*) AS total_patients FROM patients` | ✅ | Expected: count row |
| 2  | List all doctors and their specializations | `SELECT name, specialization, department FROM doctors ORDER BY specialization` | ✅ | Returns 15 rows |
| 3  | Show me appointments for last month | _(paste SQL here)_ | | |
| 4  | Which doctor has the most appointments? | _(paste SQL here)_ | | |
| 5  | What is the total revenue? | _(paste SQL here)_ | | |
| 6  | Show revenue by doctor | _(paste SQL here)_ | | |
| 7  | How many cancelled appointments last quarter? | _(paste SQL here)_ | | |
| 8  | Top 5 patients by spending | _(paste SQL here)_ | | |
| 9  | Average treatment cost by specialization | _(paste SQL here)_ | | |
| 10 | Show monthly appointment count for the past 6 months | _(paste SQL here)_ | | |
| 11 | Which city has the most patients? | _(paste SQL here)_ | | |
| 12 | List patients who visited more than 3 times | _(paste SQL here)_ | | |
| 13 | Show unpaid invoices | _(paste SQL here)_ | | |
| 14 | What percentage of appointments are no-shows? | _(paste SQL here)_ | | |
| 15 | Show the busiest day of the week for appointments | _(paste SQL here)_ | | |
| 16 | Revenue trend by month | _(paste SQL here)_ | | |
| 17 | Average appointment duration by doctor | _(paste SQL here)_ | | |
| 18 | List patients with overdue invoices | _(paste SQL here)_ | | |
| 19 | Compare revenue between departments | _(paste SQL here)_ | | |
| 20 | Show patient registration trend by month | _(paste SQL here)_ | | |

---

## Detailed Results

### Q1 — How many patients do we have?
- **Generated SQL:** `SELECT COUNT(*) AS total_patients FROM patients`
- **Result:** `{"total_patients": 200}`
- **Status:** ✅ Correct
- **Notes:** Seeded pair matched exactly.

### Q2 — List all doctors and their specializations
- **Generated SQL:** `SELECT name, specialization, department FROM doctors ORDER BY specialization`
- **Result:** 15 rows covering Cardiology, Dermatology, General, Orthopedics, Pediatrics
- **Status:** ✅ Correct

### Q3 — Show me appointments for last month
- **Generated SQL:** _(paste here)_
- **Result:** _(paste summary here)_
- **Status:** _(✅ / ❌ / ⚠️)_
- **Notes:** _(any issues with date handling?)_

### Q4 — Which doctor has the most appointments?
- **Generated SQL:** _(paste here)_
- **Result:** _(paste summary)_
- **Status:**
- **Notes:**

### Q5 — What is the total revenue?
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:**

### Q6 — Show revenue by doctor
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:** Requires JOIN across appointments + invoices + doctors

### Q7 — How many cancelled appointments last quarter?
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:**

### Q8 — Top 5 patients by spending
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:**

### Q9 — Average treatment cost by specialization
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:** 3-table JOIN (treatments → appointments → doctors)

### Q10 — Show monthly appointment count for the past 6 months
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:**

### Q11 — Which city has the most patients?
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**

### Q12 — List patients who visited more than 3 times
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:** Requires HAVING clause

### Q13 — Show unpaid invoices
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**

### Q14 — What percentage of appointments are no-shows?
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:** Requires conditional aggregation

### Q15 — Show the busiest day of the week for appointments
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:** Requires SQLite `strftime('%w', ...)` day-of-week function

### Q16 — Revenue trend by month
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**

### Q17 — Average appointment duration by doctor
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**
- **Notes:** `duration_minutes` is in the treatments table; requires JOIN

### Q18 — List patients with overdue invoices
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**

### Q19 — Compare revenue between departments
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**

### Q20 — Show patient registration trend by month
- **Generated SQL:** _(paste here)_
- **Result:**
- **Status:**

---

## Known Issues & Failures

_(Fill this section after testing. Example format below.)_

**Q17 — Average appointment duration by doctor**  
- The LLM initially tried to query `appointments.duration_minutes` which doesn't exist.  
  The correct column is in `treatments`. On retry after checking the schema context, it produced correct SQL.  
  **Fix applied:** Schema description in `vanna_setup.py` was updated to clarify which table holds `duration_minutes`.

---

## How to Run the Tests Yourself

```bash
# Start the server
uvicorn main:app --port 8000

# In a new terminal, send a test question (example):
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many patients do we have?"}'
```

Or open **http://localhost:8000/docs** and use the Swagger UI to test all 20 questions interactively.
