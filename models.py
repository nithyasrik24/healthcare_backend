from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime



# =========================
# PATIENT TABLE
# =========================
class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    gender = Column(String)
    dob = Column(String)

    # Latest health snapshot
    glucose = Column(Integer, nullable=True)
    cholesterol = Column(Integer, nullable=True)
    triglycerides = Column(Integer, nullable=True)
    bp = Column(String, nullable=True)

    predicted_disease = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    health_score = Column(Integer, nullable=True)

    # Relationships
    reports = relationship("Report", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")


# =========================
# DOCTOR TABLE
# =========================
class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    full_name = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    specialization = Column(String)
    registration_number = Column(String)
    hospital_name = Column(String, nullable=False)
    is_approved = Column(Boolean, default=False)  # 👈 ADD THIS

    # Relationships
    appointments = relationship("Appointment", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")


# =========================
# APPOINTMENT TABLE
# =========================
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(String, ForeignKey("patients.patient_id"))
    doctor_id = Column(String, ForeignKey("doctors.doctor_id"))

    doctor_name = Column(String, nullable=True)
    department = Column(String)
    consultation_type = Column(String)

    date = Column(String)
    time = Column(String)
    reason = Column(String)

    status = Column(String, default="Pending")  # Pending / Confirmed / Rejected

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


# =========================
# REPORT TABLE
# =========================
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(String, ForeignKey("patients.patient_id"))

    title = Column(String)
    report_type = Column(String)
    hospital_name = Column(String)
    doctor_name = Column(String)
    test_date = Column(String)

    file_path = Column(String)
    file_hash = Column(String)

    # 🔗 BLOCKCHAIN INFO
    blockchain_tx_hash = Column(String, nullable=True)

    # 🔗 LINK PREVIOUS REPORT
    previous_report_id = Column(Integer, nullable=True)

    # ================= HEALTH PARAMETERS =================
    glucose = Column(Integer, nullable=True)
    bp = Column(String, nullable=True)
    cholesterol = Column(Integer, nullable=True)
    triglycerides = Column(Integer, nullable=True)

    predicted_disease = Column(String)
    risk_level = Column(String)
    health_score = Column(Integer)

    # ================= TREND TRACKING =================
    glucose_trend = Column(String, nullable=True)
    bp_trend = Column(String, nullable=True)
    cholesterol_trend = Column(String, nullable=True)
    triglycerides_trend = Column(String, nullable=True)
    risk_trend = Column(String, nullable=True)

    is_emergency = Column(String, nullable=True)

    # Relationship
    patient = relationship("Patient", back_populates="reports")

# =========================
# PRESCRIPTION TABLE
# =========================
class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"))
    doctor_id = Column(String, ForeignKey("doctors.doctor_id"))
    medicine_name = Column(String)
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    time = Column(String)
    notes = Column(String)
    is_taken = Column(Boolean, default=False)
    taken_at = Column(String, nullable=True)
    created_at = Column(String, default=str(datetime.utcnow()))
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")

