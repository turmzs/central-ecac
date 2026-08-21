# 🤖 Robô Fiscal - Automação EFD-Reinf (e-CAC)

Uma ferramenta de automação RPA (Robotic Process Automation) com Interface Gráfica, desenvolvida em Python, para otimizar o fluxo de trabalho do departamento fiscal. O robô acessa o portal e-CAC da Receita Federal do Brasil, faz a troca de procurações em lote e realiza o download automático dos comprovantes da EFD-Reinf (Eventos R-2099 e R-4099).

---

## ✨ Funcionalidades Principais

* **🖥️ Interface Gráfica (GUI):** Tela intuitiva construída em Tkinter, permitindo que qualquer colaborador utilize o robô sem conhecimentos de programação.
* **📦 Processamento em Lote:** Capacidade de colar dezenas de CNPJs de uma só vez para processamento sequencial.
* **🧠 Captura Inteligente de Nomenclatura:** O robô inspeciona o HTML do e-CAC, lê o nome da empresa logada no cabeçalho de perfil, higieniza o texto e utiliza-o para nomear pastas e ficheiros automaticamente (ex: `ALFA-GERADORES-LTDA`).
* **🛡️ Resiliência e Tratamento de Erros:** O sistema identifica automaticamente empresas "Sem Procuração", regista o aviso no log visual e pula para o próximo cliente sem interromper a automação.
* **🕵️ Sessão Persistente (Anti-Bloqueio):** Utiliza o protocolo CDP (Chrome DevTools Protocol) para reaproveitar uma sessão física do Google Chrome. Isto evita bloqueios de IP pelo firewall do governo e permite passar por barreiras de Captcha iniciais de forma estável.
* **📂 Organização de Arquivos:** Os PDFs de recibos (Fechamento e Reabertura) são guardados e organizados automaticamente em `/downloads_reinf/[CNPJ]_[NOME_DA_EMPRESA]`.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.8+** (Linguagem base)
* **Playwright (Async):** Motor de automação web.
* **Tkinter:** Biblioteca nativa para a Interface Gráfica.
* **Asyncio & Threading:** Processamento paralelo para evitar o congelamento da interface durante a navegação web.
* **Regex (Re):** Expressões regulares para higienização de strings e extração de dados do HTML.

---

## ⚙️ Pré-requisitos e Instalação

### 1. Requisitos do Sistema

* Computador com Windows.
* **Google Chrome** instalado no diretório padrão (`C:\Program Files\Google\Chrome\Application\chrome.exe`).
* Certificado Digital (e-CNPJ/e-CPF) previamente configurado na máquina para acesso ao e-CAC.

### 2. Instalação das Bibliotecas

Abra o terminal na pasta do projeto e instale o Playwright:

```bash
pip install playwright
playwright install chromium
3. Configuração do Perfil do Robô (Muito Importante)
O robô precisa de uma pasta dedicada no seu computador para guardar os "cookies" de sessão do Chrome e evitar ser detetado como bot.

Vá até à unidade C:\.

Crie uma pasta vazia chamada exatamente: perfil_cdp_robo.

Opcional: Se for a primeira vez que usa o robô, o Chrome pode abrir pedindo para escolher o Certificado Digital. Marque a opção de "Lembrar decisão" para que o processo fique 100% automático.

🚀 Como Usar a Ferramenta
Execute o aplicativo através do terminal ou dando duplo clique no script (se configurado no Windows):

Bash
python app_gui.py
Na janela que se abrir, digite a Competência desejada (ex: 07/2026).

Cole a Lista de CNPJs na caixa de texto (apenas números ou com pontuação, um por linha).

Clique em ▶ INICIAR AUTOMAÇÃO.

Acompanhe o progresso em tempo real pela caixa preta de Log na própria interface.

Ao finalizar, acesse a pasta downloads_reinf gerada na raiz do projeto para recolher os PDFs.

📁 Estrutura do Projeto
Plaintext
/
├── app_gui.py                     # Arquivo principal (Interface Gráfica e Lógica de Threads)
├── app/
│   └── providers/
│       ├── base.py                # Classe base/abstrata
│       └── playwright_reinf.py    # Motor do robô, navegação e extração web
├── downloads_reinf/               # Pasta gerada automaticamente com os PDFs
└── README.md                      # Documentação do projeto
⚠️ Boas Práticas e Responsabilidade (RPA)
Este robô foi programado com tempos de espera (sleep) adequados para simular o comportamento humano e não sobrecarregar os servidores da Receita Federal do Brasil. Evite remover as pausas do código para não correr o risco de ter o endereço de IP do escritório bloqueado pelo firewall governamental.


### O que fazer agora?
Com o seu `README.md` criado e a Interface Gráfica pronta, o seu projeto deixou de ser apenas um script solto e tornou-se um **Software de Automação Profissional**. 

Você pode abrir este ficheiro em qualquer editor de código (como o VS Code) e ele será exibido lindamente com formatação, ícones e cores.

Se quiser testar a interface mais algumas vezes ou se houver algum último ajuste estético que queira fazer no Tkinter para
