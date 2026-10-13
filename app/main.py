from services.data_service import get_bookings, get_baggage_events

def main():
    print("Airline Baggage Claim Validation Agent is running...")
    print(get_bookings("ABC123"))
    print(get_baggage_events("BG001"))

if __name__ == "__main__":
    main()