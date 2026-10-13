from fastapi import FastAPI, HTTPException

from app.services.data_service import get_bookings, get_baggage_events

app = FastAPI(title="Airline Baggage Claim Validation Agent", version="1.0.0")

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/bookings/{pnr}")
def booking(pnr: str):
    result = get_bookings(pnr)
    if not result:
        raise HTTPException(status_code = 404, detail="Booking not found")
    
    return result

@app.get("/baggage/{bag_tag}")
def baggage(bag_tag: str):
    result = get_baggage_events(bag_tag)
    if not result:
        raise HTTPException(status_code = 404, detail="Baggage record not found")
    
    return result
