from fastapi import APIRouter, HTTPException
from models.libro import Libro
from typing import List

router = APIRouter()

# Datos de ejemplo para la base de datos en memoria
libros_db = [
    {"id": 1, "titulo": "Cien años de soledad", "autor_id": 1, "anio_publicacion": 1967},
    {"id": 2, "titulo": "La casa de los espíritus", "autor_id": 2, "anio_publicacion": 1982},
    {"id": 3, "titulo": "La ciudad y los perros", "autor_id": 3, "anio_publicacion": 1963},
    {"id": 4, "titulo": "Ficciones", "autor_id": 4, "anio_publicacion": 1944},
    {"id": 5, "titulo": "Veinte poemas de amor y una canción desesperada", "autor_id": 5, "anio_publicacion": 1924},
    {"id": 6, "titulo": "El amor en los tiempos del cólera", "autor_id": 1, "anio_publicacion": 1985},
    {"id": 7, "titulo": "Paula", "autor_id": 2, "anio_publicacion": 1994},
    {"id": 8, "titulo": "Conversación en La Catedral", "autor_id": 3, "anio_publicacion": 1969}
]

@router.get("/", response_model=List[dict], summary="Obtener todos los libros")
def listar_libros():
    """
    Obtiene la lista completa de todos los libros en la biblioteca.
    
    Returns:
        List[dict]: Lista de todos los libros con su id, título, autor_id y año de publicación
    """
    return libros_db

@router.get("/{libro_id}", response_model=dict, summary="Obtener libro por ID")
def obtener_libro(libro_id: int):
    """
    Obtiene un libro específico por su ID.
    
    Args:
        libro_id (int): ID único del libro
        
    Returns:
        dict: Información del libro (id, título, autor_id, año de publicación)
        
    Raises:
        HTTPException: 404 si el libro no existe
    """
    libro = next((l for l in libros_db if l["id"] == libro_id), None)
    if libro is None:
        raise HTTPException(status_code=404, detail=f"Libro con ID {libro_id} no encontrado")
    return libro

@router.post("/", response_model=dict, summary="Crear nuevo libro")
def agregar_libro(libro: Libro):
    """
    Crea un nuevo libro en la base de datos.
    
    Args:
        libro (Libro): Datos del nuevo libro
        
    Returns:
        dict: Mensaje de confirmación y datos del libro creado
    """
    # Verificar si ya existe un libro con ese ID
    if any(l["id"] == libro.id for l in libros_db):
        raise HTTPException(status_code=400, detail=f"Ya existe un libro con ID {libro.id}")
    
    nuevo_libro = libro.dict()
    libros_db.append(nuevo_libro)
    return {"mensaje": "Libro creado exitosamente", "libro": nuevo_libro}

@router.put("/{libro_id}", response_model=dict, summary="Actualizar libro")
def actualizar_libro(libro_id: int, libro: Libro):
    """
    Actualiza los datos de un libro existente.
    
    Args:
        libro_id (int): ID del libro a actualizar
        libro (Libro): Nuevos datos del libro
        
    Returns:
        dict: Mensaje de confirmación y datos actualizados
    """
    indice = next((i for i, l in enumerate(libros_db) if l["id"] == libro_id), None)
    if indice is None:
        raise HTTPException(status_code=404, detail=f"Libro con ID {libro_id} no encontrado")
    
    libros_db[indice] = libro.dict()
    return {"mensaje": "Libro actualizado exitosamente", "libro": libros_db[indice]}

@router.delete("/{libro_id}", response_model=dict, summary="Eliminar libro")
def eliminar_libro(libro_id: int):
    """
    Elimina un libro de la base de datos.
    
    Args:
        libro_id (int): ID del libro a eliminar
        
    Returns:
        dict: Mensaje de confirmación
    """
    indice = next((i for i, l in enumerate(libros_db) if l["id"] == libro_id), None)
    if indice is None:
        raise HTTPException(status_code=404, detail=f"Libro con ID {libro_id} no encontrado")
    
    libro_eliminado = libros_db.pop(indice)
    return {"mensaje": "Libro eliminado exitosamente", "libro_eliminado": libro_eliminado}

@router.get("/autor/{autor_id}", response_model=List[dict], summary="Obtener libros por autor")
def obtener_libros_por_autor(autor_id: int):
    """
    Obtiene todos los libros de un autor específico.
    
    Args:
        autor_id (int): ID del autor
        
    Returns:
        List[dict]: Lista de libros del autor especificado
    """
    libros_autor = [l for l in libros_db if l["autor_id"] == autor_id]
    return libros_autor

@router.get("/buscar/por-anio/{anio}", response_model=List[dict], summary="Buscar libros por año de publicación")
def buscar_libros_por_anio(anio: int):
    """
    Busca libros por año de publicación.
    
    Args:
        anio (int): Año de publicación a buscar
        
    Returns:
        List[dict]: Lista de libros publicados en el año especificado
    """
    libros_encontrados = [l for l in libros_db if l["anio_publicacion"] == anio]
    return libros_encontrados

@router.get("/buscar/titulo/{termino}", response_model=List[dict], summary="Buscar libros por título")
def buscar_libros_por_titulo(termino: str):
    """
    Busca libros que contengan el término especificado en el título.
    
    Args:
        termino (str): Término a buscar en los títulos
        
    Returns:
        List[dict]: Lista de libros que coinciden con el término de búsqueda
    """
    libros_encontrados = [l for l in libros_db if termino.lower() in l["titulo"].lower()]
    return libros_encontrados
