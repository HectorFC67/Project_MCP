#!/usr/bin/env python3
"""
MCP‑Server Compras v1.0 (sin API, con BD local SQLite)
"""

import re
import random
import sqlite3
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = "BD/LLM.db"
SERVICE_NAME = "compras_bd"

# ----------------------------- MODELOS -----------------------------
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

# ---------------------------- UTILIDADES ----------------------------
def query_db(sql: str, params: tuple = ()) -> List[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# --------------------------- CONTEXTO ---------------------------
async def gather_context(query: str) -> List[Chunk]:
    q = query.lower()
    chunks: List[Chunk] = []

    # 1. ¿Cuántas compras ha hecho X?
    m = re.search(r"cu[aá]ntas compras ha (hecho|realizado) ([\w\s]+)", q)
    if m:
        nombre = m.group(2).strip()
        rows = query_db("SELECT COUNT(*) as total FROM Compra JOIN Cliente ON Compra.Comprador = Cliente.DNI WHERE LOWER(Cliente.Nombre || ' ' || Cliente.Apellidos) LIKE ?", (f"%{nombre.lower()}%",))
        if rows:
            total = rows[0]["total"]
            chunks.append(Chunk(
                text=f"{nombre} ha realizado {total} compra(s).",
                source="BD: Compra + Cliente"
            ))
            return chunks

    # 2. Lista N productos al azar
    m = re.search(r"(lista|muestra)\s*(\d+)?\s*productos", q)
    if m:
        n = int(m.group(2) or 3)
        productos = query_db("SELECT Nombre FROM Producto")
        muestra = random.sample(productos, min(n, len(productos)))
        nombres = ", ".join(p["Nombre"] for p in muestra)
        chunks.append(Chunk(
            text=f"Productos al azar: {nombres}",
            source="BD: Producto"
        ))
        return chunks

    # 3. Productos comprados en un año
    m = re.search(r"(comprados|compras).*en\s+(\d{4})", q)
    if m:
        año = m.group(2)
        rows = query_db("""
            SELECT DISTINCT p.Nombre
            FROM Producto p
            JOIN CompraProd cp ON cp.Producto = p.ID
            JOIN Compra c ON c.ID = cp.Compra
            WHERE c.Fecha LIKE ?
        """, (f"{año}%",))
        nombres = ", ".join(r["Nombre"] for r in rows)
        chunks.append(Chunk(text=f"Productos comprados en {año}: {nombres}", source="BD: CompraProd + Compra + Producto"))
        return chunks

    # 4. Productos más comprados (top N)
    m = re.search(r"(top|más)\s*(\d+)?\s*(productos|artículos).*comprados", q)
    if m:
        n = int(m.group(2) or 3)
        rows = query_db("""
            SELECT p.Nombre, SUM(cp.Cantidad) as total
            FROM Producto p
            JOIN CompraProd cp ON cp.Producto = p.ID
            GROUP BY p.ID
            ORDER BY total DESC
            LIMIT ?
        """, (n,))
        resumen = ", ".join(f"{r['Nombre']} ({r['total']})" for r in rows)
        chunks.append(Chunk(text=f"Top productos más comprados: {resumen}", source="BD: CompraProd + Producto"))
        return chunks

    # 5. Número de clientes por país
    m = re.search(r"(cu[aá]ntos|número de)\s+clientes.*(pa[ií]s|país)\s+([\w\s]+)", q)
    if m:
        pais = m.group(3).strip().capitalize()
        rows = query_db("SELECT COUNT(*) as total FROM Cliente WHERE LOWER(País) = ?", (pais.lower(),))
        total = rows[0]["total"]
        chunks.append(Chunk(text=f"Clientes de {pais}: {total}", source="BD: Cliente"))
        return chunks

    # 6. Cliente más activo (más compras)
    if "cliente más activo" in q or "cliente que más ha comprado" in q:
        rows = query_db("""
            SELECT c.Nombre || ' ' || c.Apellidos as nombre, COUNT(*) as total
            FROM Compra co
            JOIN Cliente c ON co.Comprador = c.DNI
            GROUP BY c.DNI
            ORDER BY total DESC
            LIMIT 1
        """)
        if rows:
            nombre, total = rows[0]["nombre"], rows[0]["total"]
            chunks.append(Chunk(text=f"El cliente más activo es {nombre} con {total} compras.", source="BD: Compra + Cliente"))
            return chunks

    # 7. Productos sin stock
    if "sin stock" in q or "fuera de stock" in q:
        rows = query_db("SELECT Nombre FROM Producto WHERE Stock <= 0")
        nombres = ", ".join(r["Nombre"] for r in rows) if rows else "Ninguno"
        chunks.append(Chunk(text=f"Productos sin stock: {nombres}", source="BD: Producto"))
        return chunks

    # 8. Compras entre dos años
    m = re.search(r"entre\s*(\d{4})\s*y\s*(\d{4})", q)
    if m:
        y1, y2 = sorted(map(int, m.groups()))
        rows = query_db("""
            SELECT DISTINCT p.Nombre
            FROM Producto p
            JOIN CompraProd cp ON cp.Producto = p.ID
            JOIN Compra c ON c.ID = cp.Compra
            WHERE c.Fecha BETWEEN ? AND ?
        """, (f"{y1}-01-01", f"{y2}-12-31"))
        nombres = ", ".join(r["Nombre"] for r in rows)
        chunks.append(Chunk(text=f"Productos comprados entre {y1} y {y2}: {nombres}", source="BD: CompraProd + Compra + Producto"))
        return chunks

    # Fallback: contar clientes, productos y compras
    stats = {
        "clientes": query_db("SELECT COUNT(*) as total FROM Cliente")[0]["total"],
        "productos": query_db("SELECT COUNT(*) as total FROM Producto")[0]["total"],
        "compras": query_db("SELECT COUNT(*) as total FROM Compra")[0]["total"],
    }
    chunks.append(Chunk(
        text=f"Estadísticas: {stats['clientes']} clientes, {stats['productos']} productos, {stats['compras']} compras.",
        source="BD: General"
    ))
    return chunks

# ------------------------- FASTAPI -------------------------
app = FastAPI(title="MCP Compras", version="1.0")

@app.get("/manifest")
async def manifest():
    return {
        "name": SERVICE_NAME,
        "description": "MCP wrapper usando base de datos local de compras",
        "version": "1.0",
        "capabilities": [
            "count_purchases_by_client",
            "random_products",
            "search_products_by_year",
            "top_products",
            "clients_by_country",
            "most_active_client",
            "out_of_stock",
            "products_by_year_range",
        ],
    }

@app.post("/provision", response_model=ProvisionResponse)
async def provision(req: ProvisionRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query no puede estar vacía")
    chunks = await gather_context(req.query)
    return ProvisionResponse(chunks=chunks)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_compras:app", host="0.0.0.0", port=8200, reload=True)
