from langgraph.graph import StateGraph, END
from langchain_tools import biblioteca_tool, compras_tool


def decide_tool(state):
    question = state["input"].lower()
    if any(word in question for word in ["libro", "autor", "editorial", "publicación"]):
        return "biblioteca_node"
    elif any(word in question for word in ["producto", "cliente", "compra", "stock"]):
        return "compras_node"
    return "fallback_node"


graph = StateGraph()

# Nodos de procesamiento

graph.add_node("biblioteca_node", lambda state: {"result": biblioteca_tool(state["input"])})
graph.add_node("compras_node", lambda state: {"result": compras_tool(state["input"])})
graph.add_node("fallback_node", lambda state: {"result": "No se pudo determinar el dominio de la consulta."})

graph.set_entry_point("decide")
graph.add_conditional_edges("decide", decide_tool, {
    "biblioteca_node": "biblioteca_node",
    "compras_node": "compras_node",
    "fallback_node": "fallback_node"
})

graph.add_edge("biblioteca_node", END)
graph.add_edge("compras_node", END)
graph.add_edge("fallback_node", END)

flow = graph.compile()

def run_flow(question: str):
    return flow.invoke({"input": question})