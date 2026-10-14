import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def lookup_booking_info(pnr: str):
    print("Looking up booking info for PNR:", pnr)
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args = ["-m", "app.mcp.server"]
    )

    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool("lookup_booking", {"pnr": pnr})
            return json.loads(result.content[0].text)

async def lookup_baggage_info(bag_tag: str):
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args = ["-m", "app.mcp.server"]
    )

    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool("lookup_baggage", {"bag_tag": bag_tag})
            return json.loads(result.content[0].text)