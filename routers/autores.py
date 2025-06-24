from fastapi import APIRouter, HTTPException
from models.autor import Autor
from typing import List

router = APIRouter()

# Datos de ejemplo para la base de datos en memoria
autores_db = [
    {"id": 1, "nombre": "Gabriel García Márquez", "nacionalidad": "Colombia"},
    {"id": 2, "nombre": "Isabel Allende", "nacionalidad": "Chile"},
    {"id": 3, "nombre": "Mario Vargas Llosa", "nacionalidad": "Peru"},
    {"id": 4, "nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"},
    {"id": 5, "nombre": "Pablo Neruda", "nacionalidad": "Chile"},
    {"id": 6, "nombre": "Federico García Lorca", "nacionalidad": "España"},
    {"id": 7, "nombre": "Juan Ramón Giménez", "nacionalidad": "España"}
]

@router.get("/", response_model=List[dict], summary="Obtener todos los autores")
def listar_autores():
    """
    Obtiene la lista completa de todos los autores en la biblioteca.
    
    Returns:
        List[dict]: Lista de todos los autores con su id, nombre y nacionalidad
    """
    return autores_db

@router.get("/{autor_id}", response_model=dict, summary="Obtener autor por ID")
def obtener_autor(autor_id: int):
    """
    Obtiene un autor específico por su ID.
    
    Args:
        autor_id (int): ID único del autor
        
    Returns:
        dict: Información del autor (id, nombre, nacionalidad)
        
    Raises:
        HTTPException: 404 si el autor no existe
    """
    autor = next((a for a in autores_db if a["id"] == autor_id), None)
    if autor is None:
        raise HTTPException(status_code=404, detail=f"Autor con ID {autor_id} no encontrado")
    return autor

@router.post("/", response_model=dict, summary="Crear nuevo autor")
def agregar_autor(autor: Autor):
    """
    Crea un nuevo autor en la base de datos.
    
    Args:
        autor (Autor): Datos del nuevo autor
        
    Returns:
        dict: Mensaje de confirmación y datos del autor creado
    """
    # Verificar si ya existe un autor con ese ID
    if any(a["id"] == autor.id for a in autores_db):
        raise HTTPException(status_code=400, detail=f"Ya existe un autor con ID {autor.id}")
    
    nuevo_autor = autor.dict()
    autores_db.append(nuevo_autor)
    return {"mensaje": "Autor creado exitosamente", "autor": nuevo_autor}

@router.put("/{autor_id}", response_model=dict, summary="Actualizar autor")
def actualizar_autor(autor_id: int, autor: Autor):
    """
    Actualiza los datos de un autor existente.
    
    Args:
        autor_id (int): ID del autor a actualizar
        autor (Autor): Nuevos datos del autor
        
    Returns:
        dict: Mensaje de confirmación y datos actualizados
    """
    indice = next((i for i, a in enumerate(autores_db) if a["id"] == autor_id), None)
    if indice is None:
        raise HTTPException(status_code=404, detail=f"Autor con ID {autor_id} no encontrado")
    
    autores_db[indice] = autor.dict()
    return {"mensaje": "Autor actualizado exitosamente", "autor": autores_db[indice]}

@router.delete("/{autor_id}", response_model=dict, summary="Eliminar autor")
def eliminar_autor(autor_id: int):
    """
    Elimina un autor de la base de datos.
    
    Args:
        autor_id (int): ID del autor a eliminar
        
    Returns:
        dict: Mensaje de confirmación
    """
    indice = next((i for i, a in enumerate(autores_db) if a["id"] == autor_id), None)
    if indice is None:
        raise HTTPException(status_code=404, detail=f"Autor con ID {autor_id} no encontrado")
    
    autor_eliminado = autores_db.pop(indice)
    return {"mensaje": "Autor eliminado exitosamente", "autor_eliminado": autor_eliminado}

@router.get("/buscar/por-nacionalidad/{nacionalidad}", response_model=List[dict], summary="Buscar autores por nacionalidad")
def buscar_autores_por_nacionalidad(nacionalidad: str):
    """
    Busca autores por su nacionalidad.
    
    Args:
        nacionalidad (str): Nacionalidad a buscar
        
    Returns:
        List[dict]: Lista de autores que coinciden con la nacionalidad
    """
    autores_encontrados = [a for a in autores_db if nacionalidad.lower() in a["nacionalidad"].lower()]
    return autores_encontrados
