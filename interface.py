# Em: interface.py

import streamlit as st
import json
import subprocess
import os

CONFIG_FILE = 'config.json'

# Função para carregar a configuração atual
def carregar_config():
    """Lê o arquivo de configuração e retorna um dicionário Python."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Retorna uma configuração padrão se o arquivo não existir
    return {
        "anos_para_processar": ["2024"],
        "prefeituras_para_processar": ["pacatuba"],
        "configuracoes_paralelismo": {"max_workers": 4},
        "configuracoes_cidades": {}
    }

# Função para salvar a nova configuração
def salvar_config(config):
    """Salva o dicionário de configuração no arquivo JSON."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# --- Construção da Interface ---

st.set_page_config(page_title="Extrator de Royalties", layout="centered")
st.header("EXDROP")
st.title("⚙️ Painel de Controle - ExDRoP")
st.subheader("Extrator de Dados de Royalties do Petróleo")
st.markdown("Use esta interface para configurar e iniciar a extração de dados de royalties.")

config = carregar_config()
todas_as_cidades = list(config.get("configuracoes_cidades", {}).keys())

st.markdown("---")

# Seção de Configuração
with st.container(border=True):
    st.subheader("1. Selecione os Parâmetros")
    cidades_selecionadas = st.multiselect(
        "Prefeituras para Processar:",
        options=todas_as_cidades,
        default=config.get("prefeituras_para_processar", [])
    )

    anos_texto = st.text_input(
        "Anos para Processar (separados por vírgula):",
        value=", ".join(config.get("anos_para_processar", []))
    )
    
    max_workers = st.slider(
    "Número de Processos Paralelos (Workers):",
    min_value=1,
    max_value=12, # Aumentei o máximo para dar mais flexibilidade
    value=config.get("configuracoes_paralelismo", {}).get("max_workers", 4),
    key='-WORKERS-',
    help="""
    **O que é um Worker?**
    
    Pense em cada 'worker' como um robô (navegador) trabalhando em paralelo para extrair os dados.
    
    - **Mais workers:** A extração pode terminar mais rápido.
    - **Muitos workers:** Podem sobrecarregar seu computador, causando lentidão ou erros (como 'tab crashed').
    
    **Como saber a capacidade da sua máquina?**
    1. Abra o **Gerenciador de Tarefas** (`Ctrl + Shift + Esc`).
    2. Vá para a aba **Desempenho** e clique em **CPU**.
    3. Procure o número de **Núcleos**.
    
    Uma boa regra é começar com um número de workers igual ou um pouco menor que o número de **Núcleos** do seu processador.
    """
    )
    
    modo_visual = st.checkbox(
        "Executar em modo visual (não-headless)?",
        value=False,
        help="Marque esta opção para ver as janelas do navegador durante a extração. Use apenas para depuração."
    )

st.markdown("---")

# Seção de Execução
with st.container(border=True):
    st.subheader("2. Execute a Extração")
    if st.button("Salvar Configurações e Iniciar Extração", type="primary"):
        # Atualiza o dicionário de configuração com os novos valores
        config["prefeituras_para_processar"] = cidades_selecionadas
        config["anos_para_processar"] = [ano.strip() for ano in anos_texto.split(',') if ano.strip()]
        config["configuracoes_paralelismo"]["max_workers"] = max_workers
        salvar_config(config)
        st.success(f"Configurações salvas no arquivo '{CONFIG_FILE}'!")
        
        # Prepara o comando de execução com a flag --visual, se necessário
        comando = ["python", "-X", "utf8", "-u", "main.py"]
        if modo_visual:
            comando.append("--visual")
        
        st.info(f"Iniciando processo com o comando: `{' '.join(comando)}`")
        st.markdown("---")
        
        # --- LÓGICA DE EXIBIÇÃO DE LOG EM TEMPO REAL ---
        with st.container(height=400):
            log_placeholder = st.empty()
            log_output = ""
            
            with st.spinner('A extração está em andamento...'):
                try:
                    # O '-u' (unbuffered) e 'stderr=subprocess.STDOUT' são cruciais para o log em tempo real
                    processo = subprocess.Popen(
                        comando,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, # Junta a saída de erro com a saída padrão
                        text=True,
                        encoding='utf-8',
                        errors='replace' # Evita erros de decodificação de caracteres
                    )
                    
                    # Lê a saída do processo linha por linha enquanto ele executa
                    for linha in iter(processo.stdout.readline, ''):
                        log_output += linha
                        log_placeholder.code(log_output, language='log')

                    processo.stdout.close()
                    processo.wait() # Espera o processo realmente terminar

                    if processo.returncode == 0:
                        st.success("Extração concluída com sucesso!")
                    else:
                        st.error("O processo terminou com um código de erro. Verifique o log acima.")

                except Exception as e:
                    st.error(f"Falha ao iniciar o processo de extração: {e}")