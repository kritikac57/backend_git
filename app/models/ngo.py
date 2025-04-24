# app/schemas/ngo.py
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List, Tuple
from datetime import datetime
from geojson_pydantic import Point

class NGOBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    location: Point

class NGOCreate(NGOBase):
    pass

class NGOUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    location: Optional[Point] = None
    is_available: Optional[bool] = None
    verified: Optional[bool] = None

class NGOInDB(NGOBase):
    id: int
    is_available: bool
    verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NGO(NGOInDB):
    pass

class NGONearby(NGO):
    distance_km: float

# app/schemas/donation.py
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