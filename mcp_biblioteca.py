#!/usr/bin/env python3
"""
MCP‑Server Biblioteca 𝑣0.2
==========================
• Añade **detección de preguntas**:
  1. «¿Cuántos libros ha escrito X?» → cuenta libros del autor.
  2. «Lista N autores al azar» → devuelve N nombres al azar (por defecto 3).
  3. Se mantiene lógica anterior de año/nacionalidad/título y fallback stats.

Arranque:
    uvicorn mcp_biblioteca:app --port 8100 --reload
"""

import os
import re
import random
from typing import List, Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

API_BASE = os.getenv("BIBLIOTECA_API", "http://127.0.0.1:8000")
SERVICE_NAME = "biblioteca_api"

nationalities = {
            "chileno": "Chile", "chilenos": "Chile", "chile": "Chile", "chilena":"Chile",
            "colombiano": "Colombia", "colombianos": "Colombia", "colombia": "Colombia", 
            "argentino": "Argentina", "argentinos": "Argentina", "argentina": "Argentina",
            "peruano": "Peru", "peruanos": "Peru", "perú": "Peru", "peru": "Peru",
            "español": "España", "españoles": "España", "españa": "España",
            "mexicano": "Mexico", "mexicanos": "Mexico", "méxico": "Mexico"
        }

# -----------------------------------------------------------------------------
# Pydantic modelos MCP
# -----------------------------------------------------------------------------
class ProvisionRequest(BaseModel):
    query: str = Field(..., description="Pregunta del usuario en lenguaje natural")
    history: Optional[List[str]] = None

class Chunk(BaseModel):
    type: Literal["text"] = "text"
    text: str
    source: str

class ProvisionResponse(BaseModel):
    chunks: List[Chunk]
    provenance: str = SERVICE_NAME

# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------
async def fetch_json(client: httpx.AsyncClient, path: str):
    r = await client.get(path)
    r.raise_for_status()
    return r.json()

# -----------------------------------------------------------------------------
# Núcleo de obtención de contexto
# -----------------------------------------------------------------------------
async def gather_context(query: str) -> List[Chunk]:
    q = query.lower()
    chunks: List[Chunk] = []

    async with httpx.AsyncClient(base_url=API_BASE, timeout=10) as cli:
        # 1. ¿Cuántos libros ha escrito X?
        m = re.search(r"cu[aá]ntos\s+libros\s+ha\s+escrito\s+([\w\sÁÉÍÓÚáéíóúñÑ]+)\?*", q)
        if m:
            name = m.group(1).strip()
            autores = await fetch_json(cli, "/autores/")
            autor = next((a for a in autores if name in a["nombre"].lower()), None)
            if autor:
                libros = await fetch_json(cli, f"/libros/autor/{autor['id']}")
                chunks.append(Chunk(
                    text=f"{autor['nombre']} escribió {len(libros)} libro(s). Detalle: {libros}",
                    source=f"{API_BASE}/libros/autor/{autor['id']}"
                ))
            return chunks  # respuesta suficiente

        # 2. "lista|muestra N autores"  
        m = re.search(r"list(?:a|ame|ar)?\s*(\d+)?\s*autores", q)
        if m:
            n = int(m.group(1) or 3)
            autores = await fetch_json(cli, "/autores/")
            sample = random.sample(autores, min(n, len(autores)))
            nombres = ", ".join(a["nombre"] for a in sample)
            chunks.append(Chunk(text=f"Autores al azar: {nombres}", source=f"{API_BASE}/autores/"))
            return chunks

        # 3. Año
        year = re.search(r"\b(19\d{2}|20\d{2})\b", q)
        if year:
            y = year.group(1)
            libros = await fetch_json(cli, f"/libros/buscar/por-anio/{y}")
            chunks.append(Chunk(text=f"Libros publicados en {y}: {libros}", source=f"{API_BASE}/libros/buscar/por-anio/{y}"))

        # 4. Nacionalidad
        for key, canon in nationalities.items():
            if key in q:
                autores = await fetch_json(cli, f"/autores/buscar/por-nacionalidad/{canon}")
                chunks.append(Chunk(
                    text=f"Autores {canon.lower()}: {autores}",
                    source=f"{API_BASE}/autores/buscar/por-nacionalidad/{canon}"
                ))
                break

        # 5. Título entre comillas
        t = re.search(r'"([^\"]+)"', query)
        if t:
            term = t.group(1)
            libros = await fetch_json(cli, f"/libros/buscar/titulo/{term}")
            chunks.append(Chunk(text=f"Libros con '{term}': {libros}", source=f"{API_BASE}/libros/buscar/titulo/{term}"))

        # 6. Fallback stats si aún no hay chunks
        if not chunks:
            stats = await fetch_json(cli, "/stats")
            chunks.append(Chunk(text=f"Estadísticas biblioteca: {stats}", source=f"{API_BASE}/stats"))

    return chunks

# -----------------------------------------------------------------------------
# FastAPI
# -----------------------------------------------------------------------------
app = FastAPI(title="MCP Biblioteca", version="0.2.0")

@app.get("/manifest")
async def manifest():
    return {
        "name": SERVICE_NAME,
        "description": "MCP wrapper para API de libros y autores",
        "version": "0.2.0",
        "capabilities": [
            "count_books_by_author",
            "random_authors",
            "search_book_by_year",
            "search_book_by_title",
            "search_author_by_nationality",
            "library_stats",
        ],
    }

@app.post("/provision", response_model=ProvisionResponse)
async def provision(req: ProvisionRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query no puede estar vacía")
    chunks = await gather_context(req.query)
    return ProvisionResponse(chunks=chunks)

# -----------------------------------------------------------------------------
# Ejecución directa (debug)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_biblioteca:app", host="0.0.0.0", port=int(os.getenv("PORT", 8100)), reload=True)
