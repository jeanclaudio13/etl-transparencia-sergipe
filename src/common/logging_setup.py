# src/common/logging_steup

import os
import logging
import threading

# Objeto de armazenamento de dados que é local (privado) para cada thread
log_context = threading.local()

class TaskIdFilter(logging.Filter):
    """Filtro para adicionar um ID de tarefa/thread aos registros de log."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.task_id = getattr(log_context, 'task_id', 'MainThread')
        return True

def setup_logging(log_file: str) -> logging.Logger:
    """Configura o logger principal da aplicação."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    log_format = "[%(task_id)s] - %(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s"

    logger = logging.getLogger('exdrop_osr') # Nome do projeto
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(log_format)
    task_filter = TaskIdFilter()

    # Handler para o arquivo de log
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.addFilter(task_filter)

    # Handler para o console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(task_filter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Reduz o ruído de bibliotecas externas
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('WDM').setLevel(logging.WARNING)

    return logger