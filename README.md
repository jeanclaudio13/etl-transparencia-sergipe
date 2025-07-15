# Extrator de Dados de  do Petróleo - Portais da Transparência (Sergipe)

## 📖 Sobre o Projeto

Este projeto contém um conjunto de robôs (scrapers) desenvolvidos em Python para automatizar a extração de dados de pagamentos de royalties dos portais da transparência de municípios de Sergipe.

A arquitetura foi projetada para ser modular, escalável e de fácil manutenção, permitindo que novos scrapers para diferentes prefeituras sejam adicionados com o mínimo de esforço. A execução é feita em paralelo para otimizar o tempo de extração.

## ✨ Funcionalidades Principais


* **Arquitetura Modular:** Cada tipo de portal (ex: Serigy, Ágape) possui seu próprio módulo de scraper, facilitando a manutenção e expansão.
* **Execução Paralela:** Utiliza múltiplas threads para processar diferentes tarefas (meses ou anos) simultaneamente, acelerando drasticamente o tempo total da extração.
* **Logging Detalhado:** Gera logs de execução consolidados e identificados por tarefa, facilitando a depuração e o monitoramento.
* 🔶 **(Em Desenvolvimento...) Extração Parametrizada:** Controle quais cidades e anos devem ser processados através de um único arquivo de configuração (`config.json`).
* 🔶 **(Em Desenvolvimento...) Ambiente Containerizado:** Empacotado com Docker para garantir um ambiente de execução consistente e eliminar a necessidade de instalações manuais na máquina do cliente.

## 📂 Estrutura do Projeto
**🔶(Em Desenvolvimento...)** 

O projeto está organizado da seguinte forma para garantir a separação de responsabilidades:

```
etl-transparencia-sergipe/
│
├── config.json                 # Arquivo para configurar a execução
├── Dockerfile                  # "Receita" para construir o container Docker
├── main.py                     # Ponto de entrada principal do projeto
├── README.md                   # Este arquivo
├── requirements.txt            # Lista de bibliotecas Python
│
├── data/
│   └── processed/              # Pasta para os arquivos CSV finais
│       ├── aracaju/
│       └── pacatuba/
│
├── logs/                       # Pasta para os arquivos de log
│
└── src/                        # Pasta principal para todo o código-fonte
    ├── common/
    │   └── logging_setup.py
    └── scrapers/
        ├── aracaju_barra_pirambu_scraper.py
        └── pacatuba_scraper.py
```

## 🚀 Como Executar

Existem duas maneiras de executar o projeto: usando Docker (recomendado para clientes e produção) ou localmente (para desenvolvimento).

### Pré-requisitos

* **Para execução com Docker:** É necessário apenas ter o [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução.
* **Para desenvolvimento local:** Python 3.10+ e `pip`.

### Modo 1: Execução via Docker (Recomendado)

1.  **Construir a Imagem (feito apenas uma vez):**
    No terminal, na pasta raiz do projeto, execute:
    ```bash
    docker build -t extrator-sergipe .
    ```

2.  **Executar o Container:**
    Este comando inicia a extração com base nas configurações do `config.json`.
    ```bash
    # Para Windows (CMD ou PowerShell)
    docker run --rm -v "%cd%/data:/app/data" -v "%cd%/logs:/app/logs" extrator-sergipe

    # Para macOS ou Linux
    docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" extrator-sergipe
    ```
    * Os arquivos CSV gerados aparecerão na pasta `data/processed` e os logs na pasta `logs`.

### Modo 2: Execução Local (Para Desenvolvimento)

1.  **Crie um Ambiente Virtual:**
    ```bash
    python -m venv venv
    ```

2.  **Ative o Ambiente Virtual:**
    ```bash
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o Script:**
    ```bash
    python main.py
    ```

## ⚙️ Configuração

Para controlar o que será extraído, edite o arquivo `config.json` antes de executar:

```json
{
  "anos_para_processar": ["2024", "2023"],
  "prefeituras_para_processar": [
    "aracaju",
    "barra",
    "pirambu",
    "pacatuba"
  ],
  "configuracoes_paralelismo": {
    "max_workers": 4
  },
  "configuracoes_cidades": {
    "aracaju": {
      "scraper_module": "aracaju_barra_pirambu_scraper",
      "url": "https://www.municipioonline.com.br/se/prefeitura/aracaju/cidadao/despesa",
      "nome_iframe": null
    },
    "barra": {
      "scraper_module": "aracaju_barra_pirambu_scraper",
      "url": "https://www.municipioonline.com.br/se/prefeitura/barradoscoqueiros/cidadao/despesa",
      "nome_iframe": null
    },
    "pirambu": {
      "scraper_module": "aracaju_barra_pirambu_scraper",
      "url": "https://www.municipioonline.com.br/se/prefeitura/pirambu/cidadao/despesa",
      "nome_iframe": null
    },
    "pacatuba": {
      "scraper_module": "pacatuba_scraper",
      "url": "https://transparencia.pacatuba.se.gov.br/public/portal/despesas"
    }
  }
}
```
* **`anos_para_processar`**: Lista de anos para os quais o robô irá rodar.
* **`prefeituras_para_processar`**: Lista de cidades que serão processadas. O nome deve corresponder a uma chave em `configuracoes_cidades`.
* **`max_workers`**: Número de tarefas paralelas (navegadores) a serem executadas ao mesmo tempo.

---
