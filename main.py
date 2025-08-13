# Em: main.py


import json
import logging
import argparse

from src.common.logging_setup import setup_logging
# Importa os módulos scraper com seus novos nomes
from src.scrapers import aracaju_barra_pirambu_scraper, pacatuba_scraper

# Mapeia o nome do scraper (do config.json) para o módulo Python importado
SCRAPER_MODULES = {
    "aracaju_barra_pirambu_scraper": aracaju_barra_pirambu_scraper,
    "pacatuba_scraper": pacatuba_scraper
}

def main():
    """Lê a configuração e dispara os scrapers corretos para cada cidade."""
    
    # COnfigura o parser de argumentos
    parser = argparse.ArgumentParser(description="Extrator de Dados de Royalties.")
    parser.add_argument(
        '--visual', 
        action='store_true',  # Transforma o argumento em um booleano (True se presente)
        help="Executa os navegadores em modo visual (não-headless) para depuração."
    )
    args = parser.parse_args()
    
    # Define o modo headless com base no argumento (True por padrão, False se --visual for passado)
    headless_mode = not args.visual 
    
    # Usa o novo nome do logger
    logger = setup_logging(log_file="logs/main_execution.log")
    logger.info("Iniciando processo de extração unificado.")

   
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    anos = config["anos_para_processar"]
    cidades = config["prefeituras_para_processar"]
    max_workers = config["configuracoes_paralelismo"]["max_workers"]
    for cidade_nome in cidades:
        if cidade_nome in config["configuracoes_cidades"]:
            cidade_config = config["configuracoes_cidades"][cidade_nome]
            scraper_module_name = cidade_config["scraper_module"]
            
            if scraper_module_name in SCRAPER_MODULES:
                scraper_module = SCRAPER_MODULES[scraper_module_name]
                cidade_config['nome'] = cidade_nome
                
                scraper_module.run(
                    cidade_config=cidade_config,
                    anos_para_processar=anos,
                    max_workers=max_workers,
                    headless=headless_mode)
            else:
                logger.error(f"Módulo scraper '{scraper_module_name}' não encontrado.")
        else:
            logger.warning(f"Configuração para a cidade '{cidade_nome}' não encontrada.")

if __name__ == "__main__":
    main()