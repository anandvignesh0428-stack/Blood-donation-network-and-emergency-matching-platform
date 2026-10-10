from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import math
import os
from pathlib import Path

from database import engine, Base, get_db, run_safe_migration
import models
from schemas import DonorCreate, EmergencyRequestCreate

# Project-relative paths: works locally and on Vercel serverless
# (never hardcode machine-specific absolute paths).
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Safe idempotent migration before table creation - protects existing data
run_safe_migration()


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

VALID_PRIORITIES = {"Critical", "High", "Normal"}


def normalize_blood_group(bg: str) -> str:
    return bg.strip().upper()


def validate_blood_group(bg: str) -> str:
    normalized = normalize_blood_group(bg)
    if normalized not in BLOOD_COMPATIBILITY:
        raise HTTPException(status_code=400, detail=f"Invalid blood group: {bg}")
    return normalized


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


app = FastAPI(
    title="Blood Donation Network and Emergency Matching Platform",
    description="A platform to connect blood donors with patients during emergencies.",
    version="2.0.0"
)


# Frontend and API are served from the same deployment (same origin),
# so browsers do not need CORS for the built-in UI. Extra origins can be
# allowed via the FRONTEND_ORIGINS env var (comma-separated) if ever needed.
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:  # don't crash import (serverless cold start) on DB hiccup
    print(f"WARNING: could not ensure database tables exist: {exc}")


# =========================
# HOME PAGE
# =========================

@app.get("/", response_class=HTMLResponse)
def home():
    with open(TEMPLATES_DIR / "index.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# DONOR PAGE
# =========================

@app.get("/donor", response_class=HTMLResponse)
def donor_page():
    with open(TEMPLATES_DIR / "donor.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# EMERGENCY PAGE
# =========================

@app.get("/emergency", response_class=HTMLResponse)
def emergency_page():
    with open(TEMPLATES_DIR / "emergency.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# MATCHING PAGE
# =========================

@app.get("/matching", response_class=HTMLResponse)
def matching_page():
    with open(TEMPLATES_DIR / "matching.html", "r", encoding="utf-8") as file:
        return file.read()


# =========================
# DASHBOARD PAGE
# =========================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    with open(TEMPLATES_DIR / "dashboard.html", "r", encoding="utf-8") as file:
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
        available=donor.available,
        latitude=donor.latitude,
        longitude=donor.longitude
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
# UPDATE DONOR GPS
# =========================

@app.put("/donors/{donor_id}/location")
def update_donor_location(
    donor_id: int,
    latitude: float = Query(...),
    longitude: float = Query(...),
    db: Session = Depends(get_db)
):
    donor = db.query(models.Donor).filter(
        models.Donor.id == donor_id
    ).first()

    if not donor:
        return {"message": "Donor not found"}

    donor.latitude = latitude
    donor.longitude = longitude
    db.commit()
    db.refresh(donor)

    return {
        "message": "Donor location updated",
        "donor_id": donor.id,
        "latitude": donor.latitude,
        "longitude": donor.longitude
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

    priority = request.priority.strip()
    if priority not in VALID_PRIORITIES:
        priority = "Normal"

    new_request = models.EmergencyRequest(
        patient_name=request.patient_name.strip(),
        blood_group=normalized_bg,
        location=request.location.strip(),
        hospital=request.hospital.strip(),
        contact=request.contact.strip(),
        priority=priority,
        latitude=request.latitude,
        longitude=request.longitude
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
        "status": new_request.status,
        "priority": new_request.priority
    }


# =========================
# VIEW EMERGENCY REQUESTS
# =========================

@app.get("/emergency-requests")
def get_emergency_requests(
    db: Session = Depends(get_db)
):
    requests = db.query(models.EmergencyRequest).all()
    return requests


# =========================
# MATCH DONORS (with distance)
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
        return {"message": "Emergency request not found"}

    compatible_groups = BLOOD_COMPATIBILITY.get(emergency_request.blood_group, [])

    matched_donors = db.query(
        models.Donor
    ).filter(
        models.Donor.blood_group.in_(compatible_groups),
        models.Donor.available == True
    ).all()

    results = []
    req_lat = emergency_request.latitude
    req_lng = emergency_request.longitude

    for donor in matched_donors:
        donor_data = {
            "id": donor.id,
            "name": donor.name,
            "blood_group": donor.blood_group,
            "location": donor.location,
            "phone": donor.phone,
            "available": donor.available,
            "latitude": donor.latitude,
            "longitude": donor.longitude,
            "distance_km": None
        }

        if req_lat is not None and req_lng is not None and donor.latitude is not None and donor.longitude is not None:
            dist = haversine_distance(req_lat, req_lng, donor.latitude, donor.longitude)
            donor_data["distance_km"] = round(dist, 1)
        elif req_lat is not None and req_lng is not None:
            same_location = donor.location.strip().lower() == emergency_request.location.strip().lower()
            if same_location:
                donor_data["distance_km"] = 0.0
            else:
                donor_data["distance_km"] = 9999.0

        results.append(donor_data)

    results.sort(key=lambda d: (d["distance_km"] is None, d["distance_km"] or 9999))

    return {
        "request_id": emergency_request.id,
        "patient_name": emergency_request.patient_name,
        "blood_group": emergency_request.blood_group,
        "location": emergency_request.location,
        "hospital": emergency_request.hospital,
        "priority": emergency_request.priority,
        "compatible_groups": compatible_groups,
        "matched_donors": results
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
        return {"message": "Emergency request not found"}

    allowed_status = ["Pending", "Matched", "Completed", "Cancelled"]

    if status not in allowed_status:
        return {"message": "Invalid status"}

    emergency_request.status = status
    db.commit()
    db.refresh(emergency_request)

    return {
        "message": "Emergency request status updated successfully",
        "request_id": emergency_request.id,
        "status": emergency_request.status
    }


# =========================
# DASHBOARD API
# =========================

@app.get("/api/dashboard")
def dashboard_api(
    db: Session = Depends(get_db)
):
    total_donors = db.query(models.Donor).count()
    available_donors = db.query(models.Donor).filter(models.Donor.available == True).count()
    total_requests = db.query(models.EmergencyRequest).count()
    pending_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.status == "Pending").count()
    matched_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.status == "Matched").count()
    completed_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.status == "Completed").count()
    critical_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.priority == "Critical", models.EmergencyRequest.status != "Completed").count()
    high_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.priority == "High", models.EmergencyRequest.status != "Completed").count()

    return {
        "total_donors": total_donors,
        "available_donors": available_donors,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "matched_requests": matched_requests,
        "completed_requests": completed_requests,
        "critical_requests": critical_requests,
        "high_requests": high_requests
    }
