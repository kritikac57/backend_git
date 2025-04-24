from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from geojson_pydantic import Point
from enum import Enum

class DonationStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DonationType(str, Enum):
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"
    TOYS = "toys"
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    OTHER = "other"

class DonationBase(BaseModel):
    title: str
    description: Optional[str] = None
    donation_type: DonationType
    donor_name: str
    donor_email: EmailStr
    donor_phone: Optional[str] = None
    address: str
    location: Point

class DonationCreate(DonationBase):
    pass

class DonationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    donation_type: Optional[DonationType] = None
    status: Optional[DonationStatus] = None
    ngo_id: Optional[int] = None

class DonationInDB(DonationBase):
    id: int
    status: DonationStatus
    ngo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Donation(DonationInDB):
    pass

class DonationAssign(BaseModel):
    ngo_id: int