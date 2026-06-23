import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import Client


@pytest.fixture
async def mcp_client():
    from mcp_server import mcp
    async with Client(mcp) as client:
        yield client
