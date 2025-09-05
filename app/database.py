"""Database setup and sample data"""

import sqlite3
from datetime import datetime, timedelta


def setup_database():
    """Setup database with sample data"""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            date_of_birth TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            appointment_type TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled'
        )
    """
    )

    # Sample data
    patients_data = [
        (1, "John Smith", "555-010-1001", "1985-03-15"),
        (2, "Maria Garcia", "555-010-2001", "1990-07-22"),
    ]
    cursor.executemany("INSERT INTO patients VALUES (?, ?, ?, ?)", patients_data)

    # Sample appointments
    base_date = datetime.now() + timedelta(days=1)
    appointments_data = [
        (
            1,
            1,
            (base_date + timedelta(days=0)).strftime("%Y-%m-%d"),
            "09:00",
            "Dr. Anderson",
            "General Checkup",
            "scheduled",
        ),
        (
            2,
            1,
            (base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
            "14:30",
            "Dr. Brown",
            "Blood Test",
            "scheduled",
        ),
        (
            3,
            2,
            (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "10:15",
            "Dr. Wilson",
            "Follow-up",
            "scheduled",
        ),
    ]
    cursor.executemany(
        "INSERT INTO appointments VALUES (?, ?, ?, ?, ?, ?, ?)", appointments_data
    )

    conn.commit()
    return conn


DB_CONN = setup_database()
