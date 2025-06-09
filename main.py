from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import libros, autores

# Metadatos para la documentación de la API
tags_metadata = [
    {
        "name": "Autores",
        "description": "Operaciones relacionadas con autores de libros. Permite crear, leer, actualizar y eliminar autores.",
    },
    {
        "name": "Libros", 
        "description": "Operaciones relacionadas con libros. Permite gestionar el catálogo completo de la biblioteca.",
    },
]

app = FastAPI(
    title="API de Biblioteca",
    description="""
    **API REST para gestión de biblioteca** 📚
    
    Esta API permite gestionar una biblioteca con autores y libros. Está diseñada para ser consumida por LLMs y proporciona endpoints completos para:
    
    * **Autores**: Gestión completa de autores (CRUD + búsquedas)
    * **Libros**: Gestión completa de libros (CRUD + búsquedas)
    
    ## Características principales:
    
    - ✅ Operaciones CRUD completas
    - ✅ Búsquedas especializadas
    - ✅ Documentación detallada
    - ✅ Respuestas consistentes
    - ✅ Manejo de errores
    
    ## Casos de uso para LLM:
    
    Un LLM puede usar esta API para responder preguntas como:
    - "¿Qué libros tiene Gabriel García Márquez?"
    - "¿Cuántos autores chilenos hay?"
    - "¿Qué libros se publicaron en 1967?"
    - "Agrega un nuevo libro/autor"
    
    ## Base de datos:
    
    La API utiliza una base de datos en memoria con datos de ejemplo de literatura latinoamericana.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "API de Biblioteca",
        "email": "contacto@biblioteca.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Configurar CORS para permitir acceso desde diferentes orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(libros.router, prefix="/libros", tags=["Libros"])
app.include_router(autores.router, prefix="/autores", tags=["Autores"])

@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint raíz que proporciona información básica de la API.
    
    Returns:
        dict: Mensaje de bienvenida e información de la API
    """
    return {
        "mensaje": "Bienvenido a la API de la Biblioteca 📚",
        "version": "1.0.0",
        "documentacion": "/docs",
        "endpoints_principales": {
            "autores": "/autores",
            "libros": "/libros"
        },
        "caracteristicas": [
            "CRUD completo para autores y libros",
            "Búsquedas especializadas",
            "Documentación interactiva",
            "Optimizada para consumo por LLM"
        ]
    }

@app.get("/stats", tags=["Root"])
def get_stats():
    """
    Obtiene estadísticas básicas de la biblioteca.
    
    Returns:
        dict: Estadísticas de autores y libros
    """
    from routers.autores import autores_db
    from routers.libros import libros_db
    
    return {
        "total_autores": len(autores_db),
        "total_libros": len(libros_db),
        "nacionalidades_autores": len(set(a["nacionalidad"] for a in autores_db)),
        "rango_años_publicacion": {
            "año_mas_antiguo": min(l["anio_publicacion"] for l in libros_db),
            "año_mas_reciente": max(l["anio_publicacion"] for l in libros_db)
        }
    }
