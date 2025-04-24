# backend/seed_data.py
import os
import sys
import random
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.models import NGO, Donation
from app.database import Base

# Connect to database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/donation_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create database session
db = SessionLocal()

# Sample NGO data - using San Francisco Bay Area coordinates as an example
ngos_data = [
    {
        "name": "Food Bank of the Bay",
        "description": "We collect and distribute food to those in need in the Bay Area.",
        "address": "900 Pennsylvania Ave, San Francisco, CA 94107",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "is_available": True
    },
    {
        "name": "Clothes For All",
        "description": "We provide clothes and essentials to homeless individuals.",
        "address": "123 Howard St, San Francisco, CA 94105",
        "latitude": 37.7815,
        "longitude": -122.3968,
        "is_available": True
    },
    {
        "name": "East Bay Relief Center",
        "description": "Supporting families in need in the East Bay.",
        "address": "2000 Broadway, Oakland, CA 94612",
        "latitude": 37.8044,
        "longitude": -122.2711,
        "is_available": True
    },
    {
        "name": "Community Aid South Bay",
        "description": "Community-driven support for underprivileged families.",
        "address": "200 E Santa Clara St, San Jose, CA 95113",
        "latitude": 37.3382,
        "longitude": -121.8863,
        "is_available": True
    },
    {
        "name": "North Bay Support Network",
        "description": "Helping communities in the North Bay with essential supplies.",
        "address": "1550 4th St, San Rafael, CA 94901",
        "latitude": 37.9735,
        "longitude": -122.5311,
        "is_available": True
    }
]

# Sample donation data
donation_types = ["food", "clothes", "furniture", "money", "books", "toys", "medical supplies"]
donor_names = ["John Smith", "Maria Garcia", "Alex Johnson", "Sarah Chen", "Michael Brown", "Lisa Kim"]
descriptions = [
    "Gently used winter clothes for children",
    "Non-perishable food items",
    "Used furniture in good condition",
    "Books for elementary school children",
    "Toys for toddlers",
    "Medical supplies and first aid kits"
]

# Function to create NGOs
def create_ngos():
    for ngo_data in ngos_data:
        # Check if NGO already exists
        existing_ngo = db.query(NGO).filter(NGO.name == ngo_data["name"]).first()
        if existing_ngo:
            print(f"NGO '{ngo_data['name']}' already exists, skipping.")
            continue
        
        # Create PostGIS point from lat/long
        point = f"POINT({ngo_data['longitude']} {ngo_data['latitude']})"
        ngo = NGO(
            name=ngo_data["name"],
            description=ngo_data["description"],
            address=ngo_data["address"],
            is_available=ngo_data["is_available"],
            location=func.ST_GeomFromText(point, 4326)  # Uses SRID 4326 (WGS84)
        )
        db.add(ngo)
    
    db.commit()
    print(f"Added {len(ngos_data)} NGOs to the database.")

# Function to create sample donations
def create_donations(num_donations=10):
    ngos = db.query(NGO).all()
    if not ngos:
        print("No NGOs found in the database. Please run create_ngos() first.")
        return
    
    for _ in range(num_donations):
        # Random coordinates near San Francisco
        lat = 37.7749 + (random.random() - 0.5) * 0.1  # +/- 0.05 degrees
        lng = -122.4194 + (random.random() - 0.5) * 0.1  # +/- 0.05 degrees
        
        # Create PostGIS point from lat/long
        point = f"POINT({lng} {lat})"
        
        # Randomly assign donation attributes
        donation = Donation(
            donor_name=random.choice(donor_names),
            donor_address=f"{random.randint(100, 999)} Sample St, San Francisco, CA",
            type=random.choice(donation_types),
            description=random.choice(descriptions),
            donor_location=func.ST_GeomFromText(point, 4326),
            status="pending"
        )
        
        # Randomly assign to an NGO (70% chance)
        if random.random() < 0.3:
            donation.ngo_id = random.choice(ngos).id
            donation.status = "assigned"
        
        db.add(donation)
    
    db.commit()
    print(f"Added {num_donations} sample donations to the database.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--donations":
        num_donations = 10
        if len(sys.argv) > 2:
            try:
                num_donations = int(sys.argv[2])
            except ValueError:
                print("Invalid number of donations. Using default: 10")
        
        create_donations(num_donations)
    else:
        create_ngos()