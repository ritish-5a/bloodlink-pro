from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import math
import os # <--- NEW: This is needed to talk to the Cloud Server

app = FastAPI()

# Allow Frontend to talk to Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database of medical resources
RESOURCES = [
    {"id": 1, "name": "City Life Hospital", "type": "Hospital", "lat": 12.9716, "lng": 77.5946, "contact": "911000111"},
    {"id": 2, "name": "Central Blood Bank", "type": "Blood Bank", "lat": 12.9850, "lng": 77.6100, "contact": "911000222"},
    {"id": 3, "name": "Emergency Pharmacy", "type": "Pharmacy", "lat": 12.9600, "lng": 77.5800, "contact": "911000333"},
    {"id": 4, "name": "Rahul (Donor O+)", "type": "Donor", "lat": 12.9780, "lng": 77.5990, "contact": "9888877777"},
]

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

@app.get("/find-nearby")
async def find_nearby(user_lat: float, user_lng: float):
    nearby = []
    for res in RESOURCES:
        dist = calculate_distance(user_lat, user_lng, res["lat"], res["lng"])
        if dist < 15: # Show everything within 15km
            res_data = res.copy()
            res_data["distance"] = round(dist, 2)
            nearby.append(res_data)
    return sorted(nearby, key=lambda x: x["distance"])

# --- THIS IS THE SECTION THAT CHANGED FOR PUBLIC USE ---
if __name__ == "__main__":
    import uvicorn
    # The Cloud server will give us a PORT number. 
    # If it doesn't find one, it will use 8000 as a backup.
    port = int(os.environ.get("PORT", 8000)) 
    
    # We use host "0.0.0.0" so it is accessible to the whole world
    uvicorn.run(app, host="0.0.0.0", port=port)