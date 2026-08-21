import asyncio
import subprocess
import re
import os
from typing import Dict, Any
from playwright.async_api import async_playwright
from app.providers.base import ReinfProviderBase

class PlaywrightReinfProvider(ReinfProviderBase):
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.processo_chrome = None

    async def iniciar_sessao_diaria(self):
        """Passo 1: Abre o navegador de forma tradicional e segura."""
        caminho_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        caminho_perfil = r"C:\perfil_cdp_robo"
        
        print("\n[SISTEMA] Iniciando a Sessão Diária do Robô (Modo Estável EFD-Reinf)...", flush=True)
        
        self.processo_chrome = subprocess.Popen([
            caminho_chrome,
            "--remote-debugging-port=9222",
            f"--user-data-dir={caminho_perfil}"
        ])
        
        await asyncio.sleep(3)

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

        print("[SISTEMA] Acessando o portal do e-CAC...", flush=True)
        await self.page.goto("https://cav.receita.fazenda.gov.br/autenticacao/login", timeout=90000)
        
        if await self.page.locator('#btnPerfil').is_visible():
            print("✅ SESSÃO JÁ ATIVA! O e-CAC entrou direto.", flush=True)
            return

        if await self.page.locator('input[alt="Acesso Gov BR"]').is_visible():
            print("[SISTEMA] Clicando no botão Gov.br...", flush=True)
            await self.page.locator('input[alt="Acesso Gov BR"]').click(timeout=90000)

        print("\n=======================================================", flush=True)
        print("⏳ ATENÇÃO: Se houver CAPTCHA inicial, resolva-o agora...", flush=True)
        print("=======================================================\n", flush=True)

        seletor_login = self.page.locator('#login-certificate')
        seletor_painel = self.page.locator('#btnPerfil')

        for _ in range(60):
            if await seletor_painel.is_visible():
                print("✅ SESSÃO RECONHECIDA! O e-CAC avançou.", flush=True)
                return
            if await seletor_login.is_visible():
                print("[SISTEMA] Clicando no certificado...", flush=True)
                await seletor_login.click()
                break
            await asyncio.sleep(3)

        await seletor_painel.wait_for(state="visible", timeout=90000)
        print("✅ LOGIN CONCLUÍDO COM SUCESSO!\n", flush=True)

    async def consultar(self, cnpj: str, competencia: str) -> Dict[str, Any]:
        """Passo 2: Altera a procuração, captura o NOME DA EMPRESA com base na div HTML e consulta eventos."""
        if not self.page:
            raise Exception("A sessão diária não foi iniciada!")

        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)

        print(f"\n[PASSO 1/5] Alterando perfil para o CNPJ {cnpj_limpo}...", flush=True)
        btn_perfil = self.page.locator('#btnPerfil')
        await btn_perfil.wait_for(state="visible", timeout=30000)
        await btn_perfil.click()

        print("[PASSO 2/5] Aguardando a janela modal abrir...", flush=True)
        modal_perfil = self.page.locator('#perfilAcesso')
        await modal_perfil.wait_for(state="visible", timeout=30000)
        
        campo_cnpj = self.page.locator('#txtNIPapel2')
        await campo_cnpj.wait_for(state="visible", timeout=15000)
        
        await campo_cnpj.click()
        await campo_cnpj.fill(cnpj_limpo)

        print("[PASSO 3/5] Clicando em 'Alterar'...", flush=True)
        btn_alterar = self.page.locator('#formPJ input[value="Alterar"]')
        await btn_alterar.click()
        
        # Trava de Segurança
        mensagem_erro = self.page.locator('text="não possui procuração", text="Procuração não encontrada", text="não é procurador", .alert-danger, #msgErro').first
        if await mensagem_erro.is_visible(timeout=5000):
            texto_erro = await mensagem_erro.inner_text()
            print(f"  -> ❌ ALERTA: Empresa sem procuração ou erro no perfil! ({texto_erro})", flush=True)
            return {"status": "SEM_PROCURACAO", "cnpj": cnpj_limpo, "erro_detalhe": texto_erro}

        # ---------------------------------------------------------
        # CAPTURA INTELIGENTE BASEADA NO HTML DO USUÁRIO
        # ---------------------------------------------------------
        print("  -> Aguardando o portal atualizar o cabeçalho com o novo perfil...", flush=True)
        nome_empresa_formatado = f"EMPRESA-{cnpj_limpo}" 
        
        try:
            await asyncio.sleep(4) 
            
            # Aqui nós usamos a div exata que você encontrou no código-fonte!
            info_perfil = self.page.locator('#informacao-perfil')
            await info_perfil.wait_for(state="visible", timeout=10000)
            texto_cabecalho = await info_perfil.inner_text()
            
            print(f"  -> [DEBUG] Texto bruto: {texto_cabecalho!r}", flush=True)
            
            linhas = texto_cabecalho.split('\n')
            
            for linha in linhas:
                # Procuramos a linha que tem a palavra-chave
                if "Procurador de:" in linha:
                    # A linha é parecida com: "Procurador de: 41.310.378/0001-79 - ALFA GERADORES LTDA "
                    # O split(" - ", 1) divide o texto exatamente no primeiro " - " que encontrar
                    partes = linha.split(" - ", 1)
                    
                    if len(partes) > 1:
                        # Pegamos a segunda parte (o nome da empresa) e removemos espaços vazios nas pontas (.strip)
                        nome_puro = partes[1].strip()
                        
                        # Substitui todos os espaços (um ou mais) no meio do nome por traços e deixa tudo maiúsculo
                        resultado_final = re.sub(r'\s+', '-', nome_puro).upper()
                        
                        if resultado_final:
                            nome_empresa_formatado = resultado_final
                            print(f"  -> ✅ NOME CAPTURADO COM SUCESSO: {nome_empresa_formatado}", flush=True)
                        break
                        
        except Exception as e:
            print(f"  -> ❌ Aviso: Falha na extração do nome. Erro: {e}", flush=True)

        # Cria a pasta para salvar os arquivos
        pasta_destino = os.path.join(os.getcwd(), "downloads_reinf", f"{cnpj_limpo}_{nome_empresa_formatado}")
        os.makedirs(pasta_destino, exist_ok=True)

        print("  -> Acessando EFD-Reinf...", flush=True)
        await self.page.goto("https://www3.cav.receita.fazenda.gov.br/reinfweb/")
        await asyncio.sleep(3)

        print(f"[PASSO 4/5] Processando Evento R-2099...", flush=True)
        resultado_2099 = await self._processar_evento_reinf("2099", cnpj_limpo, competencia, pasta_destino, nome_empresa_formatado)
        await asyncio.sleep(3)

        print(f"[PASSO 5/5] Processando Evento R-4099...", flush=True)
        resultado_4099 = await self._processar_evento_reinf("4099", cnpj_limpo, competencia, pasta_destino, nome_empresa_formatado)

        return {
            "status": "CONSULTA_FINALIZADA",
            "cnpj": cnpj_limpo,
            "empresa": nome_empresa_formatado,
            "R-2099": resultado_2099,
            "R-4099": resultado_4099
        }

    async def _processar_evento_reinf(self, evento: str, cnpj_limpo: str, competencia: str, pasta_destino: str, nome_empresa_formatado: str) -> str:
        """Navega pelo menu da EFD-Reinf e gera o PDF."""
        print(f"  -> Navegando para a tela R-{evento}...", flush=True)
        seletor_menu_item = f'a[data-testid*="{evento}"]'
        try:
            menu_pai = self.page.locator('ul#nav li.submenu').first
            if await menu_pai.is_visible():
                await menu_pai.hover()
                await asyncio.sleep(1)
            link_evento = self.page.locator(seletor_menu_item).first
            if await link_evento.is_visible():
                await link_evento.click()
            else:
                await self.page.goto(f"https://www3.cav.receita.fazenda.gov.br/reinfweb/#/{evento}/lista")
        except Exception:
            await self.page.goto(f"https://www3.cav.receita.fazenda.gov.br/reinfweb/#/{evento}/lista")

        seletor_inicio = '#mes_ano_inicio, #periodo_inicial_pesquisa'
        campo_inicio = self.page.locator(seletor_inicio).first
        await campo_inicio.wait_for(state="visible", timeout=45000)
        await campo_inicio.fill(competencia)
        
        seletor_fim = '#mes_ano_fim, #periodo_final_pesquisa'
        await self.page.locator(seletor_fim).first.fill(competencia)
        
        seletor_btn_pesquisar = 'button[data-testid*="botao_listar"], button[data-testid="botao_pesquisar"], button:has-text("Pesquisar")'
        btn_pesquisar = self.page.locator(seletor_btn_pesquisar).first
        await btn_pesquisar.click()
        await asyncio.sleep(4)
        
        linha_resultado = self.page.locator('table.dataGrid tr.even, table.dataGrid tr.odd').first
        if await linha_resultado.count() > 0:
            situacao = await linha_resultado.locator('td').nth(1).inner_text()
            print(f"  -> Situação do Evento R-{evento}: {situacao}", flush=True)
            if "fechada" in situacao.strip().lower():
                competencia_formatada = competencia.replace('/', '-')
                nome_arquivo = f"EFD-REINF-{evento}-{competencia_formatada}-{nome_empresa_formatado}.pdf"
                caminho_pdf = os.path.join(pasta_destino, nome_arquivo)
                print(f"  -> Gerando PDF em: {caminho_pdf}", flush=True)
                await self.page.pdf(path=caminho_pdf, format="A4", landscape=False, print_background=True)
                return "FECHADA_PDF_GERADO"
            else:
                return f"SITUACAO_ENCONTRADA ({situacao})"
        else:
            return "SEM_MOVIMENTO"

    async def fechar_sessao(self):
        """Encerra as conexões."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.processo_chrome:
            self.processo_chrome.terminate()