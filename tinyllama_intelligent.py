#!/usr/bin/env python3
"""
TinyLlama Inteligente - Le damos toda la documentación de la API 
y que él decida qué endpoints usar según la pregunta.
"""

import sys
import json
import re
import requests
import asyncio
import httpx
from typing import Dict, Any, Optional, List

# Verificar llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️  llama-cpp-python no está instalado.")

class IntelligentTinyLlama:
    """TinyLlama que decide qué APIs usar por sí mismo"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.api_base_url = "http://127.0.0.1:8000"
        
        if LLAMA_CPP_AVAILABLE and model_path:
            try:
                print(f"🦙 Cargando TinyLlama...")
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_threads=4,
                    verbose=False
                )
                print("✅ TinyLlama cargado")
            except Exception as e:
                print(f"❌ Error: {e}")
                self.model = None
    
    def _get_api_docs(self) -> str:
        """Documentación completa de la API"""
        return """
🔍 API BIBLIOTECA - http://127.0.0.1:8000

ENDPOINTS DISPONIBLES:

📚 AUTORES:
• GET /autores/ → Lista todos los autores
• GET /autores/{id} → Autor específico (ej: /autores/1)
• GET /autores/buscar/por-nacionalidad/{nacionalidad} → Autores por país (ej: /autores/buscar/por-nacionalidad/Chileno)

📖 LIBROS:
• GET /libros/ → Lista todos los libros
• GET /libros/{id} → Libro específico (ej: /libros/1)
• GET /libros/autor/{autor_id} → Libros de un autor (ej: /libros/autor/1)
• GET /libros/buscar/por-anio/{anio} → Libros por año (ej: /libros/buscar/por-anio/ 7)
• GET /libros/buscar/titulo/{termino} → Libros por título (ej: /libros/buscar/titulo/amor)

📊 DATOS:
• GET /stats → Estadísticas generales

ESTRATEGIAS PARA DECIDIR QUÉ ENDPOINT USAR:

1. Para preguntas sobre AUTORES específicos:
   - Si mencionan nombre: usar /autores/ primero, luego /libros/autor/{id}
   - Si mencionan nacionalidad: usar /autores/buscar/por-nacionalidad/{país}

2. Para preguntas sobre LIBROS:
   - Si mencionan título: usar /libros/buscar/titulo/{palabra}
   - Si mencionan año: usar /libros/buscar/por-anio/{año}
   - Si preguntan por autor: primero encontrar autor ID, luego /libros/autor/{id}

3. Para CANTIDADES/ESTADÍSTICAS:
   - Usar /stats para números totales
   - Combinar con búsquedas específicas

EJEMPLOS DE RAZONAMIENTO:
"¿Qué libros tiene García Márquez?" → 
  1. /autores/ (encontrar su ID)
  2. /libros/autor/1 (sus libros)

"¿Cuántos autores chilenos hay?" →
  1. /autores/buscar/por-nacionalidad/Chileno

"¿Qué se publicó en 1967?" →
  1. /libros/buscar/por-anio/1967
"""
    
    def _call_api(self, url: str) -> str:
        """Llama a la API"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return json.dumps(response.json(), ensure_ascii=False, indent=2)
            else:
                return f"Error HTTP {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extrae URLs que TinyLlama quiere consultar"""
        patterns = [
            r'GET\s+(http://127\.0\.0\.1:8000/[^\s\n]+)',
            r'URL:\s*(http://127\.0\.0\.1:8000/[^\s\n]+)',
            r'(http://127\.0\.0\.1:8000/[^\s\n]+)',
        ]
        
        urls = []
        for pattern in patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Eliminar duplicados
        return list(dict.fromkeys(urls))
    
    def _analyze_question_dynamically(self, question: str) -> List[str]:
        """Análisis dinámico e inteligente de la pregunta - MEJORADO"""
        q = question.lower()
        urls = []
        
        # 1. EXTRACCIÓN INTELIGENTE DE AÑOS
        year_patterns = [
            r'año\s+(\d{4})',          # "año 1982"
            r'del\s+(\d{4})',          # "del 1982" 
            r'\b(19\d{2}|20\d{2})\b',  # cualquier año de 1900-2099
        ]
        
        for pattern in year_patterns:
            year_match = re.search(pattern, question)
            if year_match:
                year = year_match.group(1)
                urls.append(f"{self.api_base_url}/libros/buscar/por-anio/{year}")
                print(f"🎯 Año detectado: {year}")
                break
        
        # 2. EXTRACCIÓN INTELIGENTE DE NACIONALIDADES
        nationalities = {
            "chileno": "Chile", "chilenos": "Chile", "chile": "Chile",
            "colombiano": "Colombia", "colombianos": "Colombia", "colombia": "Colombia", 
            "argentino": "Argentina", "argentinos": "Argentina", "argentina": "Argentina",
            "peruano": "Perú", "peruanos": "Perú", "perú": "Perú", "peru": "Perú",
            "español": "España", "españoles": "España", "españa": "España",
            "mexicano": "México", "mexicanos": "México", "méxico": "México"
        }
        for key, nationality in nationalities.items():
            if key in q:
                urls.append(f"{self.api_base_url}/autores/buscar/por-nacionalidad/{nationality}")
                print(f"🎯 Nacionalidad detectada: {nationality}")
                break
        
        # 3. EXTRACCIÓN INTELIGENTE DE TÉRMINOS DE BÚSQUEDA EN TÍTULOS
        # Buscar términos entre comillas
        quote_patterns = [
            r'"([^"]+)"',              # "término entre comillas"
            r"'([^']+)'",              # 'término entre comillas simples'
        ]
        
        for pattern in quote_patterns:
            title_match = re.search(pattern, question)
            if title_match:
                search_term = title_match.group(1).lower()
                urls.append(f"{self.api_base_url}/libros/buscar/titulo/{search_term}")
                print(f"🎯 Término de búsqueda detectado: '{search_term}'")
                break
        
        # Si no hay comillas, buscar palabras clave conocidas
        if not any("/titulo/" in url for url in urls):
            title_keywords = ["amor", "casa", "cien", "años", "soledad", "muerte", "vida", "tiempo", "guerra", "paz", "historia", "viaje"]
            for keyword in title_keywords:
                if keyword in q:
                    urls.append(f"{self.api_base_url}/libros/buscar/titulo/{keyword}")
                    print(f"🎯 Palabra clave en título: '{keyword}'")
                    break
        
        # 4. DETECCIÓN DE CONSULTAS GENERALES (SOLO si no hay consultas específicas)
        has_specific_query = any("/buscar/" in url for url in urls)
        
        # Solo agregar consultas generales si NO hay ninguna consulta específica
        if not has_specific_query:
            if "autor" in q:
                urls.append(f"{self.api_base_url}/autores/")
            elif ("libro" in q or "libros" in q):
                urls.append(f"{self.api_base_url}/libros/")
        
        # 5. ESTADÍSTICAS
        if any(word in q for word in ["cuántos", "cuantos", "total", "cantidad", "número", "estadística", "estadisticas"]):
            urls.append(f"{self.api_base_url}/stats")
        
        # Si no encontramos nada específico, dar estadísticas
        if not urls:
            urls.append(f"{self.api_base_url}/stats")
        
        return urls
    
    def answer_question(self, question: str) -> str:
        """Responde usando la API"""
        
        if self.model:
            # Usar TinyLlama para decidir
            prompt = f"""{self._get_api_docs()}

PREGUNTA DEL USUARIO: "{question}"

INSTRUCCIONES:
- Analiza qué información necesitas para responder
- Decide qué endpoint(s) consultar
- Escribe las URLs completas que quieres usar

FORMATO:
API_CALL: GET http://127.0.0.1:8000/[endpoint]

EJEMPLOS:
Pregunta: "¿Quién escribió Cien años de soledad?"
API_CALL: GET http://127.0.0.1:8000/libros/buscar/titulo/cien

Pregunta: "¿Cuántos autores chilenos hay?"
API_CALL: GET http://127.0.0.1:8000/autores/buscar/por-nacionalidad/Chileno

Ahora responde:"""
            
            try:
                output = self.model(prompt, max_tokens=300, temperature=0.3, stop=["Pregunta:"])
                response = output["choices"][0]["text"].strip()
                print(f"🤖 TinyLlama decide: {response[:150]}...")
                
                urls = self._extract_urls(response)
                if not urls:
                    urls = self._analyze_question_dynamically(question)
            except Exception as e:
                print(f"Error con modelo: {e}")
                urls = self._analyze_question_dynamically(question)
        else:
            # Sin modelo, usar análisis dinámico
            urls = self._analyze_question_dynamically(question)
        
        print(f"📡 Consultando: {urls}")
        
        # Debug mejorado: mostrar el tipo de consulta
        specific_queries = [url for url in urls if "/buscar/" in url]
        general_queries = [url for url in urls if "/buscar/" not in url and "/stats" not in url]
        
        if specific_queries:
            print(f"🎯 Consultas específicas: {specific_queries}")
        if general_queries:
            print(f"📋 Consultas generales: {general_queries}")
        
        # Hacer las llamadas a la API
        results = {}
        for url in urls:
            result = self._call_api(url)
            results[url] = result
        
        return self._format_response(question, results)
    
    def _format_response(self, question: str, results: Dict[str, str]) -> str:
        """Formatea la respuesta final de manera inteligente"""
        response_parts = []
        q = question.lower()
        
        # Determinar si es una consulta específica
        is_year_query = bool(re.search(r'\b(19\d{2}|20\d{2})\b', question))
        is_nationality_query = any(nat in q for nat in ["chileno", "colombiano", "argentino", "peruano", "español", "mexicano"])
        is_title_query = bool(re.search(r'"([^"]+)"', question)) or any(word in q for word in ["amor", "casa", "cien", "años", "soledad"])
        
        # Procesar todos los resultados (ahora deberían ser solo los relevantes)
        for url, data in results.items():
            try:
                json_data = json.loads(data)
                
                # Para búsquedas por año específico
                if "/buscar/por-anio/" in url and isinstance(json_data, list):
                    year = re.search(r'/por-anio/(\d+)', url).group(1)
                    if json_data:
                        response_parts.append(f"📚 **Libros del año {year}** ({len(json_data)} encontrados):")
                        for libro in json_data:
                            titulo = libro.get('titulo', 'Sin título')
                            response_parts.append(f"  • \"{titulo}\"")
                    else:
                        response_parts.append(f"📚 No se encontraron libros del año {year}")
                
                # Para búsquedas por nacionalidad específica  
                elif "/buscar/por-nacionalidad/" in url and isinstance(json_data, list):
                    nationality = re.search(r'/por-nacionalidad/([^/]+)', url).group(1)
                    if json_data:
                        response_parts.append(f"👥 **Autores {nationality.lower()}s** ({len(json_data)} encontrados):")
                        for autor in json_data:
                            nombre = autor.get('nombre', 'Sin nombre')
                            response_parts.append(f"  • {nombre}")
                    else:
                        response_parts.append(f"👥 No se encontraron autores {nationality.lower()}s")
                
                # Para búsquedas por título específico
                elif "/buscar/titulo/" in url and isinstance(json_data, list):
                    search_term = re.search(r'/titulo/([^/]+)', url).group(1)
                    if json_data:
                        response_parts.append(f"📖 **Libros con '{search_term}'** ({len(json_data)} encontrados):")
                        for libro in json_data:
                            titulo = libro.get('titulo', 'Sin título')
                            año = libro.get('anio_publicacion', 'N/A')
                            response_parts.append(f"  • \"{titulo}\" ({año})")
                    else:
                        response_parts.append(f"📖 No se encontraron libros con '{search_term}' en el título")
                
                # Para consultas generales de autores
                elif "/autores/" in url and isinstance(json_data, list):
                    response_parts.append(f"👥 **Autores** ({len(json_data)} en total):")
                    for autor in json_data[:5]:
                        nombre = autor.get('nombre', 'Sin nombre')
                        nacionalidad = autor.get('nacionalidad', 'N/A')
                        response_parts.append(f"  • {nombre} ({nacionalidad})")
                    if len(json_data) > 5:
                        response_parts.append(f"  ... y {len(json_data) - 5} más")
                
                # Para consultas generales de libros
                elif "/libros/" in url and isinstance(json_data, list):
                    response_parts.append(f"📚 **Libros** ({len(json_data)} en total):")
                    for libro in json_data[:5]:
                        titulo = libro.get('titulo', 'Sin título')
                        año = libro.get('anio_publicacion', 'N/A')
                        response_parts.append(f"  • \"{titulo}\" ({año})")
                    if len(json_data) > 5:
                        response_parts.append(f"  ... y {len(json_data) - 5} más")
                
                # Para estadísticas
                elif "/stats" in url:
                    response_parts.append("📊 **Estadísticas de la biblioteca:**")
                    response_parts.append(f"  • Total autores: {json_data.get('total_autores', 'N/A')}")
                    response_parts.append(f"  • Total libros: {json_data.get('total_libros', 'N/A')}")
                    response_parts.append(f"  • Nacionalidades: {json_data.get('nacionalidades_autores', 'N/A')}")
                
                # Para resultados únicos
                elif isinstance(json_data, dict) and "nombre" in json_data:
                    response_parts.append(f"👤 **{json_data['nombre']}** ({json_data.get('nacionalidad', 'N/A')})")
                
                elif isinstance(json_data, dict) and "titulo" in json_data:
                    response_parts.append(f"📕 **\"{json_data['titulo']}\"** ({json_data.get('anio_publicacion', 'N/A')})")
            
            except json.JSONDecodeError:
                response_parts.append(f"⚠️ Error procesando datos de {url}")
        
        return "\n".join(response_parts) if response_parts else "No encontré información relevante para tu pregunta."

def main():
    print("🧠 TinyLlama Inteligente - API Biblioteca")
    print("=" * 40)
    
    # Verificar API
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ API no disponible. Ejecuta: python run_server.py")
            return
    except:
        print("❌ No se puede conectar a la API")
        return
    
    print("✅ API conectada")
    
    # Cargar TinyLlama
    model_path = "./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    assistant = IntelligentTinyLlama(model_path)
    
    print("\n🤖 TinyLlama listo - Decide por sí mismo qué APIs usar")
    print("Escribe 'salir' para terminar\n")
    
    while True:
        try:
            question = input("👤 Pregunta: ").strip()
            if question.lower() in ['salir', 'exit', 'quit']:
                break
            
            if question:
                print("🤔 Analizando...")
                answer = assistant.answer_question(question)
                print(f"\n📚 Respuesta:\n{answer}\n")
                print("-" * 40)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n¡Hasta luego! 👋")

if __name__ == "__main__":
    main() 