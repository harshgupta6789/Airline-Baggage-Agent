from mcp.server import MCPServer
from app.services.data_service import get_booking, get_baggage_events

mcp = MCPServer("airline-tools")

@mcp.tool()
def lookup_booking(pnr: str):
    return get_booking(pnr)

@mcp.tool()
def lookup_baggage(bag_tag: str):
    return get_baggage_events(bag_tag)

if __name__ == "__main__":
    mcp.run()