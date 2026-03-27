# 🗳️ Sistema de Votaciones — FastAPI + PostgreSQL

> **Nota honesta:** Este proyecto fue impulsado con asistencia de IA para agilizar la escritura de código, pero conozco a fondo la lógica, las funciones y las tecnologías empleadas. Puedo explicar cada decisión de diseño, cada validación y cada línea de código.

Un sistema de votaciones construido con **FastAPI**, **SQLAlchemy** y **PostgreSQL (Supabase)** como prueba técnica. El objetivo fue priorizar claridad y simplicidad por encima de over-engineering.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend | FastAPI (Python) | Sintaxis limpia, documentación automática en `/docs` |
| Base de Datos | PostgreSQL vía Supabase | Gratuito, confiable, con interfaz web |
| ORM | SQLAlchemy 2.0 | Abstrae el SQL sin esconder lo que hace |
| Frontend | HTML + Bootstrap + JS vanilla | Sin frameworks innecesarios, fácil de mantener |
| Deploy | Vercel | Integración directa con GitHub |

---

## 🚀 Cómo correrlo en local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/voting-system.git
cd voting-system
```

### 2. Crear y activar un entorno virtual

```bash
# Crear el entorno virtual (buena práctica: aísla las dependencias)
python -m venv venv

# Activar en Mac/Linux:
source venv/bin/activate

# Activar en Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la variable de entorno

Crea un archivo `.env` en la raíz del proyecto (NO lo subas a GitHub):

```bash
# .env
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_bd
```

Para que Python lo lea, instala `python-dotenv`:

```bash
pip install python-dotenv
```

Y agrega esto al principio de `database.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

> 💡 Tu `DATABASE_URL` la encuentras en Supabase → Settings → Database → Connection string (URI).

### 5. Crear las tablas en Supabase

Ve al **SQL Editor** de Supabase y ejecuta:

```sql
CREATE TABLE IF NOT EXISTS voters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    has_voted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    party VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    voter_id INTEGER UNIQUE NOT NULL REFERENCES voters(id),
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    voted_at TIMESTAMP DEFAULT NOW()
);
```

### 6. Iniciar el servidor

```bash
uvicorn main:app --reload
```

Abre tu navegador en: **http://localhost:8000**

La documentación interactiva de la API está en: **http://localhost:8000/docs**

---

## 📋 Funcionalidades

### Modelos / Tablas

- **Voter** (votante): tiene nombre, email, y el campo `has_voted` que empieza en `False` y se actualiza a `True` al votar.
- **Candidate** (candidato): tiene nombre, email y partido (opcional).
- **Vote** (voto): es la tabla puente que conecta un voter con un candidate.

### Reglas de negocio implementadas

1. ✅ **Un votante no puede ser candidato** y viceversa (se valida por email).
2. ✅ **Solo se puede votar una vez** — el campo `has_voted` lo controla.
3. ✅ **Un voto y la actualización de `has_voted`** se guardan juntos en una sola transacción (si algo falla, nada se guarda).

---

## 🔌 Ejemplos de uso de la API (con `curl`)

### Registrar un votante

```bash
curl -X POST http://localhost:8000/voters/ \
  -H "Content-Type: application/json" \
  -d '{"name": "María García", "email": "maria@email.com"}'
```

**Respuesta exitosa (201):**
```json
{
  "message": "Votante registrado exitosamente.",
  "voter": { "id": 1, "name": "María García", "email": "maria@email.com" }
}
```

---

### Registrar un candidato

```bash
curl -X POST http://localhost:8000/candidates/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Juan Pérez", "email": "juan@email.com", "party": "Partido Verde"}'
```

---

### Emitir un voto

```bash
curl -X POST http://localhost:8000/votes/ \
  -H "Content-Type: application/json" \
  -d '{"voter_id": 1, "candidate_id": 1}'
```

**Respuesta exitosa (201):**
```json
{
  "message": "¡Voto registrado! 'María García' votó por 'Juan Pérez'.",
  "vote": { "voter": "María García", "candidate": "Juan Pérez", "candidate_party": "Partido Verde" }
}
```

**Error si ya votó (400):**
```json
{
  "detail": "El votante 'María García' ya emitió su voto. Solo se permite un voto por persona."
}
```

---

### Ver resultados

```bash
curl http://localhost:8000/results/
```

**Respuesta:**
```json
{
  "total_votes": 3,
  "rankings": [
    { "id": 1, "name": "Juan Pérez", "party": "Partido Verde", "vote_count": 2 },
    { "id": 2, "name": "Ana López", "party": "Movimiento Azul", "vote_count": 1 }
  ]
}
```

---

### Otros endpoints disponibles

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/voters/` | Lista todos los votantes |
| GET | `/voters/{id}` | Detalle de un votante |
| GET | `/candidates/` | Lista todos los candidatos |
| GET | `/candidates/{id}` | Detalle de un candidato |
| GET | `/votes/` | Lista todos los votos |
| GET | `/results/` | Resultados ordenados por votos |

---

## ☁️ Deploy en Vercel

1. Sube el proyecto a GitHub.
2. Conecta el repositorio en [vercel.com](https://vercel.com).
3. En **Settings → Environment Variables**, agrega:
   - `DATABASE_URL` → tu connection string de Supabase
4. Despliega. Vercel detecta automáticamente el `vercel.json` y configura todo.

---

## 📁 Estructura del Proyecto

```
voting-system/
├── main.py          # Endpoints de la API y validaciones de negocio
├── database.py      # Conexión a BD y definición de modelos (tablas)
├── templates/
│   └── index.html   # Frontend completo en un solo archivo
├── requirements.txt # Dependencias de Python
├── vercel.json      # Configuración de deploy para Vercel
└── README.md        # Este archivo
```

---

Hecho con ☕ y mucho `console.log` / `print()` de debugging.