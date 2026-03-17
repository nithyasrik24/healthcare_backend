from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Patient, Doctor
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ================= DATABASE =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= LOGIN REQUEST MODEL =================
class LoginRequest(BaseModel):
    user_id: str
    password: str


# ================= LOGIN API =================
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    # ================= PATIENT LOGIN =================
    if data.user_id.startswith("PAT-"):

        user = db.query(Patient).filter(
            Patient.patient_id == data.user_id
        ).first()

        if not user or user.password != data.password:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials"
            )

        return {
            "role": "patient",
            "user_id": user.patient_id,
            "full_name": user.full_name
        }

    # ================= DOCTOR LOGIN =================
    elif data.user_id.startswith("DOC-"):

        user = db.query(Doctor).filter(
            Doctor.doctor_id == data.user_id
        ).first()

        if not user or user.password != data.password:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials"
            )

        # 🔐 ADMIN APPROVAL CHECK
        if not user.is_approved:
            raise HTTPException(
                status_code=403,
                detail="Doctor not approved by admin"
            )

        return {
            "role": "doctor",
            "user_id": user.doctor_id,
            "full_name": user.full_name
        }

    # ================= ADMIN LOGIN =================
    elif data.user_id == "ADMIN":

        # Hardcoded admin credentials (for project)
        if data.password != "admin123":
            raise HTTPException(
                status_code=400,
                detail="Invalid admin credentials"
            )

        return {
            "role": "admin",
            "user_id": "ADMIN",
            "full_name": "System Administrator"
        }

    # ================= INVALID USER =================
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid User ID"
        )