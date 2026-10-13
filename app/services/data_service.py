import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

def load_json(filename):
    with open(DATA_DIR / filename, "r") as file:
        return json.load(file)

def get_booking(pnr):
    bookings = load_json("bookings.json")

    for booking in bookings:
        if booking["pnr"] == pnr:
            return booking

    return None

def get_baggage_events(bag_tag):
    bags = load_json("baggage_events.json")

    for bag in bags:
        if bag["bag_tag"] == bag_tag:
            return bag

    return None