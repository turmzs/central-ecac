import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import asyncio
import sys

# Importamos o nosso robô perfeito!
from app.providers.playwright_reinf import PlaywrightReinfProvider

class RedirecionadorLog:
    """Classe responsável por pegar os 'prints' do terminal e enviar para a tela do Tkinter."""
    def __init__(self, widget_texto):
        self.widget_texto = widget_texto

    def write(self, texto):
        # Insere o texto no final da caixa de log
        self.widget_texto.insert(tk.END, texto)
        # Rola a barra de scroll automaticamente para baixo
        self.widget_texto.see(tk.END)
        # Atualiza a tela
        self.widget_texto.update_idletasks()
        
    def flush(self):
        # Necessário para evitar erros com o argumento flush=True dos nossos prints
        pass

class AppRoboReinf:
    def __init__(self, root):
        self.root = root
        self.root.title("Robô Fiscal - EFD Reinf Automático")
        self.root.geometry("650x600") # Largura x Altura
        self.root.configure(padx=20, pady=20)

        # --- SEÇÃO 1: COMPETÊNCIA ---
        tk.Label(root, text="Competência (MM/AAAA):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.entrada_competencia = tk.Entry(root, font=("Arial", 12), width=15)
        self.entrada_competencia.pack(anchor="w", pady=(0, 15))

        # --- SEÇÃO 2: LISTA DE CNPJS ---
        tk.Label(root, text="Lista de CNPJs (Um por linha):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.caixa_cnpjs = scrolledtext.ScrolledText(root, height=8, font=("Arial", 10))
        self.caixa_cnpjs.pack(fill="x", pady=(0, 15))

        # --- SEÇÃO 3: BOTÃO INICIAR ---
        self.btn_iniciar = tk.Button(
            root, 
            text="▶ INICIAR AUTOMAÇÃO", 
            font=("Arial", 12, "bold"), 
            bg="#4CAF50", # Cor verde
            fg="white", 
            command=self.iniciar_robo_em_background
        )
        self.btn_iniciar.pack(fill="x", pady=(0, 15))

        # --- SEÇÃO 4: LOG DE EXECUÇÃO (O TERMINAL VISUAL) ---
        tk.Label(root, text="Acompanhamento (Log):", font=("Arial", 10, "bold")).pack(anchor="w")
        self.caixa_log = scrolledtext.ScrolledText(root, height=12, font=("Consolas", 9), bg="black", fg="lightgreen")
        self.caixa_log.pack(fill="both", expand=True)

        # Redireciona o terminal do sistema para a nossa caixa preta de log!
        sys.stdout = RedirecionadorLog(self.caixa_log)

    def iniciar_robo_em_background(self):
        """Prepara os dados e cria uma Thread (linha paralela) para não congelar o Tkinter."""
        competencia = self.entrada_competencia.get().strip()
        cnpjs_brutos = self.caixa_cnpjs.get("1.0", tk.END).strip()

        if not competencia:
            messagebox.showwarning("Aviso", "Por favor, digite a competência!")
            return
        if not cnpjs_brutos:
            messagebox.showwarning("Aviso", "Por favor, cole pelo menos um CNPJ!")
            return

        # Desativa o botão para o usuário não clicar duas vezes
        self.btn_iniciar.config(state="disabled", text="⏳ RODANDO...")
        
        # Cria a lista de CNPJs separando por linha
        lista_cnpjs = cnpjs_brutos.split('\n')

        # Inicia a Thread que vai rodar o motor do Playwright
        thread = threading.Thread(target=self.motor_assincrono, args=(competencia, lista_cnpjs))
        thread.daemon = True # Se fechar a janela, o robô morre junto
        thread.start()

    def motor_assincrono(self, competencia, lista_cnpjs):
        """Esta função roda fora da tela principal. Ela inicia o loop do asyncio."""
        # Cria um novo loop de eventos assíncronos para esta Thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Roda a função principal do robô
        loop.run_until_complete(self.fluxo_do_robo(competencia, lista_cnpjs))
        loop.close()

        # Quando acabar, reativa o botão
        self.btn_iniciar.config(state="normal", text="▶ INICIAR AUTOMAÇÃO")
        print("\n[SISTEMA] Processo de Lote Finalizado com Sucesso!", flush=True)
        messagebox.showinfo("Sucesso", "O processamento do lote foi concluído!")

    async def fluxo_do_robo(self, competencia, lista_cnpjs):
        """O cérebro da automação em Lote."""
        robo = PlaywrightReinfProvider()
        try:
            print("="*50, flush=True)
            print(f"INICIANDO LOTE: {len(lista_cnpjs)} empresa(s) para a competência {competencia}", flush=True)
            print("="*50, flush=True)

            await robo.iniciar_sessao_diaria()

            for i, cnpj in enumerate(lista_cnpjs):
                cnpj_limpo = cnpj.strip()
                if not cnpj_limpo:
                    continue # Pula linhas em branco
                
                print(f"\n[{i+1}/{len(lista_cnpjs)}] Processando CNPJ: {cnpj_limpo}", flush=True)
                
                # Executa a função que criámos (agora sem precisar passar o nome!)
                resultado = await robo.consultar(cnpj=cnpj_limpo, competencia=competencia)
                
                status = resultado.get("status")
                if status == "SEM_PROCURACAO":
                    print(f"  -> Empresa ignorada. Motivo: Sem procuração.", flush=True)
                else:
                    print(f"  -> Concluído para a empresa: {resultado.get('empresa')}", flush=True)
                
                # Uma pequena pausa humana entre as empresas para não sobrecarregar o e-CAC
                await asyncio.sleep(2)

        except Exception as e:
            print(f"\n[ERRO CRÍTICO] O robô parou inesperadamente: {e}", flush=True)
        finally:
            await robo.fechar_sessao()

# --- INICIALIZAÇÃO DO APLICATIVO ---
if __name__ == "__main__":
    janela_principal = tk.Tk()
    app = AppRoboReinf(janela_principal)
    janela_principal.mainloop()