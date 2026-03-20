from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import patient, doctor, login
from routers import appointment, admin
from fastapi.staticfiles import StaticFiles
from blockchain import app

import hashlib



app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.mount("/uploads",StaticFiles(directory="uploads"),name="uploads")

@app.get("/")
def root():
    return {"message": "Smart Healthcare Backend Running"}

app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(login.router)
app.include_router(appointment.router)
app.include_router(admin.router)
