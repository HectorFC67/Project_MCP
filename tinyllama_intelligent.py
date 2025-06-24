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
from deep_translator import GoogleTranslator

from tinyllama_langchain import TinyLlamaLLM
from langchain_tools import (
    biblioteca_tool, 
    compras_tool, 
    ResponseValidator, 
    create_enhanced_biblioteca_tool,
    create_enhanced_compras_tool
)
from dotenv import load_dotenv
load_dotenv()

MCP_ENDPOINTS = [
    os.getenv("MCP_BIBLIOTECA", "http://127.0.0.1:8100"),
    os.getenv("MCP_COMPRAS", "http://127.0.0.1:8200"),
]

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

class OpenRouterLLM:
    def __init__(self, model="deepseek/deepseek-r1-0528:free"):
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            model=model
        )

    def invoke(self, prompt: str) -> str:
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content.strip()

class IntelligentOpenRouter:
    def __init__(self):
        print("🤖 Iniciando OpenRouter LLM y agente LangChain...")
        self.llm = OpenRouterLLM()
        self.validator = ResponseValidator(self.llm)
        
        # Create enhanced tools that already do everything we need
        self.enhanced_biblioteca = create_enhanced_biblioteca_tool(self.llm)
        self.enhanced_compras = create_enhanced_compras_tool(self.llm)
        
        # Create LangChain agent with enhanced tools
        tools = [self.enhanced_biblioteca, self.enhanced_compras]
        memory = ConversationBufferMemory(memory_key="chat_history")
        
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm.llm,  # Use the ChatOpenAI instance
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,  # Limit iterations to prevent infinite loops
            early_stopping_method="generate"
        )

    def translate_to_english(self, question: str) -> str:
        """Translate user question to English for better LLM processing"""
        try:
            return GoogleTranslator(source='auto', target='en').translate(question)
        except Exception as e:
            print(f"⚠️ Translation error: {e}, using original question")
            return question

    def translate_to_spanish(self, text: str) -> str:
        """Translate agent response back to Spanish for user"""
        try:
            return GoogleTranslator(source='en', target='es').translate(text)
        except Exception as e:
            print(f"⚠️ Translation error: {e}, using original text")
            return text

    def answer_question(self, question: str) -> str:
        # First translate to English for better processing
        translated = self.translate_to_english(question).strip()
        
        try:
            # Let the agent handle everything with translated question
            agent_response = self.agent.invoke({"input": translated})
            result = agent_response.get("output", "No response from agent")
            
            # Extract only the final answer if it exists
            final_answer = result
            if "Final Answer:" in result or "Final Answer" in result:
                final_answer = result.split("Final Answer")[-1].strip()
            
            # Translate the final answer back to Spanish
            spanish_result = self.translate_to_spanish(final_answer)
            
            # Create a clean Spanish response
            full_response = (
                f"📥 Original Question: {question}\n"
                f"🌐 Translated to English: {translated}\n"
                f"🤖 Agent Response:\n{result}\n"
                f"💃 Actual Response:\n{spanish_result}"
            )
            
            # Validate the complete response
            validation = self.validator.validate_response(question, full_response)
            
            return f"{full_response}\n\n🔍 Validación: {validation['validation']}"
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}\n📥 Pregunta: {question}"
            validation = self.validator.validate_response(question, error_msg)
            return f"{error_msg}\n\n🔍 Validación: {validation['validation']}"

# Keep the TinyLlama version for comparison
class IntelligentTinyLlama:
    def __init__(self, model_path: str):
        print("🦙 Iniciando TinyLlama LLM y agente LangChain...")
        self.llm = TinyLlamaLLM(model_path=model_path)
        self.validator = ResponseValidator(self.llm)
        
        # Use original tools for TinyLlama (since enhanced tools need OpenAI-compatible LLM)
        tools = [biblioteca_tool, compras_tool]
        memory = ConversationBufferMemory(memory_key="chat_history")
        
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )

    def answer_question(self, question: str) -> str:
        try:
            agent_response = self.agent.invoke({"input": question})
            result = agent_response.get("output", "No response from agent")
            
            validation = self.validator.validate_response(question, result)
            return f"{result}\n\n🔍 Validation: {validation['validation']}"
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            validation = self.validator.validate_response(question, error_msg)
            return f"{error_msg}\n\n🔍 Validation: {validation['validation']}"

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
        print("Usando OpenRouter en su lugar...")

    bot = IntelligentOpenRouter()

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
                print(respuesta)
                print("-" * 60)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print("❌ Error:", exc)

    print("\n👋 Hasta luego")

if __name__ == "__main__":
    main()




