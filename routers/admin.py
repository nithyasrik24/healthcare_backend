from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from models import Patient, Doctor, Appointment, Report

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# ================= DATABASE =================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# ADMIN DASHBOARD SUMMARY
# =========================================================

@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db)):

    total_patients = db.query(func.count(Patient.patient_id)).scalar()
    total_doctors = db.query(func.count(Doctor.doctor_id)).scalar()
    total_appointments = db.query(func.count(Appointment.id)).scalar()

    high_risk_patients = db.query(func.count(Patient.patient_id)).filter(
        Patient.risk_level == "High"
    ).scalar()

    pending_doctors = db.query(func.count(Doctor.doctor_id)).filter(
        Doctor.is_approved == False
    ).scalar()

    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments,
        "high_risk_patients": high_risk_patients,
        "pending_doctors": pending_doctors
    }


# =========================================================
# MANAGE PATIENTS
# =========================================================

@router.get("/patients")
def list_patients(db: Session = Depends(get_db)):

    patients = db.query(Patient).all()
    result = []

    for p in patients:

        report_count = db.query(func.count(Report.id)).filter(
            Report.patient_id == p.patient_id
        ).scalar()

        result.append({
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "email": p.email,
            "risk_level": p.risk_level if p.risk_level else "-",
            "health_score": p.health_score if p.health_score else "-",
            "report_count": report_count
        })

    return result


# =========================================================
# EMERGENCY PATIENTS
# =========================================================

@router.get("/emergency-patients")
def get_emergency_patients(db: Session = Depends(get_db)):

    patients = db.query(Patient).filter(
        Patient.risk_level == "High"
    ).all()

    result = []

    for p in patients:
        result.append({
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "risk_level": p.risk_level,
            "predicted_disease": p.predicted_disease,
            "health_score": p.health_score
        })

    return result


# =========================================================
# MANAGE DOCTORS
# =========================================================

@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):

    doctors = db.query(Doctor).all()

    return [
        {
            "doctor_id": d.doctor_id,
            "full_name": d.full_name,
            "specialization": d.specialization,
            "hospital_name": d.hospital_name,
            "email": d.email,
            "is_approved": d.is_approved,

            # 🔥 ADD THIS
            "license_file": d.license_file,
            "degree_file": d.degree_file,
            "govt_id_file": d.govt_id_file
        }
        for d in doctors
    ]


# =========================================================
# ALL APPOINTMENTS
# =========================================================

@router.get("/appointments")
def list_appointments(db: Session = Depends(get_db)):

    appointments = db.query(Appointment).all()
    result = []

    for a in appointments:

        patient = db.query(Patient).filter(
            Patient.patient_id == a.patient_id
        ).first()

        doctor = db.query(Doctor).filter(
            Doctor.doctor_id == a.doctor_id
        ).first()

        result.append({
            "appointment_id": a.id,
            "patient_name": patient.full_name if patient else a.patient_id,
            "doctor_name": doctor.full_name if doctor else a.doctor_id,
            "consultation_type": a.consultation_type if a.consultation_type else "-",
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    return result


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

@router.put("/cancel-appointment/{appointment_id}")
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "Cancelled"
    db.commit()

    return {"message": "Appointment cancelled successfully"}


# =========================================================
# VIEW APPOINTMENT DETAILS
# =========================================================

@router.get("/appointment/{appointment_id}")
def appointment_details(appointment_id: int, db: Session = Depends(get_db)):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = db.query(Patient).filter(
        Patient.patient_id == appointment.patient_id
    ).first()

    doctor = db.query(Doctor).filter(
        Doctor.doctor_id == appointment.doctor_id
    ).first()

    return {
        "patient_name": patient.full_name if patient else "",
        "doctor_name": doctor.full_name if doctor else "",
        "consultation_type": appointment.consultation_type,
        "date": appointment.date,
        "time": appointment.time,
        "status": appointment.status,
        "reason": appointment.reason
    }


# =========================================================
# SEND REMINDER
# =========================================================

@router.post("/send-reminder/{appointment_id}")
def send_reminder(appointment_id: int):

    return {
        "message": "Reminder sent to patient successfully"
    }


# =========================================================
# ALL REPORTS
# =========================================================

@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):

    reports = db.query(Report).all()
    result = []

    for r in reports:

        patient = db.query(Patient).filter(
            Patient.patient_id == r.patient_id
        ).first()

        result.append({
            "report_id": r.id,
            "patient_name": patient.full_name if patient else "Unknown",
            "predicted_disease": r.predicted_disease,
            "report_type": r.report_type,
            "risk_level": r.risk_level,
            "health_score": r.health_score,
            "test_date": r.test_date,
            "file_url": f"http://192.168.0.156:8000/{r.file_path}"
        })

    return result


# =========================================================
# AI MONITORING
# =========================================================

@router.get("/ai-monitoring")
def ai_monitoring(db: Session = Depends(get_db)):

    high = db.query(func.count(Patient.patient_id)).filter(
        Patient.risk_level == "High"
    ).scalar()

    moderate = db.query(func.count(Patient.patient_id)).filter(
        Patient.risk_level == "Moderate"
    ).scalar()

    low = db.query(func.count(Patient.patient_id)).filter(
        Patient.risk_level == "Low"
    ).scalar()

    return {
        "high_risk": high,
        "moderate_risk": moderate,
        "low_risk": low
    }

@router.get("/emergency-alerts")
def emergency_alerts(db: Session = Depends(get_db)):

    reports = db.query(Report).filter(
        Report.risk_level == "High"
    ).all()

    result = []

    for r in reports:

        patient = db.query(Patient).filter(
            Patient.patient_id == r.patient_id
        ).first()

        result.append({
            "patient_name": patient.full_name if patient else "-",
            "reason": r.predicted_disease,
            "risk_score": r.health_score,
            "time": r.test_date
        })

    return result

# =========================================================
# APPROVE DOCTOR
# =========================================================

@router.put("/approve-doctor/{doctor_id}")
def approve_doctor(doctor_id: str, db: Session = Depends(get_db)):

    doctor = db.query(Doctor).filter(
        Doctor.doctor_id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_approved = True
    db.commit()

    return {"message": "Doctor approved successfully"}


# =========================================================
# REJECT DOCTOR
# =========================================================

@router.delete("/reject-doctor/{doctor_id}")
def reject_doctor(doctor_id: str, db: Session = Depends(get_db)):

    doctor = db.query(Doctor).filter(
        Doctor.doctor_id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db.delete(doctor)
    db.commit()

    return {"message": "Doctor rejected and removed"}

# =========================================================
# DELETE PATIENT
# =========================================================

@router.delete("/delete-patient/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):

    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db.delete(patient)
    db.commit()

    return {"message": "Patient deleted successfully"}

# =========================================================
# DELETE APPOINTMENT
# =========================================================

@router.delete("/delete-appointment/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db.delete(appointment)
    db.commit()

    return {"message": "Appointment deleted"}