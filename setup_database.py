"""
setup_database.py
Creates the clinic.db SQLite database with schema and realistic dummy data.
Run: python setup_database.py
"""

import sqlite3
import random
from datetime import datetime, timedelta, date

DB_PATH = "clinic.db"

# ─── Seed data ────────────────────────────────────────────────────────────────

FIRST_NAMES_M = [
    "Arjun", "Rohan", "Vikram", "Amit", "Suresh", "Raj", "Karan", "Dev",
    "Nikhil", "Aditya", "Sanjay", "Rahul", "Pradeep", "Manish", "Vivek",
    "Deepak", "Ankit", "Gaurav", "Vishal", "Sachin",
]
FIRST_NAMES_F = [
    "Priya", "Anjali", "Sneha", "Pooja", "Meera", "Nisha", "Kavya", "Riya",
    "Divya", "Swati", "Asha", "Rekha", "Sunita", "Geeta", "Lakshmi",
    "Ananya", "Shweta", "Pallavi", "Madhuri", "Rani",
]
LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Singh", "Kumar", "Mehta", "Joshi", "Gupta",
    "Shah", "Yadav", "Tiwari", "Pandey", "Nair", "Reddy", "Rao", "Pillai",
    "Iyer", "Menon", "Khanna", "Malhotra", "Bose", "Das", "Banerjee",
    "Mukherjee", "Chatterjee",
]
CITIES = [
    "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
    "Delhi", "Bangalore", "Hyderabad", "Chennai",
]
DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

DOCTORS = [
    ("Dr. Anjali Sharma",    "Dermatology",  "Skin & Hair"),
    ("Dr. Rohan Mehta",      "Dermatology",  "Skin & Hair"),
    ("Dr. Priya Patel",      "Dermatology",  "Skin & Hair"),
    ("Dr. Vikram Singh",     "Cardiology",   "Heart & Vascular"),
    ("Dr. Sunita Rao",       "Cardiology",   "Heart & Vascular"),
    ("Dr. Aditya Gupta",     "Cardiology",   "Heart & Vascular"),
    ("Dr. Meera Iyer",       "Orthopedics",  "Bone & Joint"),
    ("Dr. Karan Nair",       "Orthopedics",  "Bone & Joint"),
    ("Dr. Deepak Reddy",     "Orthopedics",  "Bone & Joint"),
    ("Dr. Suresh Verma",     "General",      "General Medicine"),
    ("Dr. Riya Joshi",       "General",      "General Medicine"),
    ("Dr. Amit Khanna",      "General",      "General Medicine"),
    ("Dr. Ananya Banerjee",  "Pediatrics",   "Child Health"),
    ("Dr. Rahul Chatterjee", "Pediatrics",   "Child Health"),
    ("Dr. Swati Mukherjee",  "Pediatrics",   "Child Health"),
]

TREATMENTS = {
    "Dermatology":  [("Skin Biopsy",200,30),("Acne Treatment",150,20),("Laser Therapy",500,45),
                     ("Mole Removal",300,25),("Chemical Peel",400,40)],
    "Cardiology":   [("ECG",100,15),("Echocardiogram",800,45),("Stress Test",600,60),
                     ("Holter Monitor",400,20),("Angiography",5000,90)],
    "Orthopedics":  [("X-Ray",150,15),("MRI Scan",1200,60),("Physiotherapy Session",200,45),
                     ("Joint Injection",500,20),("Cast Application",300,30)],
    "General":      [("General Checkup",100,20),("Blood Test",150,10),("Urine Analysis",80,10),
                     ("Vaccination",120,15),("Dressing Change",50,15)],
    "Pediatrics":   [("Child Checkup",120,20),("Growth Assessment",100,20),("Vaccination",100,15),
                     ("Nutritional Counseling",150,30),("Nebulization",200,20)],
}

STATUSES_APPT = ["Scheduled", "Completed", "Cancelled", "No-Show"]
WEIGHTS_APPT  = [0.15, 0.65, 0.12, 0.08]
STATUSES_INV  = ["Paid", "Pending", "Overdue"]
WEIGHTS_INV   = [0.60, 0.25, 0.15]


def rand_date(start_days_ago: int, end_days_ago: int = 0) -> date:
    start = datetime.today() - timedelta(days=start_days_ago)
    end   = datetime.today() - timedelta(days=end_days_ago)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, max(delta, 0)))).date()


def rand_phone():
    return f"+91-{random.randint(7000000000, 9999999999)}"


def create_schema(conn: sqlite3.Connection):
    c = conn.cursor()
    c.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS patients (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name      TEXT NOT NULL,
        last_name       TEXT NOT NULL,
        email           TEXT,
        phone           TEXT,
        date_of_birth   DATE,
        gender          TEXT,
        city            TEXT,
        registered_date DATE
    );

    CREATE TABLE IF NOT EXISTS doctors (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        specialization  TEXT,
        department      TEXT,
        phone           TEXT
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id       INTEGER REFERENCES patients(id),
        doctor_id        INTEGER REFERENCES doctors(id),
        appointment_date DATETIME,
        status           TEXT,
        notes            TEXT
    );

    CREATE TABLE IF NOT EXISTS treatments (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id     INTEGER REFERENCES appointments(id),
        treatment_name     TEXT,
        cost               REAL,
        duration_minutes   INTEGER
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id   INTEGER REFERENCES patients(id),
        invoice_date DATE,
        total_amount REAL,
        paid_amount  REAL,
        status       TEXT
    );
    """)
    conn.commit()


def insert_doctors(conn: sqlite3.Connection) -> list[int]:
    c = conn.cursor()
    ids = []
    for name, spec, dept in DOCTORS:
        phone = rand_phone() if random.random() > 0.1 else None
        c.execute(
            "INSERT INTO doctors(name, specialization, department, phone) VALUES (?,?,?,?)",
            (name, spec, dept, phone),
        )
        ids.append(c.lastrowid)
    conn.commit()
    return ids


def insert_patients(conn: sqlite3.Connection, n: int = 200) -> list[int]:
    c = conn.cursor()
    ids = []
    for _ in range(n):
        gender = random.choice(["M", "F"])
        fname  = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
        lname  = random.choice(LAST_NAMES)
        email  = f"{fname.lower()}.{lname.lower()}{random.randint(1,99)}@{random.choice(DOMAINS)}" \
                 if random.random() > 0.15 else None
        phone  = rand_phone() if random.random() > 0.20 else None
        dob    = rand_date(365 * 70, 365 * 5)     # 5–70 years old
        city   = random.choice(CITIES)
        reg    = rand_date(365, 7)
        c.execute(
            "INSERT INTO patients(first_name,last_name,email,phone,date_of_birth,gender,city,registered_date)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (fname, lname, email, phone, str(dob), gender, city, str(reg)),
        )
        ids.append(c.lastrowid)
    conn.commit()
    return ids


def insert_appointments(
    conn: sqlite3.Connection,
    patient_ids: list[int],
    doctor_ids: list[int],
    n: int = 500,
) -> list[tuple[int, int, str]]:
    """Returns list of (appointment_id, doctor_id, status)."""
    c = conn.cursor()

    # Make some patients repeat visitors (power users)
    heavy_patients = random.sample(patient_ids, k=30)
    weights = [5 if p in heavy_patients else 1 for p in patient_ids]

    # Make some doctors busier
    busy_doctors = random.sample(doctor_ids, k=5)
    doc_weights  = [4 if d in busy_doctors else 1 for d in doctor_ids]

    results = []
    for _ in range(n):
        pid    = random.choices(patient_ids, weights=weights)[0]
        did    = random.choices(doctor_ids, weights=doc_weights)[0]
        appt_dt = rand_date(365)
        hour   = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        appt_dt_str = f"{appt_dt} {hour:02d}:{minute:02d}:00"
        status = random.choices(STATUSES_APPT, weights=WEIGHTS_APPT)[0]
        notes  = random.choice([
            "Follow-up required", "First visit", "Referred by GP",
            "Routine checkup", None, None, None,
        ])
        c.execute(
            "INSERT INTO appointments(patient_id,doctor_id,appointment_date,status,notes)"
            " VALUES (?,?,?,?,?)",
            (pid, did, appt_dt_str, status, notes),
        )
        results.append((c.lastrowid, did, status))

    conn.commit()
    return results


def get_doctor_spec(conn: sqlite3.Connection) -> dict[int, str]:
    c = conn.cursor()
    c.execute("SELECT id, specialization FROM doctors")
    return {row[0]: row[1] for row in c.fetchall()}


def insert_treatments(
    conn: sqlite3.Connection,
    appointments: list[tuple[int, int, str]],
    doc_spec: dict[int, str],
    n: int = 350,
):
    c = conn.cursor()
    completed = [(aid, did, s) for aid, did, s in appointments if s == "Completed"]
    if not completed:
        return

    sample = random.sample(completed, k=min(n, len(completed)))
    if len(sample) < n:
        sample.extend(random.choices(completed, k=n - len(sample)))

    for appt_id, doc_id, _ in sample:
        spec     = doc_spec.get(doc_id, "General")
        options  = TREATMENTS.get(spec, TREATMENTS["General"])
        name, cost, dur = random.choice(options)
        cost_jitter = cost * random.uniform(0.85, 1.15)
        c.execute(
            "INSERT INTO treatments(appointment_id,treatment_name,cost,duration_minutes)"
            " VALUES (?,?,?,?)",
            (appt_id, name, round(cost_jitter, 2), dur + random.randint(-5, 10)),
        )
    conn.commit()


def insert_invoices(
    conn: sqlite3.Connection,
    patient_ids: list[int],
    n: int = 300,
):
    c = conn.cursor()
    sample = random.choices(patient_ids, k=n)
    for pid in sample:
        inv_date  = rand_date(365)
        total     = round(random.uniform(100, 5000), 2)
        status    = random.choices(STATUSES_INV, weights=WEIGHTS_INV)[0]
        if status == "Paid":
            paid = total
        elif status == "Overdue":
            paid = round(total * random.uniform(0, 0.5), 2)
        else:  # Pending
            paid = round(total * random.uniform(0, 0.3), 2)
        c.execute(
            "INSERT INTO invoices(patient_id,invoice_date,total_amount,paid_amount,status)"
            " VALUES (?,?,?,?,?)",
            (pid, str(inv_date), total, paid, status),
        )
    conn.commit()


def print_summary(conn: sqlite3.Connection):
    c = conn.cursor()
    tables = ["patients", "doctors", "appointments", "treatments", "invoices"]
    for t in tables:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {c.fetchone()[0]} rows")


def main():
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    print("Creating schema …")
    create_schema(conn)

    print("Inserting doctors …")
    doctor_ids = insert_doctors(conn)

    print("Inserting patients …")
    patient_ids = insert_patients(conn, 200)

    print("Inserting appointments …")
    appointments = insert_appointments(conn, patient_ids, doctor_ids, 500)

    doc_spec = get_doctor_spec(conn)

    print("Inserting treatments …")
    insert_treatments(conn, appointments, doc_spec, 350)

    print("Inserting invoices …")
    insert_invoices(conn, patient_ids, 300)

    conn.close()
    print(f"\n✅  clinic.db created successfully!")
    print("Summary:")

    conn2 = sqlite3.connect(DB_PATH)
    print_summary(conn2)
    conn2.close()


if __name__ == "__main__":
    random.seed(42)
    main()
