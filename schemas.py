from pydantic import BaseModel, field_validator
from typing import Optional


VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def normalize_blood_group(bg: str) -> str:
    return bg.strip().upper()


class DonorCreate(BaseModel):
    name: str
    blood_group: str
    location: str
    phone: str
    available: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name too long (max 100 characters)")
        return v

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        normalized = normalize_blood_group(v)
        if normalized not in VALID_BLOOD_GROUPS:
            raise ValueError(f"Invalid blood group. Must be one of: {', '.join(sorted(VALID_BLOOD_GROUPS))}")
        return normalized

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Location cannot be empty")
        if len(v) > 100:
            raise ValueError("Location too long (max 100 characters)")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Phone number cannot be empty")
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        if len(digits) > 15:
            raise ValueError("Phone number too long (max 15 digits)")
        return v


class EmergencyRequestCreate(BaseModel):
    patient_name: str
    blood_group: str
    location: str
    hospital: str
    contact: str

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Patient name cannot be empty")
        if len(v) > 100:
            raise ValueError("Patient name too long (max 100 characters)")
        return v

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        normalized = normalize_blood_group(v)
        if normalized not in VALID_BLOOD_GROUPS:
            raise ValueError(f"Invalid blood group. Must be one of: {', '.join(sorted(VALID_BLOOD_GROUPS))}")
        return normalized

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Location cannot be empty")
        if len(v) > 100:
            raise ValueError("Location too long (max 100 characters)")
        return v

    @field_validator("hospital")
    @classmethod
    def validate_hospital(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Hospital name cannot be empty")
        if len(v) > 100:
            raise ValueError("Hospital name too long (max 100 characters)")
        return v

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Contact number cannot be empty")
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Contact number must have at least 10 digits")
        if len(digits) > 15:
            raise ValueError("Contact number too long (max 15 digits)")
        return v