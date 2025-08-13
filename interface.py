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

st.set_page_config(page_title="EXDROP - Sergipe", layout="centered")
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
    
    # --- LÓGICA CONDICIONAL PARA OS MESES ---
    
    # Define quais cidades usam o filtro de mês
    cidades_com_filtro_mensal = ["aracaju", "barra", "pirambu", "pacatuba"]
    
    # Verifica se qualquer uma das cidades selecionadas precisa do filtro de mês
    mostrar_filtro_mes = any(cidade in cidades_com_filtro_mensal for cidade in cidades_selecionadas)
    
    anos_texto = st.text_input(
        "Anos para Processar (separados por vírgula):",
        value=", ".join(config.get("anos_para_processar", []))
    )
    
    # A variável 'meses_para_processar' só será definida se o campo for exibido
    meses_para_processar = None
    if mostrar_filtro_mes:
        st.info("Para Aracaju, Barra e Pirambu, você pode especificar os meses. Se deixado em branco, todos os 12 meses serão processados.")
        meses_texto = st.text_input(
            "Meses para Processar (separados por vírgula, ex: 01, 02, 11):",
            value=", ".join(config.get("meses_para_processar", [])),
            placeholder="Deixe em branco para processar todos os meses"
        )
        # Converte o texto em uma lista limpa. Se for vazio, a lista será vazia.
        meses_para_processar = [mes.strip() for mes in meses_texto.split(',') if mes.strip()]
    
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
        # Adiciona ou remove a chave de meses do config
        if meses_para_processar is not None:
             # Se a lista estiver vazia (usuário apagou), usa None. Senão, usa a lista.
            config["meses_para_processar"] = meses_para_processar if meses_para_processar else None
        else:
            # Garante que a chave não exista se nenhuma cidade relevante foi selecionada
            config.pop("meses_para_processar", None)
        
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
                        
                        # Log funcionando (sem rolagem automática)
                        #log_placeholder.code(log_output, language='log')
                        
                        # Log com rolagem automática
                        log_html = f"""
                        <div style="height: 400px; overflow-y: auto; border: 1px solid #ccc; border-radius: 5px; padding: 10px; font-family: monospace; white-space: pre-wrap;" id="log-container">
                            {log_output}
                        </div>
                        <script>
                            var container = document.getElementById("log-container");
                            container.scrollTop = container.scrollHeight;
                        </script>
                        """
                        # Usa st.html para renderizar o log e executar o script
                        log_placeholder.html(log_html)  

                    processo.stdout.close()
                    processo.wait() # Espera o processo realmente terminar

                    if processo.returncode == 0:
                        st.success("Extração concluída com sucesso!")
                    else:
                        st.error("O processo terminou com um código de erro. Verifique o log acima.")

                except Exception as e:
                    st.error(f"Falha ao iniciar o processo de extração: {e}")