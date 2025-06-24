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
    """Generates API payloads for compras queries"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate_payload(self, english_question: str) -> str:
        """Generate HTTP request payload for compras API"""
        prompt = (
            "You are a system that reads natural language queries and generates the correct HTTP request payload "
            "to query a REST API for a purchases/shopping database.\n\n"
            "IMPORTANT: You will receive queries from AI agents that tend to be verbose. Extract the CORE intent.\n\n"
            "Common verbose patterns to simplify:\n"
            "- 'How many purchases has [client] made?' → 'compras cliente [client]'\n"
            "- 'Show me a list of products' → 'productos'\n"
            "- 'Products purchased in [year]' → 'productos año [year]'\n"
            "- 'Top selling products' → 'top productos'\n"
            "- 'Clients from [country]' → 'clientes país [country]'\n"
            "- 'Most active client' → 'cliente activo'\n"
            "- 'Out of stock products' → 'sin stock'\n\n"
            "You must:\n"
            "- Focus on the MAIN topic (client name, year, product, country, etc.)\n"
            "- Ignore verbose descriptors like 'comprehensive', 'detailed', 'complete list'\n"
            "- Extract the core intent and map to the appropriate query type\n"
            "- Return a JSON object specifying the method, path (which will be '/provision'), and description\n"
            "- Include the processed query that will be sent to the MCP server\n"
            "- If truly ambiguous, return: { \"error\": \"No appropriate query pattern found.\" }\n\n"
            "### Compras API Specification:\n"
            "The compras API uses a single endpoint POST /provision that accepts natural language queries.\n"
            "The MCP server processes these queries and returns relevant data from the purchases database.\n\n"
            "### Supported Query Patterns:\n"
            "1. **Purchase count by client**: 'cuántas compras ha hecho [nombre]' → Count purchases by client name\n"
            "2. **Random products**: 'lista [N] productos' → Show N random products (default 3)\n"
            "3. **Products by year**: 'productos comprados en [año]' → Products purchased in specific year\n"
            "4. **Top products**: 'top [N] productos más comprados' → Most purchased products (default 3)\n"
            "5. **Clients by country**: 'cuántos clientes de [país]' → Number of clients from country\n"
            "6. **Most active client**: 'cliente más activo' → Client with most purchases\n"
            "7. **Out of stock**: 'productos sin stock' → Products with no stock\n"
            "8. **Products by year range**: 'productos entre [año1] y [año2]' → Products purchased between years\n"
            "9. **General stats**: Any ambiguous query → General database statistics\n\n"
            "### Intent Extraction Rules:\n"
            "- If query mentions 'purchases' + client name → cuántas compras ha hecho [nombre]\n"
            "- If query mentions 'products' or 'list' + number → lista [N] productos\n"
            "- If query mentions 'products' + specific year → productos comprados en [año]\n"
            "- If query mentions 'top' or 'most purchased' + products → top productos más comprados\n"
            "- If query mentions 'clients' + country → cuántos clientes de [país]\n"
            "- If query mentions 'most active' or 'best client' → cliente más activo\n"
            "- If query mentions 'stock' or 'inventory' → productos sin stock\n"
            "- If query mentions year range (between X and Y) → productos entre [año1] y [año2]\n"
            "- If query is general or ambiguous → estadísticas generales\n\n"
            "### Country Name Mapping:\n"
            "- Spanish → España\n"
            "- French → Francia\n"
            "- German → Alemania\n"
            "- Italian → Italia\n"
            "- American/US → Estados Unidos\n"
            "- British/UK → Reino Unido\n\n"
            "### Examples:\n\n"
            "User: \"How many purchases has Juan made?\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"cuántas compras ha hecho Juan\",\n"
            "  \"description\": \"Consultar número de compras realizadas por Juan\"\n"
            "}\n\n"
            "User: \"Show me 5 random products\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"lista 5 productos\",\n"
            "  \"description\": \"Mostrar 5 productos al azar\"\n"
            "}\n\n"
            "User: \"Products purchased in 2023\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"productos comprados en 2023\",\n"
            "  \"description\": \"Productos comprados durante el año 2023\"\n"
            "}\n\n"
            "User: \"Top 3 most purchased products\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"top 3 productos más comprados\",\n"
            "  \"description\": \"Los 3 productos más comprados\"\n"
            "}\n\n"
            "User: \"How many clients from Spain?\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"cuántos clientes de España\",\n"
            "  \"description\": \"Número de clientes de España\"\n"
            "}\n\n"
            "User: \"Who is the most active client?\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"cliente más activo\",\n"
            "  \"description\": \"Cliente con más compras realizadas\"\n"
            "}\n\n"
            "User: \"Products that are out of stock\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"productos sin stock\",\n"
            "  \"description\": \"Productos que no tienen stock disponible\"\n"
            "}\n\n"
            "User: \"Products purchased between 2020 and 2022\"\n"
            "{\n"
            "  \"method\": \"POST\",\n"
            "  \"path\": \"/provision\",\n"
            "  \"query\": \"productos entre 2020 y 2022\",\n"
            "  \"description\": \"Productos comprados entre los años 2020 y 2022\"\n"
            "}\n\n"
            f"Now analyze this query and extract the core intent:\n"
            f"Query: \"{english_question}\"\n\n"
            "Return ONLY the JSON object for the appropriate query. Do not wrap in markdown code blocks."
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
        """Enhanced compras tool with intelligent payload generation and API calls.
        
        IMPORTANT: This tool searches a specific purchases database. If you get results, those are ALL the available results.
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
                
                # Extract the processed query from the payload
                processed_query = payload.get("query", query)
                print(f"🔍 DEBUG - Processed Query: {processed_query}")
                
                # Make MCP call using the processed query
                response = requests.post(COMPRAS_URL, json={"query": processed_query}, timeout=5)
                
                if response.status_code == 200:
                    result_data = response.json()
                    chunks = result_data.get("chunks", [])
                    result = "\n".join(c.get("text", "") for c in chunks)
                    
                    return f"✅ Query: {query}\n📦 Payload: {payload_json}\n📄 Result: {result}"
                else:
                    return f"❌ MCP Error: {response.status_code} - {response.text}\n🔍 URL attempted: {COMPRAS_URL}\n📦 Payload: {payload_json}"
                    
            except json.JSONDecodeError as e:
                print(f"🔍 DEBUG - JSON Decode Error: {e}")
                print(f"🔍 DEBUG - Raw payload: {payload_json}")
                # Fallback to original MCP call with original query
                response = requests.post(COMPRAS_URL, json={"query": query})
                response.raise_for_status()
                chunks = response.json().get("chunks", [])
                return "\n".join(c.get("text", "") for c in chunks)
                
        except Exception as e:
            return f"❌ Error: {str(e)}\n🔍 Query was: {query}"
    
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