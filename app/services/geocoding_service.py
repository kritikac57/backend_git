# app/services/geocoding.py
import aiohttp
import json
from fastapi import HTTPException
from app.config import settings

async def reverse_geocode(latitude: float, longitude: float):
    """Convert latitude and longitude to address using Nominatim."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&addressdetails=1"
    
    headers = {
        "User-Agent": settings.nominatim_user_agent
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "display_name": data.get("display_name", ""),
                    "address": data.get("address", {})
                }
            else:
                raise HTTPException(
                    status_code=response.status,
                    detail="Failed to retrieve address from coordinates"
                )

def format_address(geocoding_result):
    """Format address from geocoding result into a readable string."""
    address = geocoding_result["address"]
    
    components = []
    for key in ["road", "house_number", "suburb", "city", "town", "county", "state", "postcode", "country"]:
        if key in address and address[key]:
            components.append(address[key])
    
    return ", ".join(components)