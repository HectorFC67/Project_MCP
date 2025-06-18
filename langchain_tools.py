from langchain.tools import tool
import requests

BIBLIOTECA_URL = "http://127.0.0.1:8100/provision"
COMPRAS_URL = "http://127.0.0.1:8200/provision"

@tool
def biblioteca_tool(query: str) -> str:
    """Consulta la API MCP Biblioteca y devuelve texto legible."""
    response = requests.post(BIBLIOTECA_URL, json={"query": query})
    response.raise_for_status()
    chunks = response.json().get("chunks", [])
    return "\n".join(c.get("text", "") for c in chunks)

@tool
def compras_tool(query: str) -> str:
    """Consulta la MCP de compras y devuelve texto legible."""
    response = requests.post(COMPRAS_URL, json={"query": query})
    response.raise_for_status()
    chunks = response.json().get("chunks", [])
    return "\n".join(c.get("text", "") for c in chunks)