from app.mcp.client import lookup_booking_info, lookup_baggage_info
import asyncio

async def main():
    booking_info = await lookup_booking_info("ABC123")
    print("\nBOOKING INFO:")
    print(booking_info)

    baggage_info = await lookup_baggage_info("BG001")
    print("\nBAGGAGE INFO:")
    print(baggage_info)

if __name__ == "__main__":
    asyncio.run(main())