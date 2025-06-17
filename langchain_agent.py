from langchain.agents import initialize_agent, Tool
from tinyllama_langchain import TinyLlamaLLM
from langchain.memory import ConversationBufferMemory
from langchain.agents.agent_types import AgentType
from langchain_tools import biblioteca_tool, compras_tool

# Instanciamos herramientas y LLM
llm = TinyLlamaLLM()
tools = [
    Tool(name="BibliotecaTool", func=biblioteca_tool, description="Consulta información de libros y autores."),
    Tool(name="ComprasTool", func=compras_tool, description="Consulta información de compras, productos y clientes."),
]

memory = ConversationBufferMemory(memory_key="chat_history")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

def answer_user_question(question: str):
    return agent.run(question)
