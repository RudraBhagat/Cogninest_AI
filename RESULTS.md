# Test Results - 20 Benchmark Questions

LLM Provider: Google Gemini (gemini-2.0-flash)
Database: clinic.db (200 patients, 15 doctors, 500 appointments, 350 treatments, 300 invoices)
Date tested: 2026-04-08

## Summary

| Metric | Count |
|---|---:|
| Total questions | 20 |
| Correct | 20 |
| Partial | 0 |
| Failed | 0 |

Pass rate: 20/20 (100%)

## Results Table

| # | Question | Generated SQL | Correct? | Result summary |
|---|---|---|---|---|
| 1 | How many patients do we have? | SELECT COUNT(*) AS total_patients FROM patients | Yes | 1 row, total_patients=200 |
| 2 | List all doctors and their specializations | SELECT name, specialization, department FROM doctors ORDER BY specialization, name | Yes | 15 rows |
| 3 | Show me appointments for last month | SELECT a.id, p.first_name, p.last_name, d.name AS doctor, a.appointment_date, a.status FROM appointments a JOIN patients p ON p.id = a.patient_id JOIN doctors d ON d.id = a.doctor_id WHERE strftime('%Y-%m', a.appointment_date) = strftime('%Y-%m', 'now', '-1 month') ORDER BY a.appointment_date | Yes | 46 rows |
| 4 | Which doctor has the most appointments? | SELECT d.name, d.specialization, COUNT(a.id) AS appointment_count FROM doctors d JOIN appointments a ON a.doctor_id = d.id GROUP BY d.id ORDER BY appointment_count DESC LIMIT 1 | Yes | 1 row |
| 5 | What is the total revenue? | SELECT SUM(total_amount) AS total_revenue FROM invoices | Yes | 1 row, total_revenue=773041.59 |
| 6 | Show revenue by doctor | SELECT d.name, d.specialization, SUM(i.total_amount) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.id ORDER BY total_revenue DESC | Yes | 15 rows |
| 7 | How many cancelled appointments last quarter? | SELECT COUNT(*) AS cancelled_count FROM appointments WHERE status = 'Cancelled' AND appointment_date >= date('now', '-3 months')", | Yes | cancelled_count = 8 |
| 8 | Top 5 patients by total spending | SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spending FROM patients p JOIN invoices i ON i.patient_id = p.id GROUP BY p.id ORDER BY total_spending DESC LIMIT 5" | Yes | 5 rows |
| 9 | Average treatment cost by specialization | SELECT d.specialization, ROUND(AVG(t.cost), 2) AS avg_treatment_cost FROM treatments t JOIN appointments a ON a.id = t.appointment_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.specialization ORDER BY avg_treatment_cost DESC | Yes | 5 rows |
| 10 | Show monthly appointment count for the past 6 months | SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS appointment_count FROM appointments WHERE appointment_date >= date('now', '-6 months') GROUP BY month ORDER BY month | Yes | 7 rows |
| 11 | Which city has the most patients? | SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1 | Yes | 1 row, city=Pune |
| 12 | List patients who visited more than 3 times | SELECT p.first_name, p.last_name, COUNT(a.id) AS visit_count FROM patients p JOIN appointments a ON a.patient_id = p.id GROUP BY p.id HAVING visit_count > 3 ORDER BY visit_count DESC | Yes | 35 rows |
| 13 | Show unpaid invoices | SELECT i.id, p.first_name, p.last_name, i.invoice_date, i.total_amount, i.paid_amount, i.status FROM invoices i JOIN patients p ON p.id = i.patient_id WHERE i.status IN ('Pending', 'Overdue') ORDER BY i.status, i.invoice_date | Yes | 114 rows |
| 14 | What percentage of appointments are no-shows? | SELECT ROUND(100.0 * SUM(CASE WHEN status = 'No-Show' THEN 1 ELSE 0 END) / COUNT(*), 2) AS no_show_percentage FROM appointments | Yes | 1 row, no_show_percentage=6.6 |
| 15 | Show the busiest day of the week for appointments | SELECT CASE CAST(strftime('%w', appointment_date) AS INTEGER) WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday' END AS day_of_week, COUNT(*) AS appointment_count FROM appointments GROUP BY strftime('%w', appointment_date) ORDER BY appointment_count DESC LIMIT 1 | Yes | 1 row, day_of_week=Wednesday |
| 16 | Revenue trend by month | SELECT strftime('%Y-%m', invoice_date) AS month, ROUND(SUM(total_amount), 2) AS monthly_revenue FROM invoices GROUP BY month ORDER BY month | Yes | 13 rows |
| 17 | Average appointment duration by doctor | SELECT d.name, d.specialization, ROUND(AVG(t.duration_minutes), 2) AS avg_appointment_duration FROM treatments t JOIN appointments a ON a.id = t.appointment_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.id ORDER BY avg_appointment_duration DESC | Yes | 15 rows |
| 18 | List patients with overdue invoices | SELECT p.first_name, p.last_name, i.invoice_date, i.total_amount, i.paid_amount, i.status FROM invoices i JOIN patients p ON p.id = i.patient_id WHERE i.status = 'Overdue' ORDER BY i.invoice_date DESC, i.total_amount DESC | Yes | 47 rows |
| 19 | Compare revenue between departments | SELECT d.department, ROUND(SUM(i.total_amount), 2) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.department ORDER BY total_revenue DESC | Yes | 5 rows |
| 20 | Show patient registration trend by month | SELECT strftime('%Y-%m', registered_date) AS month, COUNT(*) AS new_patients FROM patients GROUP BY month ORDER BY month | Yes | 13 rows |

## Reproduction Commands

Start server:

uvicorn main:app --host 127.0.0.1 --port 8000 --reload

Example test call:

Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -ContentType "application/json" -Body '{"question":"How many patients do we have?"}'
