import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Job, JobStatus
# CORREÇÃO AQUI: Removemos o .py do ficheiro mock_reinf
from app.providers.mock_reinf import MockReinfProvider 

# Configuração de logs para vermos o que o trabalhador (worker) está a fazer
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Instanciamos o nosso provedor simulado
provider = MockReinfProvider()

async def process_job(job_id: str):
    """
    Função responsável por processar um único job (solicitação).
    """
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        db.close()
        return

    try:
        # Muda o status para "Processando"
        logger.info(f"Iniciando Job #{job.id[:8]} - CNPJ: {job.cnpj[:8]}******")
        job.status = JobStatus.PROCESSING
        job.iniciado_em = datetime.utcnow()
        db.commit()

        # Chama o provedor (Mock) para simular a consulta na Receita Federal
        resultado = await provider.consultar(job.cnpj, job.competencia)

        # Guarda o resultado e marca como "Concluído"
        job.resultado = resultado
        job.status = JobStatus.COMPLETED
        logger.info(f"Job #{job.id[:8]} CONCLUÍDO com sucesso.")

    except Exception as e:
        # Em caso de erro (ex: timeout), regista a falha
        logger.error(f"Erro no Job #{job.id[:8]}: {str(e)}")
        job.erro = str(e)
        job.status = JobStatus.FAILED
    
    finally:
        job.finalizado_em = datetime.utcnow()
        db.commit()
        db.close()

async def background_worker():
    """
    Roda continuamente em background (segundo plano), pegando 1 job de cada vez da fila.
    """
    logger.info("Worker iniciado. Aguardando jobs na fila...")
    
    # Prevenção contra jobs travados (se o servidor tiver caído no meio de um processo)
    db = SessionLocal()
    travados = db.query(Job).filter(Job.status == JobStatus.PROCESSING).all()
    for t in travados:
        t.status = JobStatus.PENDING # Reverte para a fila para tentar de novo
        logger.info(f"Job #{t.id[:8]} revertido de PROCESSING para PENDING.")
    db.commit()
    db.close()

    # Loop infinito para ficar sempre a verificar a fila
    while True:
        db = SessionLocal()
        # Pega o job PENDING mais antigo
        next_job = db.query(Job).filter(Job.status == JobStatus.PENDING).order_by(Job.criado_em.asc()).first()
        db.close()

        if next_job:
            # Processa o job (o comando 'await' garante que só avança quando acabar)
            await process_job(next_job.id)
        else:
            # Se não tem job na fila, dorme 2 segundos para não sobrecarregar o computador
            await asyncio.sleep(2)