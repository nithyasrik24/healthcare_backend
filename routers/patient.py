from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import SessionLocal
from models import Patient, Report, Appointment, Doctor, Prescription
from schemas import PatientCreate
from datetime import datetime, timedelta
import joblib
import numpy as np
import uuid
import os
import shutil
import hashlib
import pdfplumber
import re

# Blockchain
from blockchain import store_report_on_blockchain

router = APIRouter(prefix="/patient", tags=["Patient"])

# ================= LOAD MODEL =================
model = joblib.load("health_model.pkl")


# ================= DATABASE =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# REGISTER PATIENT
# =========================================================
@router.post("/register")
def register_patient(patient: PatientCreate, db: Session = Depends(get_db)):

    existing = db.query(Patient).filter(
        Patient.email == patient.email
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    patient_id = "PAT-" + str(uuid.uuid4())[:8]

    new_patient = Patient(
        patient_id=patient_id,
        email=patient.email,
        password=patient.password,
        full_name=patient.full_name,
        phone=patient.phone,
        gender=patient.gender,
        dob=patient.dob
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return {
        "patient_id": new_patient.patient_id,
        "full_name": new_patient.full_name
    }


# =========================================================
# PATIENT PROFILE
# =========================================================
@router.get("/profile/{patient_id}")
def get_patient_profile(patient_id: str, db: Session = Depends(get_db)):

    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "full_name": patient.full_name,
        "email": patient.email,
        "phone": patient.phone,
        "gender": patient.gender,
        "dob": patient.dob,
        "bp": patient.bp,
        "glucose": patient.glucose,
        "predicted_disease": patient.predicted_disease,
        "risk_level": patient.risk_level,
        "health_score": patient.health_score
    }


# =========================================================
# PATIENT DASHBOARD
# =========================================================
@router.get("/dashboard/{patient_id}")
def patient_dashboard(patient_id: str, db: Session = Depends(get_db)):

    latest_report = db.query(Report)\
        .filter(Report.patient_id == patient_id)\
        .order_by(desc(Report.id))\
        .first()

    if not latest_report:
        return {"has_report": False}

    return {
        "has_report": True,
        "bp": latest_report.bp,
        "glucose": latest_report.glucose,
        "risk": latest_report.risk_level,
        "health_score": latest_report.health_score,
        "last_report_date": latest_report.test_date
    }


# =========================================================
# UPLOAD REPORT (BLOCKCHAIN + AI)
# =========================================================
@router.post("/upload-report")
async def upload_report(
    patient_id: str = Form(...),
    title: str = Form(...),
    report_type: str = Form(...),
    hospital_name: str = Form(...),
    doctor_name: str = Form(None),
    test_date: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_location = os.path.join(upload_folder, unique_filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ================= HASH FILE =================
    with open(file_location, "rb") as f:
        file_bytes = f.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # ================= STORE HASH ON BLOCKCHAIN =================
    blockchain_tx_hash = store_report_on_blockchain(patient_id, file_hash)

    # ================= PDF TEXT EXTRACTION =================
    full_text = ""
    try:
        with pdfplumber.open(file_location) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text
    except:
        pass

    bp_match = re.search(r"BP[:\s]+(\d+)\s*/\s*(\d+)", full_text, re.IGNORECASE)
    bp = f"{bp_match.group(1)}/{bp_match.group(2)}" if bp_match else None

    def extract_value(pattern):
        match = re.search(pattern, full_text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    glucose = extract_value(r"Glucose[:\s]+(\d+)")
    cholesterol = extract_value(r"Cholesterol[:\s]+(\d+)")
    triglycerides = extract_value(r"Triglycerides[:\s]+(\d+)")

    systolic = int(bp.split("/")[0]) if bp else 0
    diastolic = int(bp.split("/")[1]) if bp else 0

    features = np.array([[systolic, diastolic,
        glucose or 0,
        cholesterol or 0,
        triglycerides or 0]])

    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    classes = model.classes_

    prob_dict = {
        classes[i]: round(float(probabilities[i]) * 100, 2)
        for i in range(len(classes))
    }

    disease = prediction
    max_prob = max(prob_dict.values())

    if max_prob > 70:
        risk = "High"
    elif max_prob > 40:
        risk = "Moderate"
    else:
        risk = "Low"

    score = 100 - int(max_prob * 0.6)

    new_report = Report(
        patient_id=patient_id,
        title=title,
        report_type=report_type,
        hospital_name=hospital_name,
        doctor_name=doctor_name,
        test_date=test_date,
        file_path=file_location,
        file_hash=file_hash,
        blockchain_tx_hash=blockchain_tx_hash,
        bp=bp,
        glucose=glucose,
        cholesterol=cholesterol,
        triglycerides=triglycerides,
        predicted_disease=disease,
        risk_level=risk,
        health_score=score
    )

    db.add(new_report)

    patient.predicted_disease = disease
    patient.risk_level = risk
    patient.health_score = score
    patient.bp = bp
    patient.glucose = glucose

    db.commit()

    return {
        "message": "Report uploaded successfully",
        "blockchain_tx_hash": blockchain_tx_hash
    }


# =========================================================
# GET PATIENT REPORTS
# =========================================================
@router.get("/reports/{patient_id}")
def get_patient_reports(patient_id: str, db: Session = Depends(get_db)):

    reports = db.query(Report).filter(
        Report.patient_id == patient_id
    ).all()

    return [
        {
            "report_id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "hospital_name": r.hospital_name,
            "test_date": r.test_date,
            "file_url": f"http://192.168.0.156:8000/uploads/{os.path.basename(r.file_path)}"
        }
        for r in reports
    ]


# =========================================================
# DELETE REPORT
# =========================================================
@router.delete("/report/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):

    report = db.query(Report).filter(
        Report.id == report_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)

    db.delete(report)
    db.commit()

    return {"message": "Report deleted successfully"}

# =========================================================
# 📅 ALL PATIENT APPOINTMENTS
# =========================================================
@router.get("/appointments/{patient_id}")
def patient_appointments(patient_id: str, db: Session = Depends(get_db)):

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(desc(Appointment.id)).all()

    if not appointments:
        return []

    result = []

    for a in appointments:

        doctor = db.query(Doctor).filter(
            Doctor.doctor_id == a.doctor_id
        ).first()

        result.append({
            "appointment_id": a.id,
            "doctor_name": doctor.full_name if doctor else "-",
            "consultation_type": a.consultation_type,
            "date": a.date,
            "time": a.time,
            "status": a.status,
            "reason": a.reason
        })

    return result

# =========================================================
# AI PREDICTION
# =========================================================
@router.get("/ai-prediction/{patient_id}")
def ai_prediction(patient_id: str, db: Session = Depends(get_db)):

    # Get latest report
    report = db.query(Report)\
        .filter(Report.patient_id == patient_id)\
        .order_by(desc(Report.id))\
        .first()

    # If patient has no report
    if not report:
        return {
            "has_data": False
        }

    # Convert test date
    try:
        test_date = datetime.strptime(report.test_date, "%Y-%m-%d")
    except:
        test_date = datetime.now()

    # Decide next test date based on risk level
    if report.risk_level == "High":
        next_test = test_date + timedelta(days=7)
        recommendation = "Immediate doctor consultation recommended."
    elif report.risk_level == "Moderate":
        next_test = test_date + timedelta(days=30)
        recommendation = "Improve diet and schedule follow-up check."
    else:
        next_test = test_date + timedelta(days=45)
        recommendation = "Maintain healthy lifestyle and routine monitoring."

    return {
        "has_data": True,
        "bp": report.bp,
        "glucose": report.glucose,
        "risk_level": report.risk_level,
        "disease": report.predicted_disease,
        "recommendation": recommendation,
        "next_test_date": next_test.strftime("%Y-%m-%d"),
        "health_score": report.health_score
    }