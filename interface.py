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
        json.dump(config, f, indent=2)

# --- Construção da Interface ---

st.set_page_config(page_title="Extrator de Royalties", layout="centered")
st.title("⚙️ Painel de Controle - Extrator de Royalties")
st.markdown("Use esta interface para configurar e iniciar a extração de dados.")

# Carrega a configuração existente
config = carregar_config()

# Define a lista de todas as cidades possíveis
todas_as_cidades = ["aracaju", "barra", "pirambu", "pacatuba"]

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
        min_value=1, max_value=4,
        value=config.get("configuracoes_paralelismo", {}).get("max_workers", 4)
    )

st.markdown("---")

# Seção de Execução
with st.container(border=True):
    st.subheader("2. Execute a Extração")
    if st.button("Salvar Configurações e Iniciar Extração Local", type="primary"):
        # Atualiza o dicionário de configuração com os novos valores
        config["prefeituras_para_processar"] = cidades_selecionadas
        config["anos_para_processar"] = [ano.strip() for ano in anos_texto.split(',') if ano.strip()]
        config["configuracoes_paralelismo"]["max_workers"] = max_workers

        # Salva o arquivo config.json atualizado
        salvar_config(config)
        st.success(f"Configurações salvas no arquivo '{CONFIG_FILE}'!")
        
        # Executa o script principal em um subprocesso
        st.info("Iniciando o processo de extração... Acompanhe o progresso no terminal que executou este painel.")
        
        with st.spinner('A extração está em andamento. Isso pode levar vários minutos...'):
            processo = subprocess.Popen(
                ["python", "-u", "main.py"], # O -u garante que a saída seja mostrada em tempo real
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Mostra a saída do log em tempo real
            log_placeholder = st.empty()
            log_output = ""
            for linha in processo.stdout:
                log_output += linha
                log_placeholder.code(log_output)

            # Espera o processo terminar e pega a saída de erro, se houver
            stdout, stderr = processo.communicate()

            if processo.returncode == 0:
                st.success("Extração concluída com sucesso!")
            else:
                st.error("Ocorreu um erro durante a extração. Verifique os logs.")
                st.code(stderr)