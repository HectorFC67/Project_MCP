# 📚 API de Biblioteca - Para Consumo por LLM

Una API REST completa para gestión de biblioteca diseñada especialmente para ser consumida por modelos de lenguaje como TinyLlama en el contexto de MCP (Model Context Protocol).

## 🎯 Características

- ✅ **CRUD Completo**: Crear, leer, actualizar y eliminar autores y libros
- ✅ **Búsquedas Especializadas**: Por nacionalidad, año, título, etc.
- ✅ **Documentación Interactiva**: Swagger UI automático
- ✅ **Optimizado para LLM**: Respuestas estructuradas y consistentes
- ✅ **Base de Datos en Memoria**: Con datos de ejemplo de literatura latinoamericana
- ✅ **CORS Habilitado**: Para acceso desde diferentes orígenes

## 🚀 Instalación y Uso

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar el Servidor

```bash
python run_server.py
```

La API estará disponible en: `http://127.0.0.1:8000`

### 3. Acceder a la Documentación

- **Documentación Interactiva**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📊 Endpoints Principales

### Autores (`/autores`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/autores/` | Obtener todos los autores |
| `GET` | `/autores/{id}` | Obtener autor por ID |
| `POST` | `/autores/` | Crear nuevo autor |
| `PUT` | `/autores/{id}` | Actualizar autor |
| `DELETE` | `/autores/{id}` | Eliminar autor |
| `GET` | `/autores/buscar/por-nacionalidad/{nacionalidad}` | Buscar por nacionalidad |

### Libros (`/libros`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/libros/` | Obtener todos los libros |
| `GET` | `/libros/{id}` | Obtener libro por ID |
| `POST` | `/libros/` | Crear nuevo libro |
| `PUT` | `/libros/{id}` | Actualizar libro |
| `DELETE` | `/libros/{id}` | Eliminar libro |
| `GET` | `/libros/autor/{autor_id}` | Libros por autor |
| `GET` | `/libros/buscar/por-anio/{anio}` | Buscar por año |
| `GET` | `/libros/buscar/titulo/{termino}` | Buscar por título |

### Otros Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Información de la API |
| `GET` | `/stats` | Estadísticas de la biblioteca |

## 🤖 Uso con LLM

### Ejemplo de Preguntas que el LLM puede Responder:

- "¿Qué libros tiene Gabriel García Márquez?"
- "¿Cuántos autores chilenos hay?"
- "¿Qué libros se publicaron en 1967?"
- "¿Hay algún libro con 'amor' en el título?"
- "Dame las estadísticas de la biblioteca"

### TinyLlama Inteligente

Ejecuta tu modelo TinyLlama que decide por sí mismo qué endpoints usar:

```bash
python tinyllama_intelligent.py
```

TinyLlama analiza tu pregunta, lee la documentación de la API y decide qué endpoints consultar para responder correctamente.

## 💾 Datos de Ejemplo

La API incluye datos de ejemplo de literatura latinoamericana:

### Autores:
- Gabriel García Márquez (Colombiano)
- Isabel Allende (Chilena)
- Mario Vargas Llosa (Peruano)
- Jorge Luis Borges (Argentino)
- Pablo Neruda (Chileno)

### Libros:
- "Cien años de soledad" (1967)
- "La casa de los espíritus" (1982)
- "Ficciones" (1944)
- "El amor en los tiempos del cólera" (1985)
- Y más...

## 🔧 Estructura del Proyecto

```
.
├── main.py                    # Aplicación principal FastAPI
├── run_server.py             # Script para ejecutar el servidor
├── requirements.txt          # Dependencias
├── README.md                # Este archivo
├── tinyllama_intelligent.py  # TinyLlama inteligente (decide qué APIs usar)
├── TINYLLAMA_SETUP.md        # Guía de configuración TinyLlama
├── models/                  # Modelos Pydantic
│   ├── autor.py
│   └── libro.py
└── routers/                 # Routers FastAPI
    ├── autores.py
    └── libros.py
```

## 🔗 Integración con TinyLlama

Para integrar con tu LLM local TinyLlama:

1. **Ejecuta la API**: `python run_server.py`
2. **Configura el LLM** para hacer peticiones HTTP a `http://127.0.0.1:8000`
3. **Define las herramientas** disponibles basándose en los endpoints
4. **Procesa las respuestas** JSON de la API

### Ejemplo de Uso con TinyLlama Inteligente:

```
👤 Usuario: "¿Qué libros escribió García Márquez?"
🤖 TinyLlama analiza la pregunta...
📡 TinyLlama decide consultar: /autores/ y /libros/autor/1
📚 TinyLlama responde: "Gabriel García Márquez escribió 2 libros: 'Cien años de soledad' (1967) y 'El amor en los tiempos del cólera' (1985)"
```

## 🛠️ Personalización

Para adaptar la API a tus necesidades:

1. **Modifica los modelos** en `models/` para cambiar la estructura de datos
2. **Actualiza los routers** en `routers/` para agregar nuevos endpoints
3. **Cambia los datos de ejemplo** en los archivos de routers
4. **Ajusta la documentación** en `main.py`

## 📝 Licencia

MIT License - Siéntete libre de usar y modificar este código.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Abre un issue o envía un pull request.

---

**¡Disfruta creando con tu LLM y la API de Biblioteca! 🚀📚** 