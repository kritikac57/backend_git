# app/models/donation.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Enum
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import enum
from datetime import datetime

from .ngo import Base

class DonationStatus(enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DonationType(enum.Enum):
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"
    TOYS = "toys"
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    OTHER = "other"

class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    donation_type = Column(Enum(DonationType), nullable=False)
    donor_name = Column(String(100), nullable=False)
    donor_email = Column(String(100), nullable=False)
    donor_phone = Column(String(20))
    address = Column(String(255), nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    status = Column(Enum(DonationStatus), default=DonationStatus.PENDING)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Donation {self.title} by {self.donor_name}>"