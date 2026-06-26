import os
import math
import requests # <--- This is new! It fetches the map data
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_real_resources(lat, lng):
    # This is an 'Overpass' query: It asks for hospitals and pharmacies near the user
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"~"hospital|pharmacy|blood_bank"](around:10000,{lat},{lng});
      way["amenity"~"hospital|pharmacy|blood_bank"](around:10000,{lat},{lng});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=10)
        data = response.json()
        
        real_resources = []
        for item in data.get('elements', []):
            tags = item.get('tags', {})
            # Extract name, phone, and coordinates
            name = tags.get('name', 'Unnamed Medical Center')
            # Look for phone or mobile tags in the map data
            phone = tags.get('phone') or tags.get('contact:phone') or tags.get('mobile') or "108" 
            
            # Clean the phone number (remove spaces)
            clean_phone = "".join(filter(str.isdigit, str(phone)))
            
            res_lat = item.get('lat') or item.get('center', {}).get('lat')
            res_lng = item.get('lon') or item.get('center', {}).get('lng')
            
            if res_lat and res_lng:
                real_resources.append({
                    "id": item.get('id'),
                    "name": name,
                    "type": tags.get('amenity', 'Medical').capitalize().replace('_', ' '),
                    "lat": res_lat,
                    "lng": res_lng,
                    "contact": clean_phone if len(clean_phone) >= 10 else "108"
                })
        return real_resources
    except:
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

@app.get("/find-nearby")
async def find_nearby(user_lat: float, user_lng: float):
    # FETCH REAL DATA FROM THE MAP
    raw_resources = fetch_real_resources(user_lat, user_lng)
    
    nearby = []
    for res in raw_resources:
        dist = calculate_distance(user_lat, user_lng, res["lat"], res["lng"])
        res["distance"] = round(dist, 2)
        nearby.append(res)
        
    # Sort by closest first
    return sorted(nearby, key=lambda x: x["distance"])[:20] # Show top 20 nearest

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)