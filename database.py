"""
database.py
-----------
Aquí vive todo lo relacionado con la base de datos:
la conexión y los modelos (tablas). Lo separé de main.py
para que cada archivo tenga UNA sola responsabilidad.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# -------------------------------------------------------------------
# CONEXIÓN A LA BASE DE DATOS
# -------------------------------------------------------------------
# Leemos la URL desde una variable de entorno para no hardcodear
# credenciales en el código (buena práctica de seguridad básica).
# En local usas un archivo .env; en Vercel la configuras en el dashboard.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está configurada.")

# create_engine es el "motor" que sabe cómo hablarle a PostgreSQL.
# pool_pre_ping=True hace un chequeo rápido de la conexión antes de usarla,
# lo que evita errores si la conexión estuvo inactiva un rato.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal es la "fábrica" de sesiones. Cada request de la API
# abrirá su propia sesión y la cerrará al terminar.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase de la que heredan todos nuestros modelos.
# SQLAlchemy la usa para saber qué tablas crear/mapear.
Base = declarative_base()


# -------------------------------------------------------------------
# MODELOS (TABLAS)
# -------------------------------------------------------------------

class Voter(Base):
    """
    Tabla 'voters': guarda a las personas que pueden votar.
    Un voter NO puede ser al mismo tiempo un candidate (lo validamos en main.py).
    """
    __tablename__ = "voters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    # has_voted empieza en False y lo cambiamos a True cuando registramos su voto.
    # Esto evita el doble voto sin hacer consultas complejas.
    has_voted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación: un voter puede tener asociado un voto (máximo uno).
    vote = relationship("Vote", back_populates="voter", uselist=False)


class Candidate(Base):
    """
    Tabla 'candidates': las personas a las que se puede votar.
    """
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    # party es el partido o grupo al que pertenece el candidato (opcional).
    party = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación: un candidato puede recibir muchos votos.
    votes = relationship("Vote", back_populates="candidate")


class Vote(Base):
    """
    Tabla 'votes': registra qué voter votó por qué candidate.
    Esta tabla es el "puente" entre voters y candidates.
    """
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    # ForeignKey vincula este campo con el id de la tabla correspondiente.
    voter_id = Column(Integer, ForeignKey("voters.id"), nullable=False, unique=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    voted_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones inversas para poder hacer vote.voter o vote.candidate fácilmente.
    voter = relationship("Voter", back_populates="vote")
    candidate = relationship("Candidate", back_populates="votes")


# -------------------------------------------------------------------
# FUNCIÓN HELPER PARA LA SESIÓN
# -------------------------------------------------------------------

def get_db():
    """
    Esta función es un 'generador' que FastAPI usa como dependencia.
    Abre una sesión, la entrega al endpoint, y SIEMPRE la cierra
    al final (el bloque finally garantiza eso aunque haya un error).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()