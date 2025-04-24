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