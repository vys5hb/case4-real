from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator, root_validator
import hashlib

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

class SurveySubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=13, le=120)
    consent: bool = Field(..., description="Must be true to accept")
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=1000)
    user_agent: Optional[str] = Field(None, description="Browser or client identifier string")
    submission_id: Optional[str] = None   # New field

    @validator("comments")
    def _strip_comments(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("consent")
    def _must_consent(cls, v):
        if v is not True:
            raise ValueError("consent must be true")
        return v

    @root_validator(pre=True)
    def assign_submission_id(cls, values):
        # If front end provided submission_id, keep it
        if values.get("submission_id"):
            return values

        email = values.get("email")
        if email:
            # Format current date/hour: YYYYMMDDHH
            now = datetime.utcnow().strftime("%Y%m%d%H")
            values["submission_id"] = sha256_hex(f"{email}{now}")
        return values


class StoredSurveyRecord(SurveySubmission):
    received_at: datetime
    ip: str

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        # Replace sensitive fields with SHA-256 hashes
        data["email"] = sha256_hex(str(self.email))
        data["age"]   = sha256_hex(str(self.age))
        return data