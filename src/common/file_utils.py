# Em: src/common/file_utils.py

import os
import glob
import logging
import pandas as pd
import csv # Importe o csv caso queira usar a Solução 2 no futuro

def unir_csvs_por_ano(cidade_nome: str, ano: str):
    """
    Busca todos os arquivos CSV mensais de uma cidade e ano específicos,
    os une e salva um arquivo consolidado, detectando o separador automaticamente.
    """
    logger = logging.getLogger('exdrop_osr')
    
    caminho_da_pasta = os.path.join("data", "processed", cidade_nome)
    
    if not os.path.isdir(caminho_da_pasta):
        logger.error(f"Consolidação: A pasta de dados para '{cidade_nome}' não foi encontrada.")
        return

    padrao_busca = os.path.join(caminho_da_pasta, f"{cidade_nome}_royalties_{ano}_??.csv")
    lista_de_arquivos = sorted(glob.glob(padrao_busca))

    if not lista_de_arquivos:
        logger.warning(f"Consolidação: Nenhum arquivo mensal encontrado para {cidade_nome} no ano de {ano}.")
        return
    
    logger.info(f"Consolidando {len(lista_de_arquivos)} arquivo(s) para {cidade_nome} - {ano}.")

    lista_de_dataframes = []
    for arquivo in lista_de_arquivos:
        try:
            # --- MUDANÇA PRINCIPAL AQUI ---
            # Pandas irá detectar automaticamente se o separador é ',' ou ';'
            df_mensal = pd.read_csv(
                arquivo, 
                sep=None, 
                engine='python', 
                encoding='utf-8-sig',
                on_bad_lines='warn' # Adiciona um aviso para linhas malformadas
            )
            lista_de_dataframes.append(df_mensal)
        except Exception as e:
            logger.error(f"Erro ao ler o arquivo '{os.path.basename(arquivo)}': {e}")

    if not lista_de_dataframes:
        logger.error("Nenhum arquivo mensal pôde ser lido com sucesso. Consolidação abortada.")
        return

    df_consolidado = pd.concat(lista_de_dataframes, ignore_index=True)

    nome_arquivo_saida = f"{cidade_nome}_royalties_{ano}_consolidado.csv"
    caminho_saida = os.path.join(caminho_da_pasta, nome_arquivo_saida)
    
    # Salva o arquivo consolidado sempre com ';' para padronização
    df_consolidado.to_csv(caminho_saida, index=False, sep=';', encoding='utf-8-sig')

    logger.info(f"✅ Arquivo consolidado salvo com sucesso em: {caminho_saida}")