from langchain.tools import tool
import requests
import json
from typing import Dict, Any

BIBLIOTECA_URL = "http://127.0.0.1:8100/provision"
COMPRAS_URL = "http://127.0.0.1:8200/provision"

class ResponseValidator:
    """Validates response quality and adequacy"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def validate_response(self, original_question: str, model_response: str) -> Dict[str, Any]:
        """Validates if a response is adequate, partially adequate, or inadequate"""
        prompt = (
            "Eres un modelo validador. Tu tarea es evaluar si la respuesta proporcionada es adecuada, "
            "clara, relevante y útil con respecto al contexto y la pregunta original del usuario. "
            "Debes basarte en la lógica, la coherencia y la precisión de la información dada. "
            "Responde únicamente con uno de los siguientes valores:\n\n"
            "- \"ADECUADA\" si la respuesta cumple correctamente con la intención de la pregunta.\n"
            "- \"PARCIALMENTE ADECUADA\" si responde en parte o le falta claridad o precisión.\n"
            "- \"INADECUADA\" si no responde correctamente a la pregunta o es irrelevante.\n\n"
            "Luego, proporciona una breve explicación en 2-3 frases justificando tu valoración.\n\n"
            f"Pregunta del usuario: {original_question}\n"
            f"Respuesta del modelo: {model_response}\n\n"
            "Responde en formato JSON: {{\"veredicto\": \"...\", \"explicación\": \"...\"}}"
        )
        
        try:
            validation_result = self.llm.invoke(prompt)
            return {"validation": validation_result}
        except Exception as e:
            return {"validation": f"Error en validación: {str(e)}"}

class BibliotecaPayloadGenerator:
    """Generates API payloads for biblioteca queries"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate_payload(self, english_question: str) -> str:
        """Generate HTTP request payload for biblioteca API"""
        prompt = (
            "You are a system that reads natural language queries and generates the correct HTTP request payload "
            "to query a REST API for a digital library.\n\n"
            "IMPORTANT: You will receive queries from AI agents that tend to be verbose. Extract the CORE intent.\n\n"
            "Common verbose patterns to simplify:\n"
            "- 'Books by [nationality] authors or related to [nationality] culture' → '[nationality] books'\n"
            "- 'Comprehensive list of seminal [nationality] books including titles, authors, genres' → '[nationality] books'\n"
            "- 'Search for books related to [nationality] literature' → '[nationality] books'\n"
            "- 'Information about [nationality] literary works and cultural significance' → '[nationality] books'\n\n"
            "You must:\n"
            "- Focus on the MAIN topic (nationality, year, title, etc.)\n"
            "- Ignore verbose descriptors like 'comprehensive', 'seminal', 'cultural context'\n"
            "- Extract the core intent and map to the appropriate endpoint\n"
            "- Return a JSON object specifying the HTTP method, endpoint path, and description\n"
            "- If truly ambiguous, return: { \"error\": \"No appropriate endpoint found for the given query.\" }\n\n"
            "### Biblioteca API Specification:\n"
            "1. GET /autores/ → Returns all authors.\n"
            "2. GET /autores/buscar/por-nacionalidad/{pais} → Authors from a country.\n"
            "3. GET /libros/ → Returns all books.\n"
            "4. GET /libros/autor/{id} → Books by author ID (if known).\n"
            "5. GET /libros/buscar/por-anio/{anio} → Books from a specific year.\n"
            "6. GET /libros/buscar/titulo/{titulo} → Books with a specific title.\n"
            "7. GET /stats → Library stats.\n\n"
            "### Intent Extraction Rules:\n"
            "- If query specifically mentions 'books' or 'libros' or 'obras' + nationality → /libros/ (to get all books, then filter)\n"
            "- If query mentions 'authors' or 'autores' + nationality → /autores/buscar/por-nacionalidad/{country}\n"
            "- If query mentions nationality alone (ambiguous) → /autores/buscar/por-nacionalidad/{country}\n"
            "- If query mentions specific year + (books|published) → /libros/buscar/por-anio/{year}\n"
            "- If query mentions specific book title → /libros/buscar/titulo/{title}\n"
            "- If query asks for (statistics|stats|numbers|count) → /stats\n"
            "- If query asks for 'all books' or 'all authors' → /libros/ or /autores/\n\n"
            "### Country Name Mapping:\n"
            "- Chilean → Chile\n"
            "- Colombian → Colombia\n"
            "- Mexican → Mexico\n"
            "- Argentinian/Argentine → Argentina\n"
            "- Peruvian → Peru\n"
            "- Brazilian → Brazil\n\n"
            "### Examples:\n\n"
            "User: \"Chilean books\"\n"
            "{\n"
            "  \"method\": \"GET\",\n"
            "  \"path\": \"/libros/\",\n"
            "  \"description\": \"Buscar todos los libros para filtrar por autores chilenos\"\n"
            "}\n\n"
            "User: \"Chilean authors\"\n"
            "{\n"
            "  \"method\": \"GET\",\n"
            "  \"path\": \"/autores/buscar/por-nacionalidad/Chile\",\n"
            "  \"description\": \"Buscar autores chilenos\"\n"
            "}\n\n"
            "User: \"Books by Chilean authors or related to Chilean culture\"\n"
            "{\n"
            "  \"method\": \"GET\",\n"
            "  \"path\": \"/libros/\",\n"
            "  \"description\": \"Buscar todos los libros para filtrar por autores chilenos\"\n"
            "}\n\n"
            "User: \"Obras de autores chilenos\"\n"
            "{\n"
            "  \"method\": \"GET\",\n"
            "  \"path\": \"/libros/\",\n"
            "  \"description\": \"Buscar libros de autores chilenos\"\n"
            "}\n\n"
            "User: \"Comprehensive list of seminal Chilean books including titles, authors, genres, and historical context\"\n"
            "{\n"
            "  \"method\": \"GET\",\n"
            "  \"path\": \"/libros/\",\n"
            "  \"description\": \"Buscar todos los libros para filtrar literatura chilena\"\n"
            "}\n\n"
            f"Now analyze this query and extract the core intent:\n"
            f"Query: \"{english_question}\"\n\n"
            "Return ONLY the JSON object for the appropriate endpoint. Do not wrap in markdown code blocks."
        )
        
        # Get response from LLM
        response = self.llm.invoke(prompt)
        
        # Extract content from LangChain response object
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        # Clean up markdown formatting if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.startswith('```'):
            content = content[3:]   # Remove ```
        if content.endswith('```'):
            content = content[:-3]  # Remove trailing ```
        
        return content.strip()

class ComprasPayloadGenerator:
    """Generates API payloads for compras queries (placeholder for future implementation)"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate_payload(self, english_question: str) -> str:
        """Generate HTTP request payload for compras API"""
        # Placeholder implementation
        return json.dumps({
            "method": "GET",
            "path": "/compras/placeholder",
            "description": "Compras payload generation not yet implemented",
            "query": english_question
        })

class ToolSelector:
    """Intelligent tool selection based on user queries"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def select_tool(self, english_question: str) -> str:
        """Select the most appropriate tool for the given question"""
        prompt = (
            "You are an assistant that must select ONE tool name based on the user's question.\n"
            "Return ONLY ONE of the following strings:\n"
            "1. BuscarBiblioteca\n"
            "2. BuscarCompras\n"
            "3. ERROR: No suitable tool\n\n"
            "Tool descriptions:\n"
            "- BuscarBiblioteca: For queries about books, authors, publishing years, nationalities, library statistics.\n"
            "- BuscarCompras: For queries about clients, purchases, products, stock, sales.\n\n"
            f"User: \"{english_question}\"\n"
            "Answer:"
        )
        return self.llm.invoke(prompt).strip()

# Enhanced tools with validation and payload generation
def create_enhanced_biblioteca_tool(llm):
    """Create enhanced biblioteca tool with payload generation"""
    payload_generator = BibliotecaPayloadGenerator(llm)
    
    @tool
    def enhanced_biblioteca_tool(query: str) -> str:
        """Enhanced biblioteca tool with intelligent payload generation and API calls.
        
        IMPORTANT: This tool searches a specific database. If you get results, those are ALL the available results.
        Do NOT call this tool multiple times with similar queries expecting different results.
        The database may have limited entries, so accept the results you get as complete."""
        try:
            # Generate payload
            payload_json = payload_generator.generate_payload(query)
            print(f"🔍 DEBUG - Query: {query}")
            print(f"🔍 DEBUG - Generated Payload: {payload_json}")
            
            # Try to parse the payload
            try:
                payload = json.loads(payload_json)
                if "error" in payload:
                    return f"❌ {payload['error']}"
                
                # Make API call using the generated payload
                api_url = f"http://127.0.0.1:8000{payload.get('path', '')}"
                print(f"🔍 DEBUG - API URL: {api_url}")
                
                response = requests.get(api_url, timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    return f"✅ Query: {query}\n📦 Payload: {payload_json}\n📄 Result: {json.dumps(result, indent=2)}"
                else:
                    return f"❌ API Error: {response.status_code} - {response.text}\n🔍 URL attempted: {api_url}\n📦 Payload: {payload_json}"
                    
            except json.JSONDecodeError as e:
                print(f"🔍 DEBUG - JSON Decode Error: {e}")
                print(f"🔍 DEBUG - Raw payload: {payload_json}")
                # Fallback to original MCP call
                response = requests.post(BIBLIOTECA_URL, json={"query": query})
                response.raise_for_status()
                chunks = response.json().get("chunks", [])
                return "\n".join(c.get("text", "") for c in chunks)
                
        except Exception as e:
            return f"❌ Error: {str(e)}\n🔍 Query was: {query}"
    
    return enhanced_biblioteca_tool

def create_enhanced_compras_tool(llm):
    """Create enhanced compras tool with payload generation"""
    payload_generator = ComprasPayloadGenerator(llm)
    
    @tool
    def enhanced_compras_tool(query: str) -> str:
        """Enhanced compras tool with intelligent payload generation."""
        try:
            # Generate payload
            payload_json = payload_generator.generate_payload(query)
            
            # For now, fallback to original MCP call
            response = requests.post(COMPRAS_URL, json={"query": query})
            response.raise_for_status()
            chunks = response.json().get("chunks", [])
            result = "\n".join(c.get("text", "") for c in chunks)
            
            return f"📦 Generated Payload: {payload_json}\n📄 Result: {result}"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    return enhanced_compras_tool

# Original tools (maintained for backward compatibility)
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