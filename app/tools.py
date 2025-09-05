"""LangChain tools for patient and appointment operations"""

from langchain_core.tools import tool
from app.database import DB_CONN


@tool
def verify_patient(full_name: str, phone_number: str, date_of_birth: str) -> str:
    """Verify patient in database. 
    
    Args:
        full_name: Patient's full name
        phone_number: Phone number
        date_of_birth: Date of birth in format YYYY-MM-DD (e.g., 1985-03-15)
    """
    cursor = DB_CONN.cursor()
    cursor.execute(
        "SELECT id, full_name FROM patients WHERE full_name = ? AND phone_number = ? AND date_of_birth = ?",
        (full_name, phone_number, date_of_birth),
    )
    result = cursor.fetchone()
    
    if result:
        return f"Patient verified successfully! Name: {result[1]}, ID: {result[0]}. You can now help them manage their appointments."
    else:
        return "Patient not found in our system. Please check the information or contact the office to register."


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
