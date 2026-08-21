import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, JSON, Boolean, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class JobType(str, enum.Enum):
    REINF_CONSULT = "REINF_CONSULT"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    cnpj = Column(String, index=True, nullable=False)
    competencia = Column(String, nullable=False)
    servico = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    
    criado_em = Column(DateTime, default=datetime.utcnow)
    iniciado_em = Column(DateTime, nullable=True)
    finalizado_em = Column(DateTime, nullable=True)
    
    resultado = Column(JSON, nullable=True) # Dados estruturados (R-2099, etc)
    erro = Column(String, nullable=True)