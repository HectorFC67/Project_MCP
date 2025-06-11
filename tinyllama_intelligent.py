#!/usr/bin/env python3
"""
TinyLlama + MCP v0.4.1
=====================
• Mejora `_prettify_chunk` para manejar cadenas que contienen **listas de dicts
  representadas con comillas simples** (el caso que aparecía como:
  `Autores de chile: [{'id': 2, 'nombre': 'Isabel…'}, …]`).
• Si detecta ese patrón, convierte con `ast.literal_eval` y redacta frase
  amigable.
"""

import os
import json
import re
import ast
from textwrap import shorten
from typing import List, Optional

import requests

try:
    from llama_cpp import Llama  # type: ignore
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️  llama‑cpp‑python no está instalado. Se usará modo heurístico.")

MCP_BASE_URL = os.getenv("MCP_BIBLIOTECA", "http://127.0.0.1:8100")
MAX_CHUNK_CHARS = 2_000

# -------------------------------------------------------------
# Utilidades de formato «natural» cuando no hay modelo
# -------------------------------------------------------------

def _format_list_of_dicts(lst: List[dict]) -> str:
    if not lst:
        return "(sin resultados)"
    if "titulo" in lst[0]:
        titulos = ", ".join(d.get("titulo", "¿?") for d in lst[:5])
        extra = "…" if len(lst) > 5 else ""
        return f"Se encontraron {len(lst)} libro(s): {titulos}{extra}."
    if "nombre" in lst[0]:
        nombres = ", ".join(d.get("nombre", "¿?") for d in lst[:5])
        extra = "…" if len(lst) > 5 else ""
        return f"Autores: {nombres}{extra}."
    return ", ".join(str(d) for d in lst)


def _prettify_chunk(text: str) -> str:
    """Convierte la mayoría de textos devueltos por MCP en frases legibles."""
    # 1) ¿Es JSON válido?
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return _format_list_of_dicts(data)
        if isinstance(data, dict):
            if {"total_autores", "total_libros"}.issubset(data.keys()):
                return (
                    f"La biblioteca cuenta con {data['total_autores']} autores y "
                    f"{data['total_libros']} libros (publicados entre "
                    f"{data['rango_años_publicacion']['año_mas_antiguo']} y "
                    f"{data['rango_años_publicacion']['año_mas_reciente']})."
                )
            if "nombre" in data:
                return f"Autor: {data['nombre']} ({data.get('nacionalidad','?')})."
            if "titulo" in data:
                return f"Libro: “{data['titulo']}” ({data.get('anio_publicacion','?')})."
    except Exception:
        pass

    # 2) Detecta patrón "Texto: [ { … } , … ]" con comillas simples
    m = re.search(r":\s*(\[\{.*\}\])", text)
    if m:
        try:
            py_obj = ast.literal_eval(m.group(1))  # convierte a lista de dicts
            return _format_list_of_dicts(py_obj)
        except Exception:
            pass

    # 3) Detecta lista de dicts sin prefijo
    if text.strip().startswith("[") and text.strip().endswith("]"):
        try:
            py_obj = ast.literal_eval(text)
            if isinstance(py_obj, list):
                return _format_list_of_dicts(py_obj)
        except Exception:
            pass

    # 4) Limpieza ligera de listas de strings entre comillas
    text = re.sub(r"\['([^']+)'(?:, '([^']+)')*\]", lambda m: m.group(0).replace("[","").replace("]","").replace("'",""), text)
    pretty = text.strip()
    if pretty and not pretty.endswith(('.', '…', '"')):
        pretty += '.'
    return pretty

# -------------------------------------------------------------
# Host principal (sin cambios en la lógica)
# -------------------------------------------------------------
class IntelligentTinyLlama:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if LLAMA_CPP_AVAILABLE and model_path:
            try:
                print("🦙 Cargando TinyLlama …")
                self.model = Llama(model_path=model_path, n_ctx=4096, n_threads=4, verbose=False)
                print("✅ TinyLlama cargado")
            except Exception as exc:
                print(f"❌ No se pudo cargar el modelo: {exc}")

    @staticmethod
    def _call_mcp(question: str) -> List[str]:
        try:
            r = requests.post(f"{MCP_BASE_URL}/provision", json={"query": question}, timeout=10)
            r.raise_for_status()
            return [c.get("text", "") for c in r.json().get("chunks", [])]
        except Exception as exc:
            print("⚠️  Error llamando a MCP:", exc)
            return []

    def answer_question(self, question: str) -> str:
        chunks = self._call_mcp(question)
        context_text = "\n".join(shorten(c, MAX_CHUNK_CHARS) for c in chunks)

        if self.model:
            prompt = (
                "### Contexto:\n" + context_text +
                "\n\n### Pregunta:\n" + question +
                "\n\n### Responde en español natural, claro y conciso:\n"
            )
            out = self.model(prompt, max_tokens=320, temperature=0.6, stop=["###"])
            return out["choices"][0]["text"].strip()

        if not chunks:
            return "Lo siento, no encontré información para tu pregunta."

        if len(chunks) == 1:
            return _prettify_chunk(chunks[0])

        partes = ["Aquí tienes la información relevante:"]
        for idx, ch in enumerate(chunks, 1):
            partes.append(f"{idx}. {_prettify_chunk(ch)}")
        return "\n".join(partes)

# -------------------------------------------------------------
# CLI (igual que antes)
# -------------------------------------------------------------

def main():
    print("🧠 TinyLlama + MCP |", MCP_BASE_URL)
    print("=" * 60)

    try:
        r = requests.get(f"{MCP_BASE_URL}/manifest", timeout=5)
        r.raise_for_status()
        print("✅ MCP‑Server conectado →", r.json().get("name"))
    except Exception as exc:
        print("❌ No se pudo acceder al MCP‑Server:", exc)
        return

    model_path = "./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    bot = IntelligentTinyLlama(model_path if os.path.exists(model_path) else None)

    print("\nEscribe 'salir' para terminar.\n")
    while True:
        try:
            q = input("👤 Pregunta: ").strip()
            if q.lower() in {"salir", "exit", "quit"}:
                break
            if q:
                print("🤔 Buscando …")
                ans = bot.answer_question(q)
                print("\n📖 " + ans + "\n")
                print("-" * 60)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print("❌ Error inesperado:", exc)

    print("\n👋 Hasta luego")


if __name__ == "__main__":
    main()
