from sqlalchemy import Column, Integer, String, Boolean
from database import Base


VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def normalize_blood_group(bg: str) -> str:
    return bg.strip().upper()


# =========================
# DONOR TABLE
# =========================

class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    blood_group = Column(String, nullable=False)

    location = Column(String, nullable=False)

    phone = Column(String, nullable=False)

    available = Column(Boolean, default=True)


# =========================
# EMERGENCY REQUEST TABLE
# =========================

class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String, nullable=False)

    blood_group = Column(String, nullable=False)

    location = Column(String, nullable=False)

    hospital = Column(String, nullable=False)

    contact = Column(String, nullable=False)

    status = Column(String, default="Pending")