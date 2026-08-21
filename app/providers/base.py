from abc import ABC, abstractmethod
from typing import Dict, Any

class ReinfProviderBase(ABC):
    @abstractmethod
    async def consultar(self, cnpj: str, competencia: str) -> Dict[str, Any]:
        """Deve retornar um dicionário com os dados estruturados da consulta."""
        pass