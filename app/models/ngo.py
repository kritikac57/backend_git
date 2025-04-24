from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from datetime import datetime

Base = declarative_base()

class NGO(Base):
    __tablename__ = "ngos"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    address = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20))
    website = Column(String(255))
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    is_available = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    created_at = Column(func.now(), nullable=False)
    updated_at = Column(func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NGO {self.name}>"

