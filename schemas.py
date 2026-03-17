from pydantic import BaseModel
from typing import Optional

class PatientCreate(BaseModel):
    email: str
    password: str
    full_name: str
    phone: str
    gender: str
    dob: str

class DoctorCreate(BaseModel):
    full_name: str
    email: str
    mobile: str
    specialization: str
    registration_number: str
    hospital_name: str
    password: str
