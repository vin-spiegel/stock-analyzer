"""헬스체크 엔드포인트 테스트 - 성공 기준 S2, S3"""
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_health_endpoint():
    """S2: /health 200 응답 + {"status": "ok"}"""
    from mcp_server import mcp
    app = mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_mcp_client_connects(mcp_client):
    """S3: MCP Client가 서버에 연결 가능"""
    tools = await mcp_client.list_tools()
    assert len(tools) > 0
