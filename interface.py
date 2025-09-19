# Em: interface.py

import streamlit as st
import json
import subprocess
import os
import time
import re

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

st.set_page_config(page_title="EXDROP - Sergipe", layout="centered")
st.image("https://i.imgur.com/626n32H.png", width=150)
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
        value=", ".join(config.get("anos_para_processar", [])),
        key='anos_input'
    )
    
    # Lógica condicional para os meses
    cidades_com_filtro_mensal = ["aracaju", "barra", "pirambu", "pacatuba"]
    mostrar_filtro_mes = any(cidade in cidades_com_filtro_mensal for cidade in cidades_selecionadas)
    
    meses_para_processar = None
    if mostrar_filtro_mes:
        st.info("Para as cidades selecionadas, você pode especificar os meses. Se deixado em branco, todos os 12 meses serão processados.")
        meses_texto = st.text_input(
            "Meses para Processar (separados por vírgula, ex: 01, 02, 11):",
            value=", ".join(config.get("meses_para_processar") or []),
            placeholder="Deixe em branco para processar todos os meses",
            key='meses_input'
        )
        meses_para_processar = [mes.strip() for mes in meses_texto.split(',') if mes.strip()]
    
    max_workers = st.slider(
        "Número de Processos Paralelos (Workers):",
        min_value=1, max_value=12,
        value=config.get("configuracoes_paralelismo", {}).get("max_workers", 4),
        key='-WORKERS-',
        help="""
        **O que é um Worker?**
        
        Pense em cada 'worker' como um robô (navegador) trabalhando em paralelo para extrair os dados.
        
        - **Mais workers:** A extração pode terminar mais rápido.
        - **Muitos workers:** Podem sobrecarregar seu computador, causando lentidão ou erros.
        
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
        # Atualiza o dicionário de configuração
        anos_lista = [ano.strip() for ano in anos_texto.split(',') if ano.strip()]
        meses_lista = meses_para_processar if meses_para_processar is not None else []

        config["prefeituras_para_processar"] = cidades_selecionadas
        config["anos_para_processar"] = anos_lista
        config["configuracoes_paralelismo"]["max_workers"] = max_workers
        
        if meses_para_processar is not None:
            config["meses_para_processar"] = meses_para_processar if meses_para_processar else None
        else:
            config.pop("meses_para_processar", None)

        salvar_config(config)
        st.success(f"Configurações salvas no arquivo '{CONFIG_FILE}'!")
        
        # Prepara o comando de execução
        comando = ["python", "-X", "utf8", "-u", "main.py"]
        if modo_visual:
            comando.append("--visual")
        
        st.info(f"Iniciando processo com o comando: `{' '.join(comando)}`")
        st.markdown("---")
        
        # --- LÓGICA FINAL COM LAYOUT ESTÁVEL E PROGRESSO ---
        
        # 1. Prepara todos os placeholders de uma só vez
        st.subheader("Progresso Geral")
        barra_progresso = st.progress(0, text="Aguardando início da extração...")
        spinner_placeholder = st.empty()
        st.subheader("Log Detalhado da Execução")
        log_container = st.container(height=400)
        log_placeholder = log_container.empty()
        
        # 2. Prepara os contadores
        is_pacatuba_anual = "pacatuba" in cidades_selecionadas and not meses_lista
        if is_pacatuba_anual:
            total_de_tarefas = len(anos_lista) * max_workers
        else:
            num_meses_por_ano = len(meses_lista) if meses_lista else 12
            total_de_tarefas = len(cidades_selecionadas) * len(anos_lista) * num_meses_por_ano
            
        tarefas_concluidas = 0
        paginas_concluidas = 0
        start_time = time.time()
        
        # 3. Executa o processo e atualiza a UI
        with spinner_placeholder.container():
            with st.spinner('A extração está em andamento... Não feche esta janela.'):
                try:
                    processo = subprocess.Popen(
                        comando,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding='utf-8', errors='replace'
                    )
                    
                    log_output = ""
                    for linha in iter(processo.stdout.readline, ''):
                        log_output += linha
                        log_placeholder.code(log_output, language='log')
                        
                        # Gatilhos de progresso
                        if "Extraindo dados da página" in linha:
                            paginas_concluidas += 1
                        
                        gatilho_mensal = "Dados salvos para" in linha or "Nenhum registro de royalties foi extraído" in linha
                        gatilho_pacatuba_anual = "[PROGRESSO]" in linha

                        if gatilho_mensal or gatilho_pacatuba_anual:
                            tarefas_concluidas += 1
                        
                        # Atualiza a barra de progresso e o texto
                        progresso_percentual = min(1.0, tarefas_concluidas / total_de_tarefas) if total_de_tarefas > 0 else 0
                        elapsed_time = time.time() - start_time
                        texto_progresso = ""
                        
                        if tarefas_concluidas > 0:
                            avg_time_per_task = elapsed_time / tarefas_concluidas
                            remaining_tasks = total_de_tarefas - tarefas_concluidas
                            etr_seconds = remaining_tasks * avg_time_per_task
                            etr_mins, etr_secs = divmod(int(etr_seconds), 60)
                            etr_formatted = f"{etr_mins}min {etr_secs}s"
                            texto_progresso = f"Concluído: {tarefas_concluidas}/{total_de_tarefas} ({progresso_percentual:.0%}). Restante: ~{etr_formatted}"
                        elif paginas_concluidas > 0:
                            avg_time_per_page = elapsed_time / paginas_concluidas
                            texto_progresso = f"Processando... ({paginas_concluidas} páginas | Média: {avg_time_per_page:.1f}s por página)"

                        if texto_progresso:
                            barra_progresso.progress(progresso_percentual, text=texto_progresso)

                    processo.wait()
                    
                    spinner_placeholder.empty()
                    
                    if processo.returncode == 0:
                        st.success("Extração concluída com sucesso!")
                        total_time = time.time() - start_time
                        total_mins, total_secs = divmod(int(total_time), 60)
                        barra_progresso.progress(1.0, text=f"Concluído em {total_mins}min {total_secs}s!")
                    else:
                        st.error("O processo terminou com um código de erro. Verifique o log acima.")

                except Exception as e:
                    spinner_placeholder.empty()
                    st.error(f"Falha ao iniciar o processo de extração: {e}")