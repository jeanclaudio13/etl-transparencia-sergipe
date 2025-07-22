# Em: main.py

import json
import logging
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
    
    # Usa o novo nome do logger
    logger = setup_logging(log_file="logs/main_execution.log")
    logger.info("Iniciando processo de extração unificado.")

    # ... O resto da função main permanece exatamente o mesmo ...
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
                scraper_module.run(cidade_config, anos, max_workers)
            else:
                logger.error(f"Módulo scraper '{scraper_module_name}' não encontrado.")
        else:
            logger.warning(f"Configuração para a cidade '{cidade_nome}' não encontrada.")

if __name__ == "__main__":
    main()