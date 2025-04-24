# app/routers/donations.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.donation import Donation, DonationStatus
from app.models.ngo import NGO
from app.schemas.donation import (
    Donation as DonationSchema,
    DonationCreate,
    DonationUpdate,
    DonationAssign
)
from app.services.notification_service import send_ngo_notification

router = APIRouter(prefix="/donations", tags=["donations"])

@router.post("/", response_model=DonationSchema)
def create_donation(donation: DonationCreate, db: Session = Depends(get_db)):
    """Create a new donation"""
    # Convert GeoJSON Point to PostGIS geometry
    location_geojson = donation.location.dict()
    
    db_donation = Donation(
        title=donation.title,
        description=donation.description,
        donation_type=donation.donation_type,
        donor_name=donation.donor_name,
        donor_email=donation.donor_email,
        donor_phone=donation.donor_phone,
        address=donation.address,
        location=f"SRID=4326;POINT({location_geojson['coordinates'][0]} {location_geojson['coordinates'][1]})",
        status=DonationStatus.PENDING
    )
    
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    return db_donation

@router.get("/", response_model=List[DonationSchema])
def get_donations(
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get all donations with optional status filter"""
    query = db.query(Donation)
    
    if status:
        query = query.filter(Donation.status == status)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{donation_id}", response_model=DonationSchema)
def get_donation(donation_id: int, db: Session = Depends(get_db)):
    """Get a donation by ID"""
    db_donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if db_donation is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    return db_donation

@router.put("/{donation_id}", response_model=DonationSchema)
def update_donation(donation_id: int, donation: DonationUpdate, db: Session = Depends(get_db)):
    """Update a donation"""
    db_donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if db_donation is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    update_data = donation.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_donation, key, value)
    
    db.commit()
    db.refresh(db_donation)
    return db_donation

@router.post("/{donation_id}/assign", response_model=DonationSchema)
def assign_donation(
    donation_id: int, 
    assignment: DonationAssign, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Assign a donation to an NGO"""
    # Check if donation exists
    db_donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if db_donation is None:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    # Check if donation is already assigned
    if db_donation.status != DonationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Donation is not available for assignment")
    
    # Check if NGO exists
    ngo = db.query(NGO).filter(NGO.id == assignment.ngo_id).first()
    if ngo is None:
        raise HTTPException(status_code=404, detail="NGO not found")
    
    # Check if NGO is available
    if not ngo.is_available:
        raise HTTPException(status_code=400, detail="NGO is not available")
    
    # Update donation
    db_donation.ngo_id = ngo.id
    db_donation.status = DonationStatus.ASSIGNED
    
    # Update NGO availability if needed
    # ngo.is_available = False  # Optional: mark NGO as busy
    
    db.commit()
    db.refresh(db_donation)
    
    # Send notification to NGO (background task)
    background_tasks.add_task(
        send_ngo_notification,
        ngo_email=ngo.email,
        ngo_name=ngo.name,
        donation_id=db_donation.id,
        donation_title=db_donation.title,
        donor_name=db_donation.donor_name
    )
    
    return db_donation