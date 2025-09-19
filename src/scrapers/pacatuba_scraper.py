# src/scrapers/pacatuba_scraper.py

import logging
import os
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from typing import List


import numpy
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager

# Importa o logger e o contexto da thread do nosso módulo comum
from src.common.logging_setup import log_context
from src.common.file_utils import unir_csvs_por_ano

# --- Constantes e Funções Auxiliares Específicas de Pacatuba ---

TERMOS_ROYALTIES = ["royaltie", "royalty", "petroleo"]

RE_REMOVE_PUNCTUATION = re.compile(r'[^a-zA-Z0-9\s]')

def normalizar(texto: str) -> str:
    """
    Normaliza um texto removendo acentos, pontuações e convertendo para minúsculas.
    """
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = RE_REMOVE_PUNCTUATION.sub('', texto)
    return texto.lower()

# --- Funções de Interação com Selenium para Pacatuba ---

def start_driver_pacatuba(headless=False, executable_path=None) -> webdriver.Chrome:
    logger = logging.getLogger('exdrop_osr')
    logger.info("Iniciando driver do Chrome para Pacatuba...")
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    else:
        options.add_argument('--window-size=1920,1080')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-dev-shm-usage")
    
    # Lógica para usar o caminho pré-instalado ou o WebDriverManager
    if executable_path:
        service = ChromeService(executable_path=executable_path)
    else:
        service = ChromeService(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def selecionar_dropdown_pacatuba(driver, container_id, texto):
    logger = logging.getLogger('exdrop_osr')
    try:
        logger.info(f"Selecionando: {texto}")
        trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@aria-labelledby='{container_id}']"))
        )
        trigger.click()
        opcao = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//li[contains(@class, 'select2-results__option') and normalize-space(.)='{texto}']"))
        )
        opcao.click()
    except Exception as e:
        logger.error(f"Erro ao selecionar {texto} no campo {container_id}: {e}")
        raise

def ir_para_proxima_pagina_pacatuba(driver, tentativas_maximas=3):
    """
    Tenta clicar no botão 'Próxima Página' com lógica de retentativas.
    """
    logger = logging.getLogger('osr_project')
    
    for tentativa in range(1, tentativas_maximas + 1):
        try:
            logger.info(f"Tentando navegar para a próxima página (Tentativa {tentativa}/{tentativas_maximas})...")
            
            # Pega a referência do primeiro item da tabela ANTES de clicar
            primeira_linha_antes = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table/tbody/tr[1]"))
            )
            proxima_pagina_locator = (By.XPATH, "//a[contains(@class, 'page-link')][i[contains(@class, 'next')]]")
            botao = driver.find_element(*proxima_pagina_locator)
            parent_li = botao.find_element(By.XPATH, "./parent::li")
            
            if "disabled" in parent_li.get_attribute("class"):
                logger.info("Última página alcançada.")
                return False

            driver.execute_script("arguments[0].click();", botao)
            logger.info("Navegando para a próxima página de resultados.")
            
            # Esperamos que referência da primeira linha da página anterior se torne "stale" (obsoleta).
            # Isso confirma que o DOM foi atualizado.
            WebDriverWait(driver, 20).until(
                EC.staleness_of(primeira_linha_antes)
            )
            logger.debug("Confirmação de que a tabela foi recarregada (elemento anterior obsoleto).")
            
            # Opcional: uma espera adicional para a visibilidade da nova tabela
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//table/tbody")))
            
            logger.debug("Navegou para a próxima página com sucesso.")
            return True
        
        except (TimeoutException, NoSuchElementException) as e:
                logger.warning(f"Falha na tentativa {tentativa}: {type(e).__name__}. Verificando se é o fim da paginação.")
                
                # Checa novamente se o botão de próximo existe e está desabilitado
                try:
                    if "disabled" in driver.find_element(By.ID, "lista_next").get_attribute("class"):
                        logger.info("Confirmação de que a última página foi alcançada.")
                        return False
                except:
                    pass # Se não encontrar, continua para a próxima tentativa

                if tentativa < tentativas_maximas:
                    tempo_espera = 5 * tentativa # Espera 5s, 10s...
                    logger.info(f"Aguardando {tempo_espera} segundos antes da próxima tentativa.")
                    time.sleep(tempo_espera)
                    driver.refresh() # Recarrega a página para tentar "desbloquear"
                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//table/tbody")))
                else:
                    logger.error("Número máximo de tentativas atingido. Abortando a paginação.")
                    
                    # Salva o diagnóstico na última tentativa falha
                    # --- LÓGICA DE DIAGNÓSTICO ---
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    screenshot_path = f"logs/pacatuba_erro_pagina_{timestamp}.png"
                    html_path = f"logs/pacatuba_erro_pagina_{timestamp}.html"
                    
                    driver.save_screenshot(screenshot_path)
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    
                    logger.error(f"Captura de tela salva em: {screenshot_path}")
                    logger.error(f"Código HTML da página salvo em: {html_path}")
                    # --- FIM DO DIAGNÓSTICO ---
                    return False # Desiste após todas as tentativas
        
        return False
            
# --- Worker e Função Principal de Pacatuba ---

def worker_processar_mes_pacatuba(cidade_config: dict, ano_mes_tuple: tuple, driver_path: str, headless: bool):
    """
    Worker que extrai dados de um ÚNICO MÊS para Pacatuba.
    Ele seleciona o filtro "Mês" e depois coleta e processa os links.
    """
    ano, mes = ano_mes_tuple
    log_context.task_id = f"Pacatuba-{ano}-{mes}"
    logger = logging.getLogger('exdrop_osr')
    logger.info(f"Worker MENSAL iniciado para Pacatuba - {mes}/{ano}.")
    
    links_do_mes = []
    driver = None
    try:
        driver = start_driver_pacatuba(headless=headless, executable_path=driver_path)
        driver.get(cidade_config['url'])
        
        # Lidando com pop-up dos cookies
        try:
            # Espera até 10 segundos para o botão de rejeitar cookies aparecer e ser clicável
            logger.info("Procurando por banner de cookies para rejeitar...")
            
            botao_rejeitar_cookies = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "rejectCookie"))
            )
            
            # Clica no botão para fechar o banner
            botao_rejeitar_cookies.click()
            logger.info("Banner de cookies rejeitado com sucesso.")
            
            # Adiciona uma pequena pausa para a animação do banner desaparecer
            time.sleep(1)
        except TimeoutException:
                # Se o botão não aparecer em 10 segundos, assume que não há banner
                logger.info("Nenhum banner de cookies encontrado para interagir.")
                pass

        # --- LÓGICA DE FILTRAGEM MENSAL ---
        # 1. Clica no botão de rádio "Mês"
        logger.info("Selecionando modo de filtro por Mês.")
        driver.find_element(By.ID, "filtro_2").click()
        
        # 2. Seleciona o Ano e o Mês
        selecionar_dropdown_pacatuba(driver, "select2-ano-container", ano)
        selecionar_dropdown_pacatuba(driver, "select2-mes-container", mes) # Usa o ID do dropdown de mês
        
        # 3. Clica em Buscar
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#filtrar.btn-buscar"))).click()
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//table/tbody")))
        
        # 4. Coleta os links da(s) página(s) de resultado para este mês
        pagina_atual = 1
        while True:
            logger.info(f"Coletando links da página {pagina_atual} para o mês {mes}/{ano}...")
            botoes_detalhes = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//td[@serigyitem='detalhesPagamento']/a")))
            for botao in botoes_detalhes:
                if link := botao.get_attribute('href'):
                    links_do_mes.append(link)
            if not ir_para_proxima_pagina_pacatuba(driver):
                break
            pagina_atual += 1
        
    finally:
        if driver:
            driver.quit()
    
    # 5. Processa os links coletados para este mês
    if links_do_mes:
        # Reutilizamos nosso worker de extração de detalhes já existente!
        dados_finais_mes = worker_extrair_detalhes_pacatuba(links_do_mes, ano, driver_path, headless)
        
        if dados_finais_mes:
            # Salva o arquivo CSV para este mês específico
            cidade_nome = cidade_config.get('nome', 'pacatuba')
            output_dir = os.path.join("data", "processed", cidade_nome)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{cidade_nome}_royalties_{ano}_{mes}.csv")
            pd.DataFrame(dados_finais_mes).to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
            logger.info(f"Dados salvos para Pacatuba - {mes}/{ano} em {output_path}")


def worker_extrair_detalhes_pacatuba(links: List[str], ano_alvo: str, driver_path: str, headless:bool) -> List[dict]:
    log_context.task_id = f"Pacatuba-Worker-{threading.get_ident() % 1000}"
    logger = logging.getLogger('exdrop_osr')
    
    logger.info(f"Worker iniciado. Processando {len(links)} links.")
    dados_coletados_pela_thread = []
    driver = None
    try:
        driver = start_driver_pacatuba(headless=headless, executable_path=driver_path)
               
        for i, link in enumerate(links):
            try:
                logger.debug(f"Acessando link {i+1}/{len(links)}.")
                driver.get(link)
                WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "table-dados")))
                
                # Mapa de XPaths para todos os campos na página de detalhes.
                XPATHS_DETALHES = {           
                    'empenho':          '//*[@id="table-dados"]/tbody/tr[2]/td[1]',
                    'credor':           '//*[@id="table-dados"]/tbody/tr[2]/td[2]',
                    'data_nota':        '//*[@id="table-dados"]/tbody/tr[2]/td[3]',

                    'processo':         '//*[@id="table-dados"]/tbody/tr[4]/th[1]',
                    'fonte_recurso':    '//*[@id="table-dados"]/tbody/tr[4]/th[2]',            
                    'numero_documento': '//*[@id="table-dados"]/tbody/tr[4]/th[3]',

                    'valor_pago':       '//*[@id="table-dados"]/tbody/tr[6]/td[1]',
                    'valor_retido':     '//*[@id="table-dados"]/tbody/tr[6]/td[2]',
                    'forma_pagamento':  '//*[@id="table-dados"]/tbody/tr[6]/td[3]',
                    
                    'historico':        '//*[@id="table-historico"]/tbody/tr/td',
                    'relacionado_covid':'//*[@id="table-outras-informacoes"]/tbody/tr/td[1]',
                    'relacionado_LC173':'//*[@id="table-outras-informacoes"]/tbody/tr/td[2]'
                }
                # --- ETAPA 1: Extrair APENAS a Fonte de Recurso para verificação ---
                logger.debug("Verificando a Fonte de Recurso primeiro...")
                fonte_recurso_texto = None
                try:
                    # Usa o XPath específico para a fonte de recurso
                    fonte_recurso_element = driver.find_element(By.XPATH, XPATHS_DETALHES['fonte_recurso'])
                    fonte_recurso_texto = fonte_recurso_element.text.strip()
                    fonte_recurso_texto = normalizar(fonte_recurso_texto)
                    
                except NoSuchElementException:
                    logger.warning(f"Campo 'fonte_recurso' não encontrado no link {link}. Pulando.")
                    continue # Pula para o próximo link
               
                # --- ETAPA 2: Verificar se é de royalties ANTES de extrair o resto ---
                if fonte_recurso_texto and any(termo in fonte_recurso_texto for termo in TERMOS_ROYALTIES):
                    logger.info(f"Royalties encontrados (Fonte: '{fonte_recurso_texto}'). Extraindo todos os dados do link: {link}")
                   
                    dados_completos = {'fonte_recurso': fonte_recurso_texto, 'link_detalhe': link}
                    for nome_campo, xpath in XPATHS_DETALHES.items():
                        if nome_campo == 'fonte_recurso': continue
                        try:
                            dados_completos[nome_campo] = driver.find_element(By.XPATH, xpath).text.strip()
                        except NoSuchElementException:
                            dados_completos[nome_campo] = None
                    dados_coletados_pela_thread.append(dados_completos)
                    
                else:
                    logger.debug(f"Link não é de royalties. Fonte: '{fonte_recurso_texto}'. Pulando extração detalhada.")

                    
            except Exception as e_link:
                logger.error(f"Erro ao processar o link {link}: {e_link}")
                continue
    finally:
        if driver: driver.quit()
        logger.info("Worker finalizado.")
    
    return dados_coletados_pela_thread

def coletar_links_lote(cidade_config: dict, ano: str, pagina_inicial: int, paginas_por_lote: int, driver_path: str, headless: bool) -> tuple[list[str], bool]:
    """
    Função que abre navegador, coleta links de um lote de páginas e fecha o navegador.
    Retorna a lista de links encontrados e um booleano indicando se há mais páginas.
    """
    logger = logging.getLogger('exdrop_osr')
    links_do_lote = []
    driver = None
    ainda_ha_paginas = True
    
    try:
        driver = start_driver_pacatuba(headless=headless, executable_path=driver_path)
        
        # Constrói a URL para ir diretamente para a página inicial do lote
        url_base = cidade_config['url']
        url_lote = f"{url_base}?pagina={pagina_inicial}&alias=pmpacatuba&p=iDespesa&base=189&recursoDESO=false&ano={ano}&tipo=pagamento&filtro=1"
        driver.get(url_lote)
        
        # A navegação direta via URL evita a necessidade de clicar nos filtros novamente
        
        for i in range(paginas_por_lote):
            pagina_atual = pagina_inicial + i
            logger.info(f"Coletando links da página: {pagina_atual}")
            
            try:
                # Aguarda a tabela aparecer antes de tentar extrair
                WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//table/tbody")))
                botoes_detalhes = driver.find_elements(By.XPATH, "//td[@serigyitem='detalhesPagamento']/a")
                for botao in botoes_detalhes:
                    if link := botao.get_attribute('href'):
                        links_do_lote.append(link)
                        
                if not ir_para_proxima_pagina_pacatuba(driver):
                    ainda_ha_paginas = False
                    break # Fim da paginação, sai do loop do lote
            except TimeoutException:
                logger.warning(f"Timeout ao carregar a pagina {pagina_atual}. Assumindo fim da paginação para este lote.")
                ainda_ha_paginas = False
                break
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador do lote de coleta de links foi fechado.")  
            
    return links_do_lote, ainda_ha_paginas
        

def run(cidade_config: dict, anos_para_processar: List[str], meses_para_processar: List[str] | None, max_workers: int, headless:bool):
    """
    Ponto de entrada para o scraper de Pacatuba.
    Decide entre a extração anual (coleta de links em massa) ou mensal
    com base no parâmetro 'meses_para_processar'.
    """
    
    logger = logging.getLogger('exdrop_osr')
    cidade_nome = cidade_config.get('nome', 'pacatuba')
    
     # --- ETAPA DE INSTALAÇÃO ÚNICA DO DRIVER ---
    try:
        logger.info("Instalando/Verificando o ChromeDriver para Pacatuba...")
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver está pronto em: {driver_path}")
    except Exception as e:
        logger.critical(f"Falha ao instalar o ChromeDriver. Abortando. Erro: {e}")
        return
    # --- FIM DA INSTALAÇÃO ---
    
    for ano in anos_para_processar:
        log_context.task_id = f"Pacatuba-{ano}"
        logger.info(f"--- INICIANDO PROCESSAMENTO PARA PACATUBA - ANO DE {ano} ---")
        
        # --- DECISÃO DA ESTRATÉGIA ---
        if meses_para_processar:
            # MODO MENSAL: Paraleliza por mês
            logger.info(f"Modo de extração MENSAL selecionado para os meses: {meses_para_processar}")
            tarefas = [(ano, mes) for mes in meses_para_processar]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                func_com_args = partial(worker_processar_mes_pacatuba, cidade_config, driver_path=driver_path, headless=headless)
                futures = {executor.submit(func_com_args, tarefa) for tarefa in tarefas}
                for future in as_completed(futures):
                    future.result() # Apenas para capturar exceções
            
            # Consolida os arquivos mensais gerados
            unir_csvs_por_ano(cidade_nome=cidade_nome, ano=ano)  
        
        else:
            # --- FASE 1: COLETA DE LINKS EM LOTES (MODO ANUAL) ---
            logger.info("Modo de extração ANUAL selecionado. Iniciando coleta de links em lotes.")
            links_para_processar = []
            pagina_atual = 1
            paginas_por_lote = 50 # Define o tamanho do lote. Ajustar se necessário.

            while True:
                logger.info(f"Iniciando coleta de lote a partir da página {pagina_atual}...")
                novos_links, tem_mais_paginas = coletar_links_lote(
                    cidade_config, ano, pagina_atual, paginas_por_lote, driver_path, headless
                )
                if novos_links:
                    links_para_processar.extend(novos_links)
                    logger.info(f"{len(novos_links)} links adicionados. Total até agora: {len(links_para_processar)}.")
                
                if not tem_mais_paginas:
                    logger.info("Fim da coleta de links detectado.")
                    break
                
                pagina_atual += paginas_por_lote

            logger.info(f"Fase 1 concluída. Total de {len(links_para_processar)} links coletados para o ano de {ano}.")
            if not links_para_processar:
                continue

        # --- FASE 2: DISTRIBUIÇÃO E PROCESSAMENTO PARALELO ---
        logger.info(f"Fase 2: Iniciando extração com {max_workers} workers.")
        dados_finais = []
        
        if max_workers > len(links_para_processar): max_workers = len(links_para_processar)
        lista_de_tarefas = numpy.array_split(links_para_processar, max_workers) if max_workers > 0 else []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            func_com_args = partial(worker_extrair_detalhes_pacatuba, driver_path=driver_path, headless=headless)
            futures = {executor.submit(func_com_args, tarefa.tolist(), ano): i for i, tarefa in enumerate(lista_de_tarefas) if tarefa.size > 0}
            
            # Lógica de log de progresso
            lotes_concluidos = 0
            total_lotes = len(futures)
            
            for future in as_completed(futures):
                if resultado_parcial := future.result(): dados_finais.extend(resultado_parcial)

            lotes_concluidos =+ 1
            logger.info(f"[PROGRESSO] Lote {lotes_concluidos} de {total_lotes} concluído")
        # --- SALVAR RESULTADOS ---
        if dados_finais:
            output_dir = os.path.join("data", "processed", "pacatuba")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"pacatuba_royalties_{ano}.csv")
            
            df = pd.DataFrame(dados_finais)
            df.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
            logger.info(f"Processamento concluído. {len(df)} registros salvos em: {output_path}")
        else:
            logger.info("Nenhum registro de royalties foi extraído.")
            
        logger.info(f"--- FINALIZADO PROCESSAMENTO DE PACATUBA - ANO DE {ano} ---")