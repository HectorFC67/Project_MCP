from pydantic import BaseModel

class Libro(BaseModel):
    id: int
    titulo: str
    autor_id: int
    anio_publicacion: int
