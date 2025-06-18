#!/usr/bin/env python3
"""
CLI para TinyLlama + LangChain + MCP
"""

import os
from typing import List
import requests

from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory

from tinyllama_langchain import TinyLlamaLLM
from langchain_tools import biblioteca_tool, compras_tool

MCP_ENDPOINTS = [
    os.getenv("MCP_BIBLIOTECA", "http://127.0.0.1:8100"),
    os.getenv("MCP_COMPRAS", "http://127.0.0.1:8200"),
]


class IntelligentTinyLlama:
    def __init__(self, model_path: str):
        print("🦙 Iniciando TinyLlama LLM y agente LangChain...")
        self.llm = TinyLlamaLLM(model_path=model_path)

        tools = [
            Tool(name="BibliotecaTool", func=biblioteca_tool, description="Consulta sobre libros, autores y publicaciones."),
            Tool(name="ComprasTool", func=compras_tool, description="Consulta sobre productos, stock, clientes y compras."),
        ]

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
        )

    def answer_question(self, question: str) -> str:
        return self.agent.run(question)


def check_mcp_connections():
    print("=" * 60)
    print("🔌 Verificando conexión con los MCP...")
    for url in MCP_ENDPOINTS:
        try:
            r = requests.get(f"{url}/manifest", timeout=3)
            name = r.json().get("name", "¿?")
            print(f"✅ MCP activo en {url} → {name}")
        except Exception as e:
            print(f"❌ No se pudo conectar a {url} → {e}")
    print("=" * 60)


def main():
    check_mcp_connections()

    model_path = "./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    if not os.path.exists(model_path):
        print(f"❌ No se encontró el modelo en {model_path}")
        return

    bot = IntelligentTinyLlama(model_path=model_path)

    print("\n🧠 TinyLlama + LangChain + MCP CLI")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            pregunta = input("👤 Pregunta: ").strip()
            if pregunta.lower() in {"salir", "exit", "quit"}:
                break
            if pregunta:
                print("🤔 Procesando...")
                respuesta = bot.answer_question(pregunta)
                print("\n📖", respuesta)
                print("-" * 60)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print("❌ Error:", exc)

    print("\n👋 Hasta luego")


if __name__ == "__main__":
    main()
