from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Doctor, Patient, Appointment, Prescription, Report
from fastapi import Form, UploadFile, File
from schemas import DoctorCreate
from datetime import datetime
import os
import uuid

router = APIRouter(prefix="/doctor", tags=["Doctor"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

    # ================= DATABASE =================
def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def save_file(file: UploadFile):
    if not file:
        return None
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return "/" + file_path

    # =========================================================
    # 👨‍⚕️ REGISTER DOCTOR
    # =========================================================
@router.post("/register")
async def register_doctor(
    full_name: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    password: str = Form(...),
    specialization: str = Form(...),
    registration_number: str = Form(...),
    hospital_name: str = Form(...),

    license_file: UploadFile = File(None),
    degree_file: UploadFile = File(None),
    govt_id_file: UploadFile = File(None),

    db: Session = Depends(get_db)
):

    existing = db.query(Doctor).filter(
        Doctor.email == email
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    doctor_id = "DOC-" + str(uuid.uuid4())[:8]

    # SAVE FILES
    license_path = save_file(license_file)
    degree_path = save_file(degree_file)
    id_path = save_file(govt_id_file)

    new_doctor = Doctor(
        doctor_id=doctor_id,
        full_name=full_name,
        email=email,
        mobile=mobile,
        password=password,
        specialization=specialization,
        registration_number=registration_number,
        hospital_name=hospital_name,

        # 🔥 IMPORTANT
        license_file=license_path,
        degree_file=degree_path,
        govt_id_file=id_path
    )

    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)

    return {
        "message": "Doctor registered successfully",
        "doctor_id": doctor_id
    }


# =========================================================
# 👤 DOCTOR PROFILE
# =========================================================
@router.get("/profile/{doctor_id}")
def get_doctor_profile(doctor_id: str, db: Session = Depends(get_db)):

        doctor = db.query(Doctor).filter(
            Doctor.doctor_id == doctor_id
        ).first()

        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        return {
            "doctor_id": doctor.doctor_id,
            "full_name": doctor.full_name,
            "specialization": doctor.specialization,
            "hospital_name": doctor.hospital_name,
            "email": doctor.email,
            "mobile": doctor.mobile,
            "registration_number": doctor.registration_number
        }


# =========================================================
# 📊 DASHBOARD SUMMARY
# =========================================================
@router.get("/dashboard/{doctor_id}")
def doctor_dashboard(doctor_id: str, db: Session = Depends(get_db)):

        doctor = db.query(Doctor).filter(
            Doctor.doctor_id == doctor_id
        ).first()

        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        today = str(datetime.now().date())

        total_patients = db.query(Appointment)\
            .filter(Appointment.doctor_id == doctor_id)\
            .distinct(Appointment.patient_id)\
            .count()

        today_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == today,
            Appointment.status == "Confirmed"
        ).count()

        pending_requests = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "Pending"
        ).count()

        emergency_cases = db.query(Appointment)\
            .join(Patient, Appointment.patient_id == Patient.patient_id)\
            .filter(
                Appointment.doctor_id == doctor_id,
                Patient.risk_level == "High"
            ).count()

        return {
            "total_patients": total_patients,
            "today_appointments": today_appointments,
            "pending_requests": pending_requests,
            "emergency_cases": emergency_cases
        }

# =========================================================
# ⏳ PENDING APPOINTMENTS
# =========================================================
@router.get("/pending-appointments/{doctor_id}")
def get_pending_appointments(doctor_id: str, db: Session = Depends(get_db)):

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "Pending"
        ).all()

        result = []

        for a in appointments:

            patient = db.query(Patient).filter(
                Patient.patient_id == a.patient_id
            ).first()

            result.append({
                "appointment_id": a.id,
                "patient_name": patient.full_name if patient else "",
                "consultation_type": a.consultation_type,
                "date": a.date,
                "time": a.time,
                "status": a.status
            })

        return result

# =========================================================
# 📅 TODAY CONFIRMED APPOINTMENTS
# =========================================================
@router.get("/today-appointments/{doctor_id}")
def get_today_appointments(doctor_id: str, db: Session = Depends(get_db)):

        today = str(datetime.now().date())

        appointments = db.query(Appointment)\
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == today,
                Appointment.status == "Confirmed"
            ).all()

        result = []

        for a in appointments:
            patient = db.query(Patient).filter(
                Patient.patient_id == a.patient_id
            ).first()

            if patient:
                result.append({
                    "patient_name": patient.full_name,
                    "time": a.time,
                    "consultation_type": a.consultation_type,
                    "risk": patient.risk_level,
                    "disease": patient.predicted_disease
                })

        return result


# =========================================================
# 🚨 EMERGENCY PATIENTS
# =========================================================
@router.get("/emergencies/{doctor_id}")
def emergency_cases(doctor_id: str, db: Session = Depends(get_db)):

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "Confirmed"
    ).all()

    patient_ids = list(set([a.patient_id for a in appointments]))

    reports = db.query(Report).filter(
        Report.patient_id.in_(patient_ids),
        Report.risk_level == "High"
    ).order_by(Report.id.desc()).all()

    result = []

    for r in reports:

        patient = db.query(Patient).filter(
            Patient.patient_id == r.patient_id
        ).first()

        result.append({
            "patient_id": r.patient_id,

            "patient_name": patient.full_name if patient else "-",

            "reason": r.predicted_disease,

            "health_score": r.health_score,

            "time": r.test_date,

            "severity": r.risk_level,

            # 🔬 LAB VALUES
            "glucose": r.glucose,
            "bp": r.bp,
            "cholesterol": r.cholesterol,
            "triglycerides": r.triglycerides,

        })

    return result

    # =========================================================
    # ✅ ACCEPT APPOINTMENT
    # =========================================================
@router.put("/accept/{appointment_id}")
def accept_appointment(appointment_id: int, db: Session = Depends(get_db)):

        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        appointment.status = "Confirmed"
        db.commit()

        return {"message": "Appointment confirmed"}


    # =========================================================
    # ❌ REJECT APPOINTMENT
    # =========================================================
@router.put("/reject/{appointment_id}")
def reject_appointment(appointment_id: int, db: Session = Depends(get_db)):

        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        appointment.status = "Rejected"
        db.commit()

        return {"message": "Appointment rejected"}

    # =========================================================
    # CONFIRMED APPOINTMENTS
    # =========================================================

@router.get("/confirmed-appointments/{doctor_id}")
def confirmed_appointments(doctor_id: str, db: Session = Depends(get_db)):

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "Confirmed"
        ).all()

        result = []

        for a in appointments:

            patient = db.query(Patient).filter(
                Patient.patient_id == a.patient_id
            ).first()

            result.append({
                "appointment_id": a.id,
                "patient_name": patient.full_name if patient else "",
                "consultation_type": a.consultation_type,
                "date": a.date,
                "time": a.time,
                "status": a.status
            })

        return result


    # =========================================================
    # 📋 LIST DOCTORS
    # =========================================================
@router.get("/list")
def list_doctors(db: Session = Depends(get_db)):

        doctors = db.query(Doctor).all()

        return [
            {
                "doctor_id": d.doctor_id,
                "full_name": d.full_name,
                "specialization": d.specialization
            }
            for d in doctors
        ]


    # =========================================================
    # 👨‍⚕️ DOCTOR PATIENT LIST
    # =========================================================
@router.get("/patients/{doctor_id}")
def get_doctor_patients(doctor_id: str, db: Session = Depends(get_db)):

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == "Confirmed"
    ).all()

    result = []

    for a in appointments:

        patient = db.query(Patient).filter(
            Patient.patient_id == a.patient_id
        ).first()

        latest_report = db.query(Report).filter(
            Report.patient_id == a.patient_id
        ).order_by(Report.id.desc()).first()

        age = "-"
        if patient and patient.dob:
            try:
                dob = datetime.fromisoformat(patient.dob)
                age = datetime.now().year - dob.year
            except:
                age = "-"

        result.append({
            "patient_id": patient.patient_id if patient else "-",
            "name": patient.full_name if patient else "-",
            "age": age,
            "disease": latest_report.predicted_disease if latest_report else "-",
            "date": a.date,
            "time": a.time
        })

    return result


    # =========================================================
    # 📄 DOCTOR PATIENT REPORTS
    # =========================================================
@router.get("/reports/{doctor_id}")
def get_doctor_reports(doctor_id: str, db: Session = Depends(get_db)):

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "Confirmed"
        ).all()

        patient_ids = list(set([a.patient_id for a in appointments]))

        reports = db.query(Report).filter(
            Report.patient_id.in_(patient_ids)
        ).order_by(Report.id.desc()).all()

        result = []

        for r in reports:

            patient = db.query(Patient).filter(
                Patient.patient_id == r.patient_id
            ).first()

            result.append({
                "patient_name": patient.full_name if patient else "-",
                "predicted_disease": r.predicted_disease,
                "risk_level": r.risk_level,
                "health_score": r.health_score,
                "test_date": r.test_date,
                "file": f"http://192.168.0.156:8000/{r.file_path}"
            })

        return result


    # =========================================================
    # 💊 ADD PRESCRIPTION
    # =========================================================
@router.post("/prescribe")
def prescribe(
        patient_id: str = Form(...),
        doctor_id: str = Form(...),
        medicine_name: str = Form(...),
        dosage: str = Form(...),
        frequency: str = Form(...),
        duration: str = Form(...),
        time: str = Form(...),
        notes: str = Form(None),
        db: Session = Depends(get_db)
    ):

        prescription = Prescription(
            patient_id=patient_id,
            doctor_id=doctor_id,
            medicine_name=medicine_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            time=time,
            notes=notes,
            is_taken=False
        )

        db.add(prescription)
        db.commit()

        return {"message": "Prescription added successfully"}

    # =========================================================
    # 🧠 AI PREDICTIONS FOR DOCTOR
    # =========================================================
@router.get("/ai-predictions/{doctor_id}")
def get_ai_predictions(doctor_id: str, db: Session = Depends(get_db)):

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "Confirmed"
        ).all()

        patient_ids = list(set([a.patient_id for a in appointments]))

        reports = db.query(Report).filter(
            Report.patient_id.in_(patient_ids)
        ).order_by(Report.id.desc()).all()

        result = []

        for r in reports:

            patient = db.query(Patient).filter(
                Patient.patient_id == r.patient_id
            ).first()

            result.append({
                "patient_name": patient.full_name if patient else "-",
                "predicted_disease": r.predicted_disease,
                "risk_level": r.risk_level,
                "health_score": r.health_score,
                "test_date": r.test_date
            })

        return result

    # =========================================================
    # 🚨 EMERGENCY ALERTS FOR DOCTOR
    # =========================================================
@router.get("/emergencies/{doctor_id}")
def emergency_cases(doctor_id: str, db: Session = Depends(get_db)):

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "Confirmed"
        ).all()

        patient_ids = list(set([a.patient_id for a in appointments]))

        reports = db.query(Report).filter(
            Report.patient_id.in_(patient_ids),
            Report.risk_level == "High"
        ).order_by(Report.id.desc()).all()

        result = []

        for r in reports:

            patient = db.query(Patient).filter(
                Patient.patient_id == r.patient_id
            ).first()

            result.append({
                "patient_name": patient.full_name if patient else "-",
                "reason": r.predicted_disease,
                "risk_score": r.health_score,
                "time": r.test_date,
                "severity": r.risk_level
            })

        return result

    # =========================================================
# 📋 GET PRESCRIPTIONS FOR DOCTOR
# =========================================================
@router.get("/prescriptions/{doctor_id}")
def get_prescriptions(doctor_id: str, db: Session = Depends(get_db)):

    prescriptions = db.query(Prescription).filter(
        Prescription.doctor_id == doctor_id
    ).order_by(Prescription.id.desc()).all()

    result = []

    for p in prescriptions:

        patient = db.query(Patient).filter(
            Patient.patient_id == p.patient_id
        ).first()

        result.append({
            "patient_id": p.patient_id,
            "patient_name": patient.full_name if patient else "-",
            "medicine_name": p.medicine_name,
            "dosage": p.dosage,
            "frequency": p.frequency,
            "duration": p.duration,
            "time": p.time,
            "notes": p.notes
        })

    return result


@router.post("/emergency-appointment")
def create_emergency_appointment(
    doctor_id: str = Form(...),
    patient_id: str = Form(...),
    db: Session = Depends(get_db)
):

    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        consultation_type="Emergency",
        date=str(datetime.now().date()),
        time=str(datetime.now().time())[:5],
        status="Confirmed"
    )

    db.add(appointment)
    db.commit()

    return {"message": "Emergency appointment created"}