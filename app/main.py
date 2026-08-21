import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app.models import Job, JobStatus, JobType
from app.worker import background_worker

app = FastAPI(title="Central de Automação e-CAC")

# Monta arquivos estáticos (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Schemas de Entrada/Saída
class JobCreate(BaseModel):
    cnpj: str
    competencia: str

class JobResponse(BaseModel):
    id: str
    cnpj: str
    competencia: str
    servico: str
    status: str
    resultado: Optional[dict] = None
    erro: Optional[str] = None
    posicao_fila: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    init_db()
    # Inicia o worker em background assim que o servidor subir
    asyncio.create_task(background_worker())

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")

@app.post("/api/jobs", response_model=JobResponse)
def criar_solicitacao(solicitacao: JobCreate, db: Session = Depends(get_db)):
    # Remove pontuação do CNPJ
    cnpj_limpo = ''.join(filter(str.isdigit, solicitacao.cnpj))
    if len(cnpj_limpo) != 14:
        raise HTTPException(status_code=400, detail="CNPJ inválido.")

    # Verifica duplicidade na fila (mesmo CNPJ, competência e que ainda não terminou)
    job_existente = db.query(Job).filter(
        Job.cnpj == cnpj_limpo,
        Job.competencia == solicitacao.competencia,
        Job.status.in_([JobStatus.PENDING, JobStatus.PROCESSING])
    ).first()

    if job_existente:
        return converter_para_response(job_existente, db)

    novo_job = Job(
        id=str(uuid.uuid4()),
        cnpj=cnpj_limpo,
        competencia=solicitacao.competencia,
        servico=JobType.REINF_CONSULT
    )
    db.add(novo_job)
    db.commit()
    db.refresh(novo_job)

    return converter_para_response(novo_job, db)

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def consultar_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    return converter_para_response(job, db)

def converter_para_response(job: Job, db: Session) -> dict:
    posicao = None
    if job.status == JobStatus.PENDING:
        # Conta quantos jobs foram criados ANTES deste e ainda estão PENDING
        posicao = db.query(Job).filter(
            Job.status == JobStatus.PENDING,
            Job.criado_em <= job.criado_em
        ).count()

    return {
        "id": job.id,
        "cnpj": job.cnpj,
        "competencia": job.competencia,
        "servico": job.servico.value,
        "status": job.status.value,
        "resultado": job.resultado,
        "erro": job.erro,
        "posicao_fila": posicao
    }