# app/routers/ngos.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeomFromGeoJSON
from app.core.database import get_db
from app.models.ngo import NGO
from app.schemas.ngo import NGOCreate, NGO as NGOSchema, NGOUpdate, NGONearby
from geojson_pydantic import Point

router = APIRouter(prefix="/ngos", tags=["ngos"])

@router.post("/", response_model=NGOSchema)
def create_ngo(ngo: NGOCreate, db: Session = Depends(get_db)):
    """Create a new NGO"""
    # Convert GeoJSON Point to PostGIS geometry
    location_geojson = ngo.location.dict()
    
    db_ngo = NGO(
        name=ngo.name,
        description=ngo.description,
        address=ngo.address,
        email=ngo.email,
        phone=ngo.phone,
        website=str(ngo.website) if ngo.website else None,
        location=f"SRID=4326;POINT({location_geojson['coordinates'][0]} {location_geojson['coordinates'][1]})"
    )
    
    db.add(db_ngo)
    db.commit()
    db.refresh(db_ngo)
    return db_ngo

@router.get("/", response_model=List[NGOSchema])
def get_ngos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all NGOs"""
    return db.query(NGO).offset(skip).limit(limit).all()

@router.get("/{ngo_id}", response_model=NGOSchema)
def get_ngo(ngo_id: int, db: Session = Depends(get_db)):
    """Get an NGO by ID"""
    db_ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if db_ngo is None:
        raise HTTPException(status_code=404, detail="NGO not found")
    return db_ngo

@router.put("/{ngo_id}", response_model=NGOSchema)
def update_ngo(ngo_id: int, ngo: NGOUpdate, db: Session = Depends(get_db)):
    """Update an NGO"""
    db_ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if db_ngo is None:
        raise HTTPException(status_code=404, detail="NGO not found")
    
    update_data = ngo.dict(exclude_unset=True)
    
    # Handle location separately if provided
    if "location" in update_data:
        location_geojson = update_data.pop("location")
        if location_geojson:
            db_ngo.location = f"SRID=4326;POINT({location_geojson['coordinates'][0]} {location_geojson['coordinates'][1]})"
    
    # Update other fields
    for key, value in update_data.items():
        setattr(db_ngo, key, value)
    
    db.commit()
    db.refresh(db_ngo)
    return db_ngo

@router.delete("/{ngo_id}", status_code=204)
def delete_ngo(ngo_id: int, db: Session = Depends(get_db)):
    """Delete an NGO"""
    db_ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if db_ngo is None:
        raise HTTPException(status_code=404, detail="NGO not found")
    
    db.delete(db_ngo)
    db.commit()
    return None

@router.get("/nearby/", response_model=List[NGONearby])
def get_nearby_ngos(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    available_only: bool = Query(True, description="Filter only available NGOs"),
    db: Session = Depends(get_db)
):
    """Find NGOs within a specified radius"""
    # Convert km to meters for PostGIS
    radius_meters = radius_km * 1000
    
    # Create user point
    user_point = f"SRID=4326;POINT({lng} {lat})"
    
    # Base query
    query = db.query(
        NGO,
        func.ST_Distance(
            func.ST_Transform(NGO.location, 3857),
            func.ST_Transform(func.ST_GeomFromText(user_point, 4326), 3857)
        ).label("distance_meters")
    )
    
    # Filter by distance
    query = query.filter(
        ST_DWithin(
            func.ST_Transform(NGO.location, 3857),
            func.ST_Transform(func.ST_GeomFromText(user_point, 4326), 3857),
            radius_meters
        )
    )
    
    # Filter by availability if requested
    if available_only:
        query = query.filter(NGO.is_available == True)
    
    # Order by distance and get results
    results = query.order_by("distance_meters").all()
    
    # Format results with distance in km
    nearby_ngos = []
    for ngo, distance_meters in results:
        ngo_dict = {
            "id": ngo.id,
            "name": ngo.name,
            "description": ngo.description,
            "address": ngo.address,
            "email": ngo.email,
            "phone": ngo.phone,
            "website": ngo.website,
            "location": extract_point_from_wkb(ngo.location),
            "is_available": ngo.is_available,
            "verified": ngo.verified,
            "created_at": ngo.created_at,
            "updated_at": ngo.updated_at,
            "distance_km": distance_meters / 1000  # Convert meters to km
        }
        nearby_ngos.append(ngo_dict)
    
    return nearby_ngos

def extract_point_from_wkb(wkb_point):
    """Extract coordinates from WKB geometry"""
    # This is a placeholder - in a real implementation,
    # you'd use proper WKB parsing from PostGIS
    # For now, we'll return a mock point
    return {"type": "Point", "coordinates": [0, 0]}

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