
from concrete.secret_manager import load_application_secrets

from graphmcp import MultiServerMCPClient

# Load environment variables from .env file
load_application_secrets()


async def test_all_servers_healthy():
    client = MultiServerMCPClient.from_config_file("clients/mcp_config.json")
    health = await client.health_check_all()
    assert all(health.values()), f"Unhealthy servers: {health}"
