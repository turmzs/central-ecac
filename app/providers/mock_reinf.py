import asyncio
import random
from datetime import datetime
from typing import Dict, Any
from app.providers.base import ReinfProviderBase

class MockReinfProvider(ReinfProviderBase):
    async def consultar(self, cnpj: str, competencia: str) -> Dict[str, Any]:
        """
        Simula a extração de dados das páginas R-2099 e R-4099 do e-CAC,
        gerando dados dinâmicos baseados no formato real para OS DOIS eventos.
        """
        # Simulando o tempo de navegação do robô no e-CAC (3 segundos)
        await asyncio.sleep(3.0)
        
        # 1. Gerar a Data e Hora exatas da consulta
        agora = datetime.now()
        data_hora_formatada = agora.strftime("%d/%m/%Y %H:%M:%S")
        
        # 2. Extrair mês e ano para o formato do recibo
        try:
            mes = competencia.split('/')[0]
            ano_curto = competencia.split('/')[1][-2:] 
        except IndexError:
            mes = "00"
            ano_curto = "00"
            
        # Função auxiliar (Helper) para não repetirmos código na geração de recibos
        def gerar_recibo(codigo_evento: str) -> str:
            parte_1 = random.randint(1000000, 9999999)
            parte_2 = random.randint(1000000, 9999999)
            return f"{parte_1}-{mes}-{codigo_evento}-{ano_curto}{mes}-{parte_2}"

        # 3. Retornar os dados estruturados de AMBOS os eventos
        return {
            "r2099": {
                "situacao": "Fechada",
                "periodo": competencia,
                "data_hora_envio": data_hora_formatada,
                "numero_recibo": gerar_recibo("2099"),
                "url_origem": "https://www3.cav.receita.fazenda.gov.br/reinfweb/#/2099/lista"
            },
            "r4099": {
                "situacao": "Fechada",
                "periodo": competencia,
                "data_hora_envio": data_hora_formatada,
                "numero_recibo": gerar_recibo("4099"),
                "url_origem": "https://www3.cav.receita.fazenda.gov.br/reinfweb/#/4099/lista"
            },
            "status": "OK"
        }