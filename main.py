"""
main.py
-------
El corazón de la aplicación. Aquí defino todos los endpoints
de la API y sus validaciones de negocio.
Uso FastAPI porque su sintaxis es muy clara y genera
documentación automática en /docs (¡súper útil para demostrar el proyecto!).
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

# Importamos todo lo que necesitamos de nuestro database.py
from database import Base, engine, get_db, Voter, Candidate, Vote

# -------------------------------------------------------------------
# INICIALIZACIÓN
# -------------------------------------------------------------------

# Esto crea las tablas en la BD si no existen todavía.
# En producción con Supabase, las tablas ya existen (las creamos con el script SQL),
# pero esto es un "seguro" para el entorno local.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Votaciones",
    description="API para gestionar votantes, candidatos y votos.",
    version="1.0.0"
)

# Le decimos a FastAPI dónde están nuestras plantillas HTML.
templates = Jinja2Templates(directory="templates")


# -------------------------------------------------------------------
# SCHEMAS (modelos de entrada/salida con Pydantic)
# -------------------------------------------------------------------
# Pydantic valida automáticamente que los datos del request
# tengan el formato correcto. Si no lo tienen, devuelve un 422.

class VoterCreate(BaseModel):
    name: str
    email: EmailStr  # Pydantic valida que sea un email real

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    party: Optional[str] = None  # El partido es opcional

class VoteCreate(BaseModel):
    voter_id: int
    candidate_id: int


# -------------------------------------------------------------------
# FRONTEND
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Sirve el archivo HTML del frontend.
    Usamos Jinja2Templates para poder pasar variables al HTML si fuera necesario.
    """
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------------------------------------------------
# ENDPOINTS DE VOTERS (Votantes)
# -------------------------------------------------------------------

@app.post("/voters/", status_code=201)
def create_voter(voter_data: VoterCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo votante.
    Antes de crearlo, verificamos que el email no esté
    registrado como candidato (una persona no puede ser las dos cosas).
    """
    # Validación 1: ¿El email ya está registrado como candidato?
    existing_candidate = db.query(Candidate).filter(Candidate.email == voter_data.email).first()
    if existing_candidate:
        raise HTTPException(
            status_code=400,
            detail="Este email ya está registrado como candidato. Un candidato no puede ser votante."
        )

    # Validación 2: ¿El email ya está registrado como voter?
    existing_voter = db.query(Voter).filter(Voter.email == voter_data.email).first()
    if existing_voter:
        raise HTTPException(status_code=400, detail="Este email ya está registrado como votante.")

    # Si pasó las validaciones, creamos el voter y lo guardamos
    new_voter = Voter(name=voter_data.name, email=voter_data.email)
    db.add(new_voter)
    db.commit()
    db.refresh(new_voter)  # Recargamos para obtener el id generado por la BD

    return {
        "message": "Votante registrado exitosamente.",
        "voter": {"id": new_voter.id, "name": new_voter.name, "email": new_voter.email}
    }


@app.get("/voters/")
def list_voters(db: Session = Depends(get_db)):
    """Devuelve la lista de todos los votantes registrados."""
    voters = db.query(Voter).all()
    result = []
    for v in voters:
        result.append({
            "id": v.id,
            "name": v.name,
            "email": v.email,
            "has_voted": v.has_voted,
            "created_at": v.created_at
        })
    return result


@app.get("/voters/{voter_id}")
def get_voter(voter_id: int, db: Session = Depends(get_db)):
    """Devuelve el detalle de un votante por su ID."""
    voter = db.query(Voter).filter(Voter.id == voter_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Votante no encontrado.")
    return {
        "id": voter.id,
        "name": voter.name,
        "email": voter.email,
        "has_voted": voter.has_voted,
        "created_at": voter.created_at
    }


# -------------------------------------------------------------------
# ENDPOINTS DE CANDIDATES (Candidatos)
# -------------------------------------------------------------------

@app.post("/candidates/", status_code=201)
def create_candidate(candidate_data: CandidateCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo candidato.
    Validamos que el email no esté ya registrado como votante.
    """
    # Validación 1: ¿El email ya está registrado como voter?
    existing_voter = db.query(Voter).filter(Voter.email == candidate_data.email).first()
    if existing_voter:
        raise HTTPException(
            status_code=400,
            detail="Este email ya está registrado como votante. Un votante no puede ser candidato."
        )

    # Validación 2: ¿El email ya está registrado como candidate?
    existing_candidate = db.query(Candidate).filter(Candidate.email == candidate_data.email).first()
    if existing_candidate:
        raise HTTPException(status_code=400, detail="Este email ya está registrado como candidato.")

    new_candidate = Candidate(
        name=candidate_data.name,
        email=candidate_data.email,
        party=candidate_data.party
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)

    return {
        "message": "Candidato registrado exitosamente.",
        "candidate": {
            "id": new_candidate.id,
            "name": new_candidate.name,
            "email": new_candidate.email,
            "party": new_candidate.party
        }
    }


@app.get("/candidates/")
def list_candidates(db: Session = Depends(get_db)):
    """Devuelve la lista de candidatos con el conteo de votos de cada uno."""
    candidates = db.query(Candidate).all()
    result = []
    for c in candidates:
        # len(c.votes) cuenta cuántos votos tiene gracias a la relación que definimos
        result.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "party": c.party,
            "vote_count": len(c.votes),
            "created_at": c.created_at
        })
    return result


@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Devuelve el detalle de un candidato por su ID."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato no encontrado.")
    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "party": candidate.party,
        "vote_count": len(candidate.votes),
        "created_at": candidate.created_at
    }


# -------------------------------------------------------------------
# ENDPOINTS DE VOTES (Votos)
# -------------------------------------------------------------------

@app.post("/votes/", status_code=201)
def cast_vote(vote_data: VoteCreate, db: Session = Depends(get_db)):
    """
    Registra un voto. Aquí están las validaciones más importantes:
    1. El voter debe existir.
    2. El candidate debe existir.
    3. El voter NO debe haber votado antes (has_voted = False).
    """
    # Buscamos al voter
    voter = db.query(Voter).filter(Voter.id == vote_data.voter_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Votante no encontrado.")

    # Buscamos al candidato
    candidate = db.query(Candidate).filter(Candidate.id == vote_data.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato no encontrado.")

    # Validación clave: ¿Ya votó esta persona?
    # Revisamos has_voted en lugar de buscar en la tabla votes para que sea más directo.
    if voter.has_voted:
        raise HTTPException(
            status_code=400,
            detail=f"El votante '{voter.name}' ya emitió su voto. Solo se permite un voto por persona."
        )

    # Registramos el voto
    new_vote = Vote(voter_id=voter.id, candidate_id=candidate.id)
    db.add(new_vote)

    # Actualizamos has_voted a True para que no pueda votar de nuevo
    voter.has_voted = True

    # commit() guarda AMBOS cambios juntos (el voto y el has_voted).
    # Si algo falla, ninguno se guarda (eso se llama transacción atómica).
    db.commit()

    return {
        "message": f"¡Voto registrado! '{voter.name}' votó por '{candidate.name}'.",
        "vote": {
            "voter": voter.name,
            "candidate": candidate.name,
            "candidate_party": candidate.party
        }
    }


@app.get("/votes/")
def list_votes(db: Session = Depends(get_db)):
    """Devuelve todos los votos registrados."""
    votes = db.query(Vote).all()
    result = []
    for v in votes:
        result.append({
            "id": v.id,
            "voter": v.voter.name,
            "candidate": v.candidate.name,
            "candidate_party": v.candidate.party,
            "voted_at": v.voted_at
        })
    return result


@app.get("/results/")
def get_results(db: Session = Depends(get_db)):
    """
    Endpoint de resultados: devuelve los candidatos ordenados
    de mayor a menor número de votos. Perfecto para el frontend.
    """
    candidates = db.query(Candidate).all()

    results = []
    for c in candidates:
        results.append({
            "id": c.id,
            "name": c.name,
            "party": c.party,
            "vote_count": len(c.votes)
        })

    # Ordenamos en Python (no en SQL) para que el código sea más legible.
    # reverse=True = descendente (el que más votos tiene, primero).
    results.sort(key=lambda x: x["vote_count"], reverse=True)

    total_votes = db.query(Vote).count()

    return {
        "total_votes": total_votes,
        "rankings": results
    }