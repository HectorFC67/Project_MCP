#!/usr/bin/env python3
"""
TinyLlama Inteligente - Le damos toda la documentación de la API 
y que él decida qué endpoints usar según la pregunta.
"""

import sys
import json
import re
import requests
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
• GET /libros/buscar/por-anio/{anio} → Libros por año (ej: /libros/buscar/por-anio/1967)
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
    
    def _simple_decision(self, question: str) -> List[str]:
        """Decisión genérica cuando no hay modelo - permite más flexibilidad"""
        # En lugar de reglas hardcodeadas, usar una estrategia más general
        # que explore múltiples endpoints relevantes
        
        q = question.lower()
        urls = []
        
        # Estrategia: Si menciona autores, consultar endpoints de autores
        if "autor" in q:
            urls.append(f"{self.api_base_url}/autores/")
            # Si menciona nacionalidad, también buscar por nacionalidad
            for nacionalidad in ["chileno", "colombiano", "argentino", "peruano"]:
                if nacionalidad in q:
                    urls.append(f"{self.api_base_url}/autores/buscar/por-nacionalidad/{nacionalidad.capitalize()}")
                    break
        
        # Si menciona libros, consultar endpoints de libros
        if "libro" in q or "título" in q or "titulo" in q:
            urls.append(f"{self.api_base_url}/libros/")
            
            # Buscar años mencionados
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', q)
            if year_match:
                urls.append(f"{self.api_base_url}/libros/buscar/por-anio/{year_match.group()}")
            
            # Buscar términos de títulos (palabras significativas)
            title_terms = ["amor", "casa", "cien", "años", "soledad", "espíritus", "ficciones", "catedral"]
            for term in title_terms:
                if term in q:
                    urls.append(f"{self.api_base_url}/libros/buscar/titulo/{term}")
                    break
        
        # Si menciona números/estadísticas, incluir stats
        if any(word in q for word in ["cuántos", "cuantos", "total", "estadística", "estadisticas", "número"]):
            urls.append(f"{self.api_base_url}/stats")
        
        # Si no encontramos nada específico, dar información general
        if not urls:
            urls.extend([f"{self.api_base_url}/stats", f"{self.api_base_url}/autores/"])
        
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
                    urls = self._simple_decision(question)
            except Exception as e:
                print(f"Error con modelo: {e}")
                urls = self._simple_decision(question)
        else:
            # Sin modelo, usar lógica simple
            urls = self._simple_decision(question)
        
        print(f"📡 Consultando: {urls}")
        
        # Hacer las llamadas a la API
        results = {}
        for url in urls:
            result = self._call_api(url)
            results[url] = result
        
        return self._format_response(question, results)
    
    def _format_response(self, question: str, results: Dict[str, str]) -> str:
        """Formatea la respuesta final"""
        response_parts = []
        
        for url, data in results.items():
            try:
                json_data = json.loads(data)
                
                if "/autores/" in url and isinstance(json_data, list):
                    response_parts.append(f"📚 Autores ({len(json_data)}):")
                    for autor in json_data[:5]:
                        response_parts.append(f"  • {autor.get('nombre')} ({autor.get('nacionalidad')})")
                
                elif "/libros/" in url and isinstance(json_data, list):
                    response_parts.append(f"📖 Libros ({len(json_data)}):")
                    for libro in json_data[:5]:
                        response_parts.append(f"  • \"{libro.get('titulo')}\" ({libro.get('anio_publicacion')})")
                
                elif "/stats" in url:
                    response_parts.append("📊 Estadísticas:")
                    response_parts.append(f"  • Autores: {json_data.get('total_autores')}")
                    response_parts.append(f"  • Libros: {json_data.get('total_libros')}")
                    response_parts.append(f"  • Nacionalidades: {json_data.get('nacionalidades_autores')}")
                
                elif isinstance(json_data, dict) and "nombre" in json_data:
                    response_parts.append(f"👤 {json_data['nombre']} ({json_data.get('nacionalidad')})")
                
                elif isinstance(json_data, dict) and "titulo" in json_data:
                    response_parts.append(f"📕 \"{json_data['titulo']}\" ({json_data.get('anio_publicacion')})")
            
            except json.JSONDecodeError:
                response_parts.append(f"⚠️ Error en {url}")
        
        return "\n".join(response_parts) if response_parts else "No encontré información relevante."

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