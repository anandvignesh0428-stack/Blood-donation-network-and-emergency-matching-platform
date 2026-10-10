from sqlalchemy import Column, Integer, String, Boolean, Float
from database import Base


VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
VALID_PRIORITIES = {"Critical", "High", "Normal"}


def normalize_blood_group(bg: str) -> str:
    return bg.strip().upper()


# =========================
# DONOR TABLE
# =========================

class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    blood_group = Column(String(10), nullable=False)

    location = Column(String(100), nullable=False)

    phone = Column(String(20), nullable=False)

    available = Column(Boolean, default=True)

    latitude = Column(Float, nullable=True)

    longitude = Column(Float, nullable=True)


# =========================
# EMERGENCY REQUEST TABLE
# =========================

class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String(100), nullable=False)

    blood_group = Column(String(10), nullable=False)

    location = Column(String(100), nullable=False)

    hospital = Column(String(100), nullable=False)

    contact = Column(String(20), nullable=False)

    status = Column(String(20), default="Pending")

    priority = Column(String(20), default="Normal")

    latitude = Column(Float, nullable=True)

    longitude = Column(Float, nullable=True)
