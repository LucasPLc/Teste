import sys
import os
import logging
from mcp.server.fastmcp import FastMCP

# Logging básico para debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP_Test")

# Criar MCP com nome único
mcp = FastMCP("mcp_teste_minimalista")
logger.info("Servidor MCP minimalista iniciado.")

@mcp.tool()
async def ping() -> str:
    """Ferramenta simples para testar conexão."""
    return "pong"

if __name__ == "__main__":
    # Garante que diretório existe
    os.makedirs("relatorios_json", exist_ok=True)
    mcp.run(transport='stdio')
