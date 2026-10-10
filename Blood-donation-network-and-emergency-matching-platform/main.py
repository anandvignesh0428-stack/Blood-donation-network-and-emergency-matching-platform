from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
from schemas import DonorCreate, EmergencyRequestCreate


try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


BLOOD_COMPATIBILITY = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    "AB-": ["A-", "B-", "AB-", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"],
}


def normalize_blood_group(bg: str) -> str:
    return bg.strip().upper()


def validate_blood_group(bg: str) -> str:
    normalized = normalize_blood_group(bg)
    if normalized not in BLOOD_COMPATIBILITY:
        raise HTTPException(status_code=400, detail=f"Invalid blood group: {bg}")
    return normalized


app = FastAPI(
    title="Blood Donation Network and Emergency Matching Platform",
    description="A platform to connect blood donors with patients during emergencies.",
    version="1.0.0"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# CREATE DATABASE TABLES
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# HOME PAGE
# =========================

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# DONOR PAGE
# =========================

@app.get("/donor", response_class=HTMLResponse)
def donor_page():
    with open("templates/donor.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# EMERGENCY PAGE
# =========================

@app.get("/emergency", response_class=HTMLResponse)
def emergency_page():
    with open("templates/emergency.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# MATCHING PAGE
# =========================

@app.get("/matching", response_class=HTMLResponse)
def matching_page():
    with open("templates/matching.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================
# VOICE RECOGNITION
# =========================

@app.post("/voice/recognize")
def recognize_voice():
    if not SPEECH_RECOGNITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Speech recognition not available")

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        text = recognizer.recognize_google(audio)
        return {"text": text}
    except sr.WaitTimeoutError:
        raise HTTPException(status_code=408, detail="No speech detected within timeout")
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand the audio")
    except sr.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Speech recognition service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice recognition failed: {e}")


# =========================
# REGISTER DONOR
# =========================

@app.post("/donors")
def create_donor(
    donor: DonorCreate,
    db: Session = Depends(get_db)
):
    normalized_bg = validate_blood_group(donor.blood_group)
    new_donor = models.Donor(
        name=donor.name.strip(),
        blood_group=normalized_bg,
        location=donor.location.strip(),
        phone=donor.phone.strip(),
        available=donor.available
    )

    db.add(new_donor)
    db.commit()
    db.refresh(new_donor)

    return {
        "message": "Donor registered successfully",
        "donor_id": new_donor.id,
        "name": new_donor.name,
        "blood_group": new_donor.blood_group,
        "location": new_donor.location
    }


# =========================
# VIEW ALL DONORS
# =========================

@app.get("/donors")
def get_donors(
    db: Session = Depends(get_db)
):
    donors = db.query(models.Donor).all()

    return donors


# =========================
# UPDATE DONOR AVAILABILITY
# =========================

@app.put("/donors/{donor_id}/availability")
def update_donor_availability(
    donor_id: int,
    available: bool,
    db: Session = Depends(get_db)
):
    donor = db.query(models.Donor).filter(
        models.Donor.id == donor_id
    ).first()

    if not donor:
        return {
            "message": "Donor not found"
        }

    donor.available = available

    db.commit()
    db.refresh(donor)

    return {
        "message": "Donor availability updated successfully",
        "donor_id": donor.id,
        "name": donor.name,
        "available": donor.available
    }


# =========================
# CREATE EMERGENCY REQUEST
# =========================

@app.post("/emergency-requests")
def create_emergency_request(
    request: EmergencyRequestCreate,
    db: Session = Depends(get_db)
):
    normalized_bg = validate_blood_group(request.blood_group)
    new_request = models.EmergencyRequest(
        patient_name=request.patient_name.strip(),
        blood_group=normalized_bg,
        location=request.location.strip(),
        hospital=request.hospital.strip(),
        contact=request.contact.strip()
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {
        "message": "Emergency blood request created successfully",
        "request_id": new_request.id,
        "patient_name": new_request.patient_name,
        "blood_group": new_request.blood_group,
        "location": new_request.location,
        "hospital": new_request.hospital,
        "status": new_request.status
    }


# =========================
# VIEW EMERGENCY REQUESTS
# =========================

@app.get("/emergency-requests")
def get_emergency_requests(
    db: Session = Depends(get_db)
):
    requests = db.query(
        models.EmergencyRequest
    ).all()

    return requests


# =========================
# MATCH DONORS
# =========================

@app.get("/match/{request_id}")
def match_donors(
    request_id: int,
    db: Session = Depends(get_db)
):

    emergency_request = db.query(
        models.EmergencyRequest
    ).filter(
        models.EmergencyRequest.id == request_id
    ).first()

    if not emergency_request:
        return {
            "message": "Emergency request not found"
        }

    compatible_groups = BLOOD_COMPATIBILITY.get(emergency_request.blood_group, [])

    matched_donors = db.query(
        models.Donor
    ).filter(
        models.Donor.blood_group.in_(compatible_groups),
        models.Donor.location.ilike(emergency_request.location),
        models.Donor.available == True
    ).all()

    return {
        "request_id": emergency_request.id,
        "patient_name": emergency_request.patient_name,
        "blood_group": emergency_request.blood_group,
        "location": emergency_request.location,
        "compatible_groups": compatible_groups,
        "matched_donors": matched_donors
    }


# =========================
# UPDATE EMERGENCY REQUEST STATUS
# =========================

@app.put("/emergency-requests/{request_id}/status")
def update_emergency_status(
    request_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    emergency_request = db.query(
        models.EmergencyRequest
    ).filter(
        models.EmergencyRequest.id == request_id
    ).first()

    if not emergency_request:
        return {
            "message": "Emergency request not found"
        }

    allowed_status = [
        "Pending",
        "Matched",
        "Completed"
    ]

    if status not in allowed_status:
        return {
            "message": "Invalid status"
        }

    emergency_request.status = status

    db.commit()
    db.refresh(emergency_request)

    return {
        "message": "Emergency request status updated successfully",
        "request_id": emergency_request.id,
        "status": emergency_request.status
    }


# =========================
# DASHBOARD
# =========================

@app.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    total_donors = db.query(
        models.Donor
    ).count()

    available_donors = db.query(
        models.Donor
    ).filter(
        models.Donor.available == True
    ).count()

    total_requests = db.query(
        models.EmergencyRequest
    ).count()

    pending_requests = db.query(
        models.EmergencyRequest
    ).filter(
        models.EmergencyRequest.status == "Pending"
    ).count()

    matched_requests = db.query(
        models.EmergencyRequest
    ).filter(
        models.EmergencyRequest.status == "Matched"
    ).count()

    completed_requests = db.query(
        models.EmergencyRequest
    ).filter(
        models.EmergencyRequest.status == "Completed"
    ).count()

    return {
        "total_donors": total_donors,
        "available_donors": available_donors,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "matched_requests": matched_requests,
        "completed_requests": completed_requests
    }