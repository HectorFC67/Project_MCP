#!/usr/bin/env python3
"""
TinyLlama + MCP (v0.3)
=====================
Este Host ya **no** consulta la API directa; en su lugar envía la pregunta al
*MCP‑Server* (`mcp_biblioteca.py`) mediante el endpoint `/provision` y recibe un
`ContextBundle` con fragmentos relevantes.

Flujo:
1. El usuario pregunta → `answer_question()`
2. `_call_mcp()` hace `POST http://127.0.0.1:8100/provision` con `{query}`
3. Concatenamos los `chunks[].text` para formar `context_text`
4. Añadimos esa información al *prompt* y llamamos al modelo (si está cargado)
5. Si no hay modelo, respondemos con un resumen rápido de los chunks.

> **Requisitos**
> ‑ MCP‑Server levantado en `localhost:8100` (puerto configurable por env)
> ‑ Python 3.10‑3.12 si quieres usar `llama_cpp`. Con 3.13 se ejecutará en modo heurístico.
"""

import os
import json
import re
from textwrap import shorten
from typing import List, Optional

import requests

# -------------------------------------------------------------
# Carga opcional de llama‑cpp‑python
# -------------------------------------------------------------
try:
    from llama_cpp import Llama  # type: ignore
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️  llama‑cpp‑python no está instalado. Se usará modo heurístico.")

# -------------------------------------------------------------
# Configuración global
# -------------------------------------------------------------
MCP_BASE_URL = os.getenv("MCP_BIBLIOTECA", "http://127.0.0.1:8100")
MAX_CHUNK_CHARS = 2_000  # límite de contexto pegado al prompt

# -------------------------------------------------------------
# Clase principal
# -------------------------------------------------------------
class IntelligentTinyLlama:
    """Host que obtiene contexto vía MCP y se lo pasa a TinyLLaMA."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if LLAMA_CPP_AVAILABLE and model_path:
            try:
                print("🦙 Cargando TinyLlama …")
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_threads=4,
                    verbose=False,
                )
                print("✅ TinyLlama cargado")
            except Exception as exc:
                print(f"❌ No se pudo cargar el modelo: {exc}")

    # =========================================================
    # 1. Solicitar contexto al MCP‑Server
    # =========================================================
    @staticmethod
    def _call_mcp(question: str) -> List[str]:
        try:
            resp = requests.post(
                f"{MCP_BASE_URL}/provision",
                json={"query": question},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return [c.get("text", "") for c in data.get("chunks", [])]
        except Exception as exc:
            print(f"⚠️  Error llamando a MCP: {exc}")
            return []

    # =========================================================
    # 2. Construir prompt y generar respuesta
    # =========================================================
    def answer_question(self, question: str) -> str:
        # ----- obtener contexto -----
        chunks = self._call_mcp(question)
        context_text = "\n".join(shorten(c, MAX_CHUNK_CHARS) for c in chunks)

        if self.model:
            prompt = (
                "### Contexto proporcionado:\n" + context_text +
                "\n\n### Pregunta del usuario:\n" + question +
                "\n\n### Respuesta (sé claro y conciso):\n"
            )
            output = self.model(prompt, max_tokens=300, temperature=0.7, stop=["###"])
            return output["choices"][0]["text"].strip()

        # ----- modo heurístico si no hay LLM -----
        if not chunks:
            return "No encontré información para tu pregunta."

        # pequeña heurística: si sólo viene un chunk lo devolvemos limpio,
        # si hay varios los enumeramos.
        if len(chunks) == 1:
            return chunks[0]

        response_lines = ["📚 Información relevante:"]
        for idx, ch in enumerate(chunks, 1):
            response_lines.append(f"{idx}. {shorten(ch, 250)}")
        return "\n".join(response_lines)

# -------------------------------------------------------------
# CLI interactivo
# -------------------------------------------------------------

def main() -> None:
    print("🧠 TinyLlama + MCP | puerto", MCP_BASE_URL)
    print("=" * 60)

    # comprobación rápida de MCP
    try:
        m = requests.get(f"{MCP_BASE_URL}/manifest", timeout=5)
        assert m.status_code == 200
        print("✅ MCP‑Server conectado →", m.json().get("name"))
    except Exception as exc:
        print("❌ No se pudo acceder al MCP‑Server:", exc)
        return

    model_path = "./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    assistant = IntelligentTinyLlama(model_path if os.path.exists(model_path) else None)

    print("\nEscribe 'salir' para terminar.\n")
    while True:
        try:
            q = input("👤 Pregunta: ").strip()
            if q.lower() in {"salir", "exit", "quit"}:
                break
            if q:
                print("🤔 Consultando MCP …")
                ans = assistant.answer_question(q)
                print("\n📖 Respuesta:\n" + ans + "\n")
                print("-" * 60)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print("❌ Error inesperado:", exc)

    print("\n👋 Hasta luego")


if __name__ == "__main__":
    main()
