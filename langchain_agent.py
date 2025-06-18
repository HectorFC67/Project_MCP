from tinyllama_langchain import TinyLlamaLLM
from langchain.memory import ConversationBufferMemory
from langchain.agents.agent_types import AgentType
from langchain.agents import initialize_agent
from langchain_tools import biblioteca_tool, compras_tool

llm = TinyLlamaLLM()

tools = [biblioteca_tool, compras_tool] 

memory = ConversationBufferMemory(memory_key="chat_history")

system_msg = (
    "Eres un asistente. Tienes acceso a dos herramientas:\n"
    "- BuscarBiblioteca: para libros, autores, editoriales...\n"
    "- BuscarCompras: para productos, clientes, compras...\n"
    "Para usarlas, llama EXACTAMENTE al nombre indicado arriba. No uses variantes.\n"
    "Por ejemplo, escribe:\n"
    "Action: BuscarBiblioteca\n"
    "Action Input: 'Gabriel García Márquez'\n"
    "Nunca uses nombres como 'Buscar en la biblioteca' o similares."
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    system_message=system_msg
)

def answer_user_question(question: str):
    return agent.invoke(question)