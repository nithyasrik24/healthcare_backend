from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Appointment, Doctor
from sqlalchemy import desc

router = APIRouter(prefix="/appointment", tags=["Appointment"])


# ================= DATABASE =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# 1️⃣ PATIENT REQUEST APPOINTMENT
# ============================================
@router.post("/request")
def request_appointment(
    patient_id: str = Form(...),
    doctor_id: str = Form(...),
    consultation_type: str = Form(...),
    reason: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    db: Session = Depends(get_db)
):

    new_appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        consultation_type=consultation_type,
        reason=reason,
        date=date,
        time=time,
        status="Pending"
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return {
        "message": "Appointment request sent",
        "appointment_id": new_appointment.id,
        "status": new_appointment.status
    }


# ============================================
# 2️⃣ DOCTOR ACCEPT APPOINTMENT
# ============================================
@router.put("/accept/{appointment_id}")
def accept_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "Confirmed"
    db.commit()

    return {
        "message": "Appointment accepted",
        "status": appointment.status
    }


# ============================================
# 3️⃣ DOCTOR REJECT APPOINTMENT
# ============================================
@router.put("/reject/{appointment_id}")
def reject_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "Rejected"
    db.commit()

    return {
        "message": "Appointment rejected",
        "status": appointment.status
    }


# ============================================
# 4️⃣ GET ALL PATIENT APPOINTMENTS
# ============================================
@router.get("/patient/{patient_id}")
def get_patient_appointments(
    patient_id: str,
    db: Session = Depends(get_db)
):

    appointments = db.query(Appointment)\
        .filter(Appointment.patient_id == patient_id)\
        .order_by(desc(Appointment.id))\
        .all()

    result = []

    for a in appointments:

        doctor = db.query(Doctor).filter(
            Doctor.doctor_id == a.doctor_id
        ).first()

        result.append({
            "appointment_id": a.id,
            "doctor_name": doctor.full_name if doctor else "-",
            "consultation_type": a.consultation_type if a.consultation_type else "-",
            "date": a.date,
            "time": a.time,
            "status": a.status,
            "reason": a.reason
        })

    return result


# ============================================
# 5️⃣ GET DOCTOR APPOINTMENTS
# ============================================
@router.get("/doctor/{doctor_id}")
def get_doctor_appointments(
    doctor_id: str,
    db: Session = Depends(get_db)
):

    appointments = db.query(Appointment)\
        .filter(Appointment.doctor_id == doctor_id)\
        .order_by(desc(Appointment.id))\
        .all()

    result = []

    for a in appointments:

        result.append({
            "appointment_id": a.id,
            "patient_id": a.patient_id,
            "consultation_type": a.consultation_type,
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    return result


# ============================================
# 6️⃣ GET LATEST APPOINTMENT (Dashboard)
# ============================================
@router.get("/patient-latest/{patient_id}")
def get_patient_latest_appointment(
    patient_id: str,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment)\
        .filter(Appointment.patient_id == patient_id)\
        .order_by(desc(Appointment.id))\
        .first()

    if not appointment:
        return {"has_appointment": False}

    doctor = db.query(Doctor)\
        .filter(Doctor.doctor_id == appointment.doctor_id)\
        .first()

    return {
        "has_appointment": True,
        "doctor_name": doctor.full_name if doctor else "-",
        "doctor_id": appointment.doctor_id,
        "consultation_type": appointment.consultation_type if appointment.consultation_type else "-",
        "date": appointment.date,
        "time": appointment.time,
        "status": appointment.status
    }

