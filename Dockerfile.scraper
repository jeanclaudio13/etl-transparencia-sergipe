# Em: Dockerfile

# --- Estágio 1: Imagem Base ---
# Começamos com uma imagem oficial do Python. A versão "slim" é mais leve.
FROM python:3.11-slim

# --- Estágio 2: Configuração do Ambiente ---
# Define o diretório de trabalho padrão dentro do container.
# Todos os comandos a seguir serão executados a partir daqui.
WORKDIR /app

# --- Estágio 3: Instalação do Google Chrome ---
# Para o Selenium funcionar, precisamos de um navegador instalado DENTRO do container.
# Estes comandos instalam o Chrome em um ambiente Debian/Linux.
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    wget \
    gnupg \
    --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# --- Estágio 4: Instalação das Dependências Python ---
# Copia apenas o arquivo de requisitos primeiro, para aproveitar o cache do Docker.
COPY requirements.txt .

# Instala todas as bibliotecas listadas no requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# --- Estágio 5: Copia o Código do Projeto ---
# Copia todo o resto do seu projeto (a pasta 'src', 'main.py', etc.) para o diretório /app dentro do container.
COPY . .

# --- Estágio 6: Comando de Execução ---
# Define o comando que será executado quando o container iniciar.
# Ele simplesmente executa nosso script principal.
CMD ["python", "main.py"]

#Para rodar no Terminal Powershell
# docker build -t extrator-sergipe .
# docker run --rm -v "$(pwd)\data:/app/data" -v "$(pwd)\logs:/app/logs" extrator-sergipe