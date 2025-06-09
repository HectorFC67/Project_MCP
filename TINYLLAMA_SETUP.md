# 🦙 Configuración de TinyLlama con API de Biblioteca

Esta guía te ayudará a conectar tu modelo TinyLlama local con la API de Biblioteca.

## 🏗️ Arquitectura del Sistema

```
Usuario → TinyLlama → API FastAPI → Base de Datos
```

1. **Usuario** hace una pregunta
2. **TinyLlama** identifica qué herramientas necesita usar
3. **TinyLlama** hace peticiones HTTP directas a la API
4. **API FastAPI** procesa las peticiones y consulta los datos
5. **TinyLlama** recibe los datos y formula una respuesta

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Verificar que Todo Funciona

#### Paso 1: Ejecutar la API
```bash
python run_server.py
```
Debería mostrar: `INFO: Uvicorn running on http://127.0.0.1:8000`

#### Paso 2: Probar el Sistema Completo
```bash
python tinyllama_intelligent.py
```

## 🔧 Configuración de TinyLlama

### Archivos Principales:

1. **`tinyllama_intelligent.py`** - TinyLlama inteligente que decide qué endpoints usar
2. **`main.py`** - API FastAPI con todos los endpoints
3. **`run_server.py`** - Script para ejecutar la API

### Configuración Específica para TinyLlama:

```python
# El modelo se carga automáticamente desde:
model_path = "./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
```

## 🛠️ Herramientas Disponibles para TinyLlama

Tu TinyLlama tendrá acceso a estas herramientas:

### 📚 Gestión de Autores
- `listar_autores()` - Lista todos los autores
- `obtener_autor(autor_id)` - Obtiene datos de un autor específico
- `buscar_autores_por_nacionalidad(nacionalidad)` - Busca autores por nacionalidad

### 📖 Gestión de Libros
- `listar_libros()` - Lista todos los libros
- `obtener_libros_por_autor(autor_id)` - Libros de un autor específico
- `buscar_libros_por_anio(anio)` - Libros por año de publicación
- `buscar_libros_por_titulo(termino)` - Busca libros por título

### 📊 Estadísticas
- `obtener_estadisticas()` - Estadísticas generales de la biblioteca

## 💡 Casos de Uso para TinyLlama

### Ejemplo 1: Consulta Simple
```
Usuario: "¿Qué autores hay en la biblioteca?"
TinyLlama: Accede a GET /autores/
API: Devuelve lista de autores
TinyLlama: "Hay 5 autores en la biblioteca: Gabriel García Márquez (Colombiano), Isabel Allende (Chilena)..."
```

### Ejemplo 2: Consulta Compleja
```
Usuario: "¿Qué libros tiene Gabriel García Márquez?"
TinyLlama: 
1. Accede a GET /autores/ para encontrar ID de García Márquez
2. Accede a GET /libros/autor/1 para obtener sus libros
API: Devuelve datos
TinyLlama: "Gabriel García Márquez tiene 2 libros: 'Cien años de soledad' (1967) y 'El amor en los tiempos del cólera' (1985)"
```

### Ejemplo 3: Búsqueda Específica
```
Usuario: "¿Cuántos autores chilenos hay?"
TinyLlama: Accede a GET /autores/buscar/por-nacionalidad/Chileno
API: Devuelve autores chilenos
TinyLlama: "Hay 2 autores chilenos: Isabel Allende y Pablo Neruda"
```

## 🔄 Flujo de Comunicación

### 1. TinyLlama recibe pregunta del usuario
### 2. TinyLlama identifica qué información necesita
### 3. TinyLlama hace petición HTTP directa a la API
```python
GET http://127.0.0.1:8000/autores/
```

### 4. API responde con datos JSON
```json
[
  {"id": 1, "nombre": "Gabriel García Márquez", "nacionalidad": "Colombiano"},
  {"id": 2, "nombre": "Isabel Allende", "nacionalidad": "Chilena"}
]
```

### 5. TinyLlama procesa los datos y responde al usuario

## 🐛 Solución de Problemas

### Error: "No se puede conectar a la API"
```bash
# Verificar que la API está ejecutándose
curl http://127.0.0.1:8000/
# Debería devolver un JSON con mensaje de bienvenida
```

### Error: "llama-cpp-python no está instalado"
```bash
pip install llama-cpp-python
```

### Error: "Modelo no encontrado"
Verificar que el archivo del modelo existe en:
`./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf`

## 🎯 Uso

### 1. Ejecutar la API:
```bash
python run_server.py
```

### 2. Ejecutar TinyLlama:
```bash
python tinyllama_intelligent.py
```

### 3. Hacer preguntas:
```
👤 Tu pregunta: ¿Qué libros tiene Gabriel García Márquez?
🤖 TinyLlama (pensando...)
📚 TinyLlama responde: Los libros de Gabriel García Márquez son:
- "Cien años de soledad" (1967)
- "El amor en los tiempos del cólera" (1985)
```

## 📝 Personalización

### Agregar Nueva Herramienta

1. **Crear endpoint en la API** (en `routers/`)
2. **Agregar método a `BibliotecaTools`** en `tinyllama_client.py`
3. **Actualizar lógica en `tinyllama_real.py`**

## 🎯 Próximos Pasos

1. **Ejecutar la API**: `python run_server.py`
2. **Ejecutar TinyLlama**: `python tinyllama_intelligent.py`
3. **Hacer preguntas** y ver cómo TinyLlama decide qué endpoints usar
4. **Personalizar** según tus necesidades

¡Tu TinyLlama ya está listo para ser un bibliotecario inteligente! 📚🤖 