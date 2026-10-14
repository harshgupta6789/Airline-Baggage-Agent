import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:")
            print(tools)

            booking = await session.call_tool("lookup_booking", {"pnr": "ABC123"})
            print("\nBOOKING:")
            print(booking)
            
            baggage = await session.call_tool("lookup_baggage", {"bag_tag": "BG001"})
            print("\nBAGGAGE:")
            print(baggage)

if __name__ == "__main__":
    asyncio.run(main())