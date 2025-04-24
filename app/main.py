# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint
from typing import List, Optional

from app.database import get_db, engine
from app.models import Base, User, NGO, Donation, Notification
from app.schemas import (
    UserCreate, UserResponse, UserLogin, NGOCreate, NGOResponse, NGOUpdate,
    DonationCreate, DonationResponse, DonationUpdate, NotificationResponse,
    Token, GeocodingResponse
)
from app.services.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user
)
from app.services.geocoding import reverse_geocode, format_address
from app.services.notification import (
    create_notification, notify_user_donation_status_change,
    notify_ngo_new_donation
)
from app.config import settings

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="API for Geolocation-based Donation App",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
@app.post(f"{settings.api_prefix}/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post(f"{settings.api_prefix}/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# Geocoding routes
@app.get(f"{settings.api_prefix}/geocode/reverse", response_model=GeocodingResponse)
async def get_address_from_coordinates(latitude: float, longitude: float):
    return await reverse_geocode(latitude, longitude)

# NGO routes
@app.post(f"{settings.api_prefix}/ngos", response_model=NGOResponse)
async def create_ngo(
    ngo: NGOCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create point geography from lat/lon
    point = f"POINT({ngo.longitude} {ngo.latitude})"
    
    db_ngo = NGO(
        name=ngo.name,
        description=ngo.description,
        email=ngo.email,
        phone=ngo.phone,
        website=ngo.website,
        location=point,
        address=ngo.address,
        status=ngo.status
    )
    
    db.add(db_ngo)
    db.commit()
    db.refresh(db_ngo)
    
    # Format response
    response = {**db_ngo.__dict__}
    if hasattr(db_ngo, 'location') and db_ngo.location is not None:
        # Extract coordinates from geography point
        point_wkb = bytes(db_ngo.location.data)
        coords = db.execute(text(f"SELECT ST_X('{point_wkb}'::geometry), ST_Y('{point_wkb}'::geometry)")).first()
        response['longitude'] = coords[0]
        response['latitude'] = coords[1]
    
    return response

@app.get(f"{settings.api_prefix}/ngos", response_model=List[NGOResponse])
async def get_ngos(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[float] = 10000,  # Default 10km radius
    db: Session = Depends(get_db)
):
    query = db.query(NGO)
    
    # If coordinates provided, find NGOs within radius and add distance
    if latitude is not None and longitude is not None:
        # Create point from user coordinates
        user_point = func.ST_MakePoint(longitude, latitude)
        user_geog = func.ST_SetSRID(user_point, 4326)
        
        # Filter NGOs within radius
        query = query.filter(
            func.ST_DWithin(
                NGO.location,
                user_geog,
                radius  # Distance in meters
            )
        )
        
        # Add distance calculation
        query = query.add_columns(
            func.ST_Distance(
                NGO.location,
                user_geog
            ).label("distance")
        ).order_by("distance")
    
    results = query.all()
    
    # Format response
    response = []
    for result in results:
        if hasattr(result, "distance"):
            ngo = result[0]
            distance = result[1]
        else:
            ngo = result
            distance = None
        
        ngo_dict = {**ngo.__dict__}
        
        # Extract coordinates from geography point
        if hasattr(ngo, 'location') and ngo.location is not None:
            point_wkb = bytes(ngo.location.data)
            coords = db.execute(text(f"SELECT ST_X('{point_wkb}'::geometry), ST_Y('{point_wkb}'::geometry)")).first()
            ngo_dict['longitude'] = coords[0]
            ngo_dict['latitude'] = coords[1]
        
        if distance is not None:
            ngo_dict['distance'] = distance
        
        response.append(ngo_dict)
    
    return response

@app.get(f"{settings.api_prefix}/ngos/{{ngo_id}}", response_model=NGOResponse)
async def get_ngo(ngo_id: int, db: Session = Depends(get_db)):
    ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NGO not found"
        )
    
    # Format response
    response = {**ngo.__dict__}
    if hasattr(ngo, 'location') and ngo.location is not None:
        point_wkb = bytes(ngo.location.data)
        coords = db.execute(text(f"SELECT ST_X('{point_wkb}'::geometry), ST_Y('{point_wkb}'::geometry)")).first()
        response['longitude'] = coords[0]
        response['latitude'] = coords[1]
    
    return response

@app.put(f"{settings.api_prefix}/ngos/{{ngo_id}}", response_model=NGOResponse)
async def update_ngo(
    ngo_id: int,
    ngo_update: NGOUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_ngo = db.query(NGO).filter(NGO.id == ngo_id).first()
    if not db_ngo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NGO not found"
        )
    
    # Update fields
    update_data = ngo_update.dict(exclude_unset=True)
    
    # Handle location update if latitude and longitude are provided
    if "latitude" in update_data and "longitude" in update_data:
        point = f"POINT({update_data['longitude']} {update_data['latitude']})"
        db_ngo.location = point
        del update_data["latitude"]
        del update_data["longitude"]
    
    # Update other fields
    for key, value in update_data.items():
        setattr(db_ngo, key, value)
    
    db.commit()
    db.refresh(db_ngo)
    
    # Format response
    response = {**db_ngo.__dict__}
    if hasattr(db_ngo, 'location') and db_ngo.location is not None:
        point_wkb = bytes(db_ngo.location.data)
        coords = db.execute(text(f"SELECT ST_X('{point_wkb}'::geometry), ST_Y('{point_wkb}'::geometry)")).first()
        response['longitude'] = coords[0]
        response['latitude'] = coords[1]
    
    return response

# Donation routes
@app.post(f"{settings.api_prefix}/donations", response_model=DonationResponse)
async def create_donation(
    donation: DonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create point geography from lat/lon
    point = f"POINT({donation.longitude} {donation.latitude})"
    
    db_donation = Donation(
        user_id=current_user.id,
        donation_type=donation.donation_type,
        description=donation.description,
        quantity=donation.quantity,
        location=point,
        address=donation.address,
        status="pending"
    )
    
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)
    