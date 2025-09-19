# src/scrapers/aracaju_barra_pirambu_scraper.py

import os
import re
import sys
import time
import csv
import glob
import unicodedata
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

from src.common.logging_setup import log_context
from src.common.file_utils import unir_csvs_por_ano

# --- Constantes e Funções Auxiliares (do seu notebook) ---
TERMOS_ROYALTIES = ['royalty', 'royalties', 'petroleo', '15300000', '15400000', '17050000', '17200000', '17210000', '0120000']
RE_REMOVE_PUNCTUATION = re.compile(r'[^a-zA-Z0-9\s]')

def normalizar(texto: str) -> str:
    if not isinstance(texto, str): return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = RE_REMOVE_PUNCTUATION.sub('', texto)
    return texto.lower()

# --- Funções de Interação com Selenium ---

def start_driver_aracaju_family(headless=False, executable_path=None) -> webdriver.Chrome:
    logger = logging.getLogger('exdrop_osr')
    logger.info("Iniciando driver do Chrome para a família de portais Serigy...")
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
    else:
        options.add_argument('--window-size=1920,1080')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-dev-shm-usage")
    # Lógica para usar o caminho pré-instalado ou o WebDriverManager
    if executable_path:
        service = ChromeService(executable_path=executable_path)
    else:
        # Fallback para o método antigo, útil para testes individuais
        service = ChromeService(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_loading_to_disappear(driver, timeout=60):
    logger = logging.getLogger('exdrop_osr')
    try:
        logger.debug("Aguardando o indicador de carregamento desaparecer...")
        WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((By.ID, "loading")))
        logger.debug("Indicador de carregamento desapareceu.")
    except TimeoutException:
        logger.warning(f"Timeout: Indicador de carregamento não desapareceu em {timeout}s.")

def selecionar_ano_mes_aracaju(driver, ano, mes):
    logger = logging.getLogger('exdrop_osr')
    logger.info(f"Selecionando filtro para {mes}/{ano}")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dataTables-Pagamentos")))
    Select(WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlAnoPagamentos")))).select_by_value(ano)
    Select(WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ddlMesPagamentos")))).select_by_value(mes)
    driver.find_element(By.ID, "btnFiltrarPagamentos").click()
    wait_for_loading_to_disappear(driver)
    logger.info(f"Filtro para {mes}/{ano} aplicado.")
    

def ir_para_proxima_pagina_aracaju(driver, tentativas_maximas=3):
    """
    Tenta clicar no botão da próxima página na tabela de pagamentos com lógica de retentativas.
    Retorna True se conseguiu ir para a próxima página, False caso contrário.
    """
    logger = logging.getLogger('exdrop_osr')
    
    for tentativa in range(1, tentativas_maximas + 1):
        try:
            logger.info(f"Tentando navegar para a próxima página (Tentativa {tentativa}/{tentativas_maximas})...")
            
            proxima_pagina_li_locator = (By.ID, "dataTables-Pagamentos_next")
            
            # Espera que o elemento <li> esteja presente
            proxima_pagina_li_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(proxima_pagina_li_locator)
            )
            
            # Verifica se o botão <li> está desabilitado pela classe
            if "disabled" in proxima_pagina_li_element.get_attribute("class"):
                logger.info("Última página alcançada (botão 'Próximo' está desabilitado).")
                return False

            # Usa clique via JavaScript para maior robustez
            driver.execute_script("arguments[0].click();", proxima_pagina_li_element)
            
            # Aguarda o indicador de carregamento da página desaparecer
            wait_for_loading_to_disappear(driver)
            
            logger.info("Navegou para a próxima página com sucesso.")
            return True # Sucesso, sai da função

        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Falha na tentativa {tentativa}: {type(e).__name__}.")
            
            if tentativa < tentativas_maximas:
                tempo_espera = 5 * tentativa # Espera 5s, 10s...
                logger.info(f"Aguardando {tempo_espera} segundos antes da próxima tentativa.")
                time.sleep(tempo_espera)
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

def _processar_linha_aracaju(driver, indice_linha: int, xpath_base: str, dados_coletados_mes: list) -> bool:
    """
    Função auxiliar que processa uma ÚNICA linha da tabela de Aracaju.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    logger = logging.getLogger('exdrop_osr')
    current_row_xpath = f"({xpath_base})[{indice_linha + 1}]"
    
    try:
        # Etapa 1: Localiza a linha principal e abre os detalhes se necessário
        linha_principal = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, current_row_xpath)))
        
        if "shown" not in linha_principal.get_attribute("class"):
            btn_detalhes_locator = linha_principal.find_element(By.XPATH, "./td[1][contains(@class, 'details-control')]")
            
            btn_detalhes = WebDriverWait(linha_principal, 15).until(
                EC.element_to_be_clickable(btn_detalhes_locator)
            )
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_detalhes)
            time.sleep(0.3)
            btn_detalhes.click()
            WebDriverWait(driver, 20).until(lambda d: "shown" in d.find_element(By.XPATH, current_row_xpath).get_attribute("class"))

        # Etapa 2: Extrai os dados dos detalhes
        details_wrapper_xpath = f"{current_row_xpath}/following-sibling::tr[1]"
        linha_detalhes_container = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, details_wrapper_xpath)))
        
        dados_detalhes_preview = {}
        fonte_recurso_valor = None

        tabela_detalhes = linha_detalhes_container.find_element(By.XPATH, ".//div[@class='table-responsive']/table")
        for linha_det in tabela_detalhes.find_elements(By.XPATH, "./tbody/tr"):
            try:
                chave = linha_det.find_element(By.XPATH, "./th").text.strip().replace(":", "")
                valor = linha_det.find_element(By.XPATH, "./td").text.strip()
                chave_norm = normalizar(chave).replace(" ", "_")
                if chave_norm:
                    dados_detalhes_preview[chave_norm] = valor
                    if chave_norm == "fonte_de_recurso":
                        fonte_recurso_valor = valor
            except NoSuchElementException:
                continue

        # Etapa 3: Verifica se é de royalties
        if fonte_recurso_valor and any(termo in normalizar(fonte_recurso_valor) for termo in TERMOS_ROYALTIES):
            logger.info(f"Linha {indice_linha + 1}: Royalties detectados. Coletando dados completos.")
            linha_principal = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, current_row_xpath)))
            celulas = linha_principal.find_elements(By.XPATH, "./td")
            
            dados_linha = {
                'orgao': celulas[1].text, 'unidade': celulas[2].text, 'data': celulas[3].text,
                'empenho': celulas[4].text, 'processo': celulas[5].text, 'credor': celulas[6].text,
                'cpf_cnpj': celulas[7].text, 'pago': celulas[8].text, 'retido': celulas[9].text,
                'anulacao': celulas[10].text
            }
            dados_linha.update(dados_detalhes_preview)
            dados_coletados_mes.append(dados_linha)
        
        # Etapa 4: Fecha os detalhes (importante para não sobrecarregar a página)
        linha_principal = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, current_row_xpath)))
        if "shown" in linha_principal.get_attribute("class"):
            btn_detalhes = linha_principal.find_element(By.XPATH, "./td[1][contains(@class, 'details-control')]")
            btn_detalhes.click()
            WebDriverWait(driver, 10).until(lambda d: "shown" not in d.find_element(By.XPATH, current_row_xpath).get_attribute("class"))

        return True # Sucesso
        
    except Exception as e:
        logger.error(f"Erro ao processar a linha {indice_linha + 1}: {e}")
        return False # Falha

def extrair_dados_pagina_aracaju(driver, dados_coletados_mes: list):
    logger = logging.getLogger('exdrop_osr')
    logger.info("Executando extração da página...")

    xpath_base_linhas = "//table[@id='dataTables-Pagamentos']/tbody/tr[@role='row'][contains(@class, 'odd') or contains(@class, 'even')]"
    try:
        num_linhas = len(WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, xpath_base_linhas))))
        if num_linhas == 0:
            logger.info("Nenhuma linha de dados encontrada nesta página.")
            return
        logger.info(f"Encontradas {num_linhas} linhas para processar.")
    except TimeoutException:
        logger.info("Tabela de dados não encontrada ou vazia nesta página.")
        return

    linhas_para_retentativa = []

    # --- PRIMEIRA PASSAGEM ---
    logger.info("Iniciando primeira passagem pelas linhas da página...")
    for i in range(num_linhas):
        sucesso = _processar_linha_aracaju(driver, i, xpath_base_linhas, dados_coletados_mes)
        if not sucesso:
            linhas_para_retentativa.append(i) # Guarda o índice da linha que falhou
    
    # --- SEGUNDA PASSAGEM (APENAS NAS LINHAS QUE FALHARAM) ---
    if linhas_para_retentativa:
        logger.info(f"Iniciando segunda passagem para {len(linhas_para_retentativa)} linha(s) que falharam...")
        time.sleep(2) # Pausa estratégica antes de tentar novamente

        for i in linhas_para_retentativa:
            logger.info(f"Retentativa na linha {i+1}...")
            _processar_linha_aracaju(driver, i, xpath_base_linhas, dados_coletados_mes)



# --- Worker e Função Principal (Ponto de Entrada do Módulo) ---

def worker_processar_mes(cidade_config: dict, ano: str, mes: str, driver_path: str, headless:bool):
    cidade_nome = cidade_config['nome']
    log_context.task_id = f"{cidade_nome.capitalize()}-{ano}-{mes}"
    logger = logging.getLogger('exdrop_osr')
    logger.info("Worker iniciado.")
    
    driver = None
    try:
        driver = start_driver_aracaju_family(headless=headless, executable_path=driver_path)
        driver.get(cidade_config['url'])
        
        # Lógica de iframe (se existir no config)
        if iframe := cidade_config.get('nome_iframe'):
            WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe)))

        # Navegação inicial para a página de pagamentos
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//ul/li[4]/a"))).click()
        wait_for_loading_to_disappear(driver)
        
        selecionar_ano_mes_aracaju(driver, ano, mes)
        
        dados_do_mes = []
        pagina_atual = 1
        while True:
            logger.info(f"Extraindo dados da página {pagina_atual}...")
            extrair_dados_pagina_aracaju(driver, dados_do_mes)
            
            if not ir_para_proxima_pagina_aracaju(driver): break
            pagina_atual += 1
            
        if dados_do_mes:
            output_dir = os.path.join("data", "processed", cidade_nome)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{cidade_nome}_royalties_{ano}_{mes}.csv")
            
            df = pd.DataFrame(dados_do_mes)
            df.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
            logger.info(f"Dados salvos para {cidade_nome} - {mes}/{ano} em {output_path}")

    except Exception as e:
        logger.error(f"Erro no worker para {cidade_nome} {mes}/{ano}: {e}")
    finally:
        if driver: driver.quit()

def run(cidade_config: dict, anos_para_processar: List[str], meses_para_processar: List[str], max_workers: int, headless:bool):
    """Ponto de entrada que orquestra a extração para Aracaju, Barra ou Pirambu."""
    logger = logging.getLogger('exdrop_osr')
    cidade_nome = cidade_config['nome']
    
    # --- ETAPA DE INSTALAÇÃO ÚNICA DO DRIVER ---
    try:
        logger.info("Instalando/Verificando o ChromeDriver antes de iniciar os workers...")
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver está pronto em: {driver_path}")
    except Exception as e:
        logger.critical(f"Falha ao instalar o ChromeDriver. Abortando. Erro: {e}")
        return
    # --- FIM DA INSTALAÇÃO ---
    
    for ano in anos_para_processar:
        log_context.task_id = f"{cidade_nome.capitalize()}-{ano}"
        logger.info(f"--- INICIANDO PROCESSAMENTO PARA {cidade_nome.upper()} - ANO DE {ano} ---")
        
        # Lógica de seleção de meses
        if meses_para_processar:
            logger.info(f"Executando para meses específicos: {meses_para_processar}")
            meses=meses_para_processar
        else:
            meses = [f"{m:02d}" for m in range(1, 13)]
            
        tarefas = [(ano, mes) for mes in meses]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Passa a configuração da cidade para cada worker
            func_com_args = partial(
                worker_processar_mes,
                cidade_config,
                driver_path=driver_path,
                headless=headless
            )
            futures = [executor.submit(func_com_args, *tarefa) for tarefa in tarefas] # * crucial para desempacotar atupla (ano, mes)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Uma tarefa para {cidade_nome} falhou: {e}")
        
        # --- CONSOLIDAÇÃO APÓS PROCESSAR TODOS OS MESES ---
        logger.info(f"Processamento de todos os meses de {ano} para {cidade_nome} concluído. Iniciando consolidação...")
        try:
            unir_csvs_por_ano(cidade_nome=cidade_nome, ano=ano)
        except Exception as e:
            logger.error(f"Falha ao consolidar arquivos para {cidade_nome} - {ano}: {e}")
        

        logger.info(f"--- FINALIZADO PROCESSAMENTO DE {cidade_nome.upper()} - ANO DE {ano} ---")