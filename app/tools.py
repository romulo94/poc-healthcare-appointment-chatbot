"""LangChain tools for patient and appointment operations"""

from langchain_core.tools import tool
from app.database import DB_CONN


@tool
def verify_patient(full_name: str, phone_number: str, date_of_birth: str) -> dict:
    """Verify patient in database"""
    cursor = DB_CONN.cursor()
    cursor.execute(
        "SELECT id, full_name FROM patients WHERE full_name = ? AND phone_number = ? AND date_of_birth = ?",
        (full_name, phone_number, date_of_birth),
    )
    result = cursor.fetchone()
    return (
        {"verified": True, "user_id": result[0], "name": result[1]}
        if result
        else {"verified": False}
    )


@tool
def get_appointments(patient_id: int) -> list:
    """Get patient appointments"""
    cursor = DB_CONN.cursor()
    cursor.execute(
        "SELECT id, appointment_date, appointment_time, doctor_name, appointment_type, status FROM appointments WHERE patient_id = ?",
        (patient_id,),
    )
    return [
        {
            "id": row[0],
            "date": row[1],
            "time": row[2],
            "doctor": row[3],
            "type": row[4],
            "status": row[5],
        }
        for row in cursor.fetchall()
    ]


@tool
def update_appointment_status(appointment_id: int, status: str) -> dict:
    """Update appointment status"""
    cursor = DB_CONN.cursor()
    cursor.execute(
        "UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id)
    )
    DB_CONN.commit()
    return {"success": True, "appointment_id": appointment_id, "new_status": status}
