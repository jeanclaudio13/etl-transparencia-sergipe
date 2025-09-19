# ExDRoP - Extrator de Dados de Royalties do Petróleo

## 📜 Sobre o Projeto

O **ExDRoP** é uma ferramenta de automação projetada para extrair, de forma robusta e paralela, dados de pagamentos de royalties de múltiplos portais da transparência de municípios em Sergipe. O projeto nasceu da necessidade de contornar a falta de padronização e a dificuldade de acesso a esses dados públicos, fornecendo um conjunto de dados limpo e consolidado para análise e controle social.

O sistema conta com uma interface gráfica amigável para configuração e execução, além de um modo de automação para uso em servidores.

## ✨ Funcionalidades

* **Extração Multi-portal:** Suporte para diferentes layouts de portais (família Serigy e outros).
* **Processamento Paralelo:** Utiliza múltiplos "workers" (threads) para acelerar drasticamente a extração de dados.
* **Robusto e Resiliente:** Possui lógicas de retentativas para lidar com instabilidades dos portais, coleta em lotes para evitar travamentos e salvamento de diagnóstico em caso de falhas.
* **Interface Gráfica:** Um painel de controle construído com Streamlit permite a configuração e o acompanhamento da extração em tempo real, de forma totalmente visual.
* **Containerizado com Docker:** Tanto o scraper quanto a interface podem ser executados via Docker, garantindo um ambiente consistente e facilitando a distribuição.
* **Configuração Flexível:** Todas as execuções são controladas por um arquivo `config.json`, permitindo selecionar cidades, anos e meses específicos.

## 🛠️ Pré-requisitos

Para executar o projeto, você precisará de:

* **Python 3.11+**
* **Docker Desktop** (para a execução via containers, que é a forma mais recomendada)

## 🚀 Como Executar o ExDRoP

Este projeto oferece múltiplas formas de execução, projetadas para diferentes tipos de usuários, desde pesquisadores que desejam uma interface amigável até desenvolvedores que precisam de automação em servidor.

### Modo 1: Usando a Interface Gráfica (Recomendado para Usuários)

Esta é a forma mais fácil de usar o extrator. Ela abre um painel de controle no seu navegador onde você pode configurar e iniciar a extração.

#### Opção A (Mais Simples): Via Docker
Você só precisa do Docker Desktop instalado no seu computador.

1.  **Construa a imagem da UI (apenas na primeira vez):**
    ```bash
    # O -f aponta para o Dockerfile da interface
    docker build -t extrator-ui -f Dockerfile.ui .
    ```

2.  **Execute o container da UI:**
    ```powershell
    # Comando para Windows (PowerShell)
    docker run --rm -p 8501:8501 -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" -v "$(pwd)/config.json:/app/config.json" extrator-ui
    ```

3.  **Acesse a Interface:**
    Abra seu navegador e acesse: **`http://localhost:8501`**

#### Opção B (Para Desenvolvimento): Localmente com `venv`
Este método é ideal para quem está a modificar o código da interface.

1.  **Ative o ambiente virtual:**
    ```powershell
    # Para Windows (PowerShell)
    .\venv\Scripts\Activate
    ```
2.  **Instale as dependências (se necessário):**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Execute o Streamlit:**
    ```bash
    python -m streamlit run interface.py
    ```

### Modo 2: Execução Automatizada do Scraper (Recomendado para Servidores)

Este modo executa o robô em "headless" (sem interface gráfica), lendo a configuração do `config.json`. É ideal para ser agendado (`cron`) em um servidor.

1.  **Construa a imagem do scraper (apenas na primeira vez):**
    ```bash
    # O -f aponta para o Dockerfile do scraper
    docker build -t extrator-sergipe -f Dockerfile.scraper .
    ```

2.  **Execute o container do scraper:**
    ```powershell
    # Comando para Windows (PowerShell)
    docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" -v "$(pwd)/config.json:/app/config.json" extrator-sergipe
    ```

    ## 📂 Estrutura do Projeto
```
.
├── data/
│   ├── processed/      # Onde os arquivos CSV finais são salvos
│   └── raw/            # (Opcional) Para dados brutos, se necessário
├── logs/               # Arquivos de log detalhados da execução
├── src/
│   ├── common/         # Módulos compartilhados (ex: logger)
│   └── scrapers/       # Cada scraper em seu próprio arquivo .py
├── .gitignore
├── config.json         # Arquivo principal de configuração
├── Dockerfile.scraper  # Dockerfile para o robô de automação
├── Dockerfile.ui       # Dockerfile para a interface gráfica
├── interface.py        # Código da interface com Streamlit
├── main.py             # Ponto de entrada principal do robô
└── requirements.txt    # Lista de dependências Python
```

## ⚙️ Configuração

A configuração da extração é feita de forma simples e visual através da **Interface Gráfica**, não sendo necessário editar arquivos manualmente para o uso comum.

### Configurando pela Interface Gráfica

Ao executar a interface (`Modo 1` da seção "Como Executar"), você encontrará as seguintes opções no painel de controle:

* **Prefeituras para Processar:** Uma caixa de seleção múltipla para escolher quais municípios serão incluídos na extração.
* **Anos para Processar:** Um campo de texto onde você pode listar os anos desejados, separados por vírgula.
* **Meses para Processar (Condicional):** Um campo de texto que aparece se você selecionar um município compatível (todos os atuais). Permite especificar meses (ex: `01, 02, 11`), otimizando a extração. Se deixado em branco, o robô processará o ano inteiro.
* **Número de Processos Paralelos (Workers):** Um slider para definir quantos navegadores rodarão simultaneamente. Uma ajuda (`?`) explica como escolher o melhor número com base na capacidade do seu computador.
* **Executar em modo visual:** Uma caixa de seleção que permite assistir à execução do robô. Ideal para depuração.

Ao clicar em "Salvar Configurações e Iniciar Extração", suas escolhas são salvas automaticamente no arquivo `config.json` e a execução começa.

### Para Desenvolvedores ou Automação (Editando o `config.json`)

Para execuções automatizadas em servidor (`Modo 2`), a configuração é lida diretamente do arquivo `config.json`. Você pode editá-lo manualmente para controlar o processo.

```json
{
  "anos_para_processar": ["2024", "2023"],
  "prefeituras_para_processar": ["aracaju", "pacatuba"],
  "meses_para_processar": ["01", "02", "03"],
  "configuracoes_paralelismo": {
    "max_workers": 4
  },
  "configuracoes_cidades": {
    "aracaju": {
      "scraper_module": "aracaju_barra_pirambu_scraper",
      "url": "[https://www.municipioonline.com.br/se/prefeitura/aracaju/cidadao/despesa](https://www.municipioonline.com.br/se/prefeitura/aracaju/cidadao/despesa)"
    },
    "barra": {
      "scraper_module": "aracaju_barra_pirambu_scraper",
      "url": "[https://www.municipioonline.com.br/se/prefeitura/barradoscoqueiros/cidadao/despesa](https://www.municipioonline.com.br/se/prefeitura/barradoscoqueiros/cidadao/despesa)"
    },
    "pirambu": {
      "scraper_module": "aracaju_barra_pirambu_scraper",
      "url": "[https://www.municipioonline.com.br/se/prefeitura/pirambu/cidadao/despesa](https://www.municipioonline.com.br/se/prefeitura/pirambu/cidadao/despesa)"
    },
    "pacatuba": {
      "scraper_module": "pacatuba_scraper",
      "url": "[https://transparencia.pacatuba.se.gov.br/public/portal/despesas](https://transparencia.pacatuba.se.gov.br/public/portal/despesas)"
    }
  }
}
```

* anos_para_processar: Lista de anos para os quais o robô irá rodar.

* prefeituras_para_processar: Lista das chaves das cidades que serão processadas.

* meses_para_processar (Opcional): Se presente, o robô processará apenas os meses listados para as cidades compatíveis. Se ausente ou null, processará o ano inteiro.

* max_workers: Número de tarefas paralelas (navegadores) a serem executadas ao mesmo tempo.

* configuracoes_cidades: Dicionário com as configurações específicas de cada portal, como a URL e o módulo scraper a ser utilizado.


## 📦 Manutenção e Atualização das Imagens

Para garantir que a aplicação continue segura e estável, é recomendado reconstruir as imagens Docker periodicamente (a cada 1-2 meses) para incorporar as últimas atualizações de segurança da imagem base e das dependências.

O processo consiste em dois passos:

### 1. Atualizar a Imagem Base

Primeiro, garanta que você tenha a versão mais recente da imagem oficial do Python que usamos como base:

```bash
docker pull python:3.11-slim
```

### 2. Reconstruir as Imagens da Aplicação sem Cache
Em seguida, reconstrua as suas imagens `extrator-ui` e extrator-sergipe usando a flag --no-cache. Isso força o Docker a executar todos os passos do zero, incluindo o apt-get upgrade, garantindo que as últimas atualizações sejam aplicadas.

Para a imagem da Interface:

```bash

docker build --no-cache -t `extrator-ui` -f Dockerfile.ui .
```

Para a imagem do Scraper (automação):

```bash

docker build --no-cache -t extrator-sergipe -f Dockerfile.scraper .
```

