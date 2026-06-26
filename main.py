import os
import math
import requests 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_phone_number(phone_str):
    """Converts messy map text into a clickable phone number."""
    if not phone_str:
        return "108"
    # Keep only digits and the '+' sign
    clean = "".join([c for c in str(phone_str) if c.isdigit() or c == '+'])
    return clean if len(clean) >= 5 else "108"

def fetch_real_data(lat, lng):
    # Using the most reliable Global Overpass Mirror
    overpass_url = "https://overpass.kumi.systems/api/interpreter"
    query = f"""
    [out:json][timeout:20];
    (
      node["amenity"~"hospital|pharmacy|blood_bank"](around:10000,{lat},{lng});
      way["amenity"~"hospital|pharmacy|blood_bank"](around:10000,{lat},{lng});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': query}, timeout=15)
        elements = response.json().get('elements', [])
        
        results = []
        for item in elements:
            tags = item.get('tags', {})
            # Get real name or use generic
            name = tags.get('name') or tags.get('operator') or "Medical Center"
            
            # Get real phone number from tags
            raw_phone = tags.get('phone') or tags.get('contact:phone') or tags.get('mobile')
            phone = clean_phone_number(raw_phone)
            
            # Get coordinates
            r_lat = item.get('lat') or item.get('center', {}).get('lat')
            r_lng = item.get('lon') or item.get('center', {}).get('lng')
            
            if r_lat and r_lng:
                results.append({
                    "id": item.get('id'),
                    "name": name,
                    "type": tags.get('amenity', 'Medical').replace('_', ' ').title(),
                    "lat": r_lat,
                    "lng": r_lng,
                    "contact": phone
                })
        return results
    except Exception:
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

@app.get("/find-nearby")
async def find_nearby(user_lat: float, user_lng: float):
    raw_data = fetch_real_data(user_lat, user_lng)
    
    # If API is down, provide the basic emergency contact
    if not raw_data:
        return [{"id": 0, "name": "Local Emergency Line", "type": "Ambulance", "lat": user_lat, "lng": user_lng, "distance": 0, "contact": "108"}]

    nearby = []
    for res in raw_data:
        dist = calculate_distance(user_lat, user_lng, res["lat"], res["lng"])
        res["distance"] = round(dist, 2)
        nearby.append(res)
    
    # Sort by distance and return top 25
    return sorted(nearby, key=lambda x: x["distance"])[:25]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)