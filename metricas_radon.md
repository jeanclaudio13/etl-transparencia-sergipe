# Métricas de Complexidade de Softrware

## CC (Complexidade Ciclomática)
- -s: show
- -a: average
- (A = excelente, F = muito ruim)


(venv) C:\Users\user\Desktop\etl-transparencia-sergipe>radon cc src/ -s -a
src\common\file_utils.py
    F 9:0 unir_csvs_por_ano - B (6)
src\common\logging_setup.py
    F 16:0 setup_logging - A (2)
    C 10:0 TaskIdFilter - A (2)
    M 12:4 TaskIdFilter.filter - A (1)
src\scrapers\aracaju_barra_pirambu_scraper.py
    F 107:0 extrair_dados_pagina_aracaju - D (27)
    F 318:0 run - B (9)
    F 274:0 worker_processar_mes - B (7)
    F 47:0 start_driver_aracaju_family - A (3)
    F 89:0 ir_para_proxima_pagina_aracaju - A (3)
    F 39:0 normalizar - A (2)
    F 70:0 wait_for_loading_to_disappear - A (2)
    F 79:0 selecionar_ano_mes_aracaju - A (1)
src\scrapers\pacatuba_scraper.py
    F 195:0 run - C (17)
    F 122:0 worker_extrair_detalhes_pacatuba - C (11)
    F 45:0 start_driver_pacatuba - A (3)
    F 86:0 ir_para_proxima_pagina_pacatuba - A (3)
    F 33:0 normalizar - A (2)
    F 70:0 selecionar_dropdown_pacatuba - A (2)

18 blocks (classes, functions, methods) analyzed.
Average complexity: B (5.722222222222222)

-------------------------------------------------------------------------------------------------------------------

## Índice de Manutenabilidade

Como Interpretar: O resultado é uma pontuação de 0 a 100, convertida em uma "nota":

- A (100-20): Código de fácil manutenção.

- B (19-10): Manutenção moderada.

- C (9-0): Manutenção difícil.


(venv) C:\Users\user\Desktop\etl-transparencia-sergipe>radon mi src/ -s
src\__init__.py - A (100.00)
src\common\file_utils.py - A (84.06)
src\common\logging_setup.py - A (100.00)
src\common\__init__.py - A (100.00)
src\scrapers\aracaju_barra_pirambu_scraper.py - A (45.94)
src\scrapers\pacatuba_scraper.py - A (50.52)
src\scrapers\__init__.py - A (100.00)


-------------------------------------------------------------------------------------------------------------------

## Métricas Brutas (Raw)

- LOC (Lines of Code): Total de linhas no arquivo.

- LLOC (Logical Lines of Code): Linhas que efetivamente contêm código Python (excluindo comentários e linhas em branco).

- SLOC (Source Lines of Code): Total de linhas do código-fonte (geralmente o mesmo que LOC).

- Comments: Número de linhas de comentário.

- Multi: Número de linhas que são parte de strings multi-linha.

- Blank: Número de linhas em branco.

(venv) C:\Users\user\Desktop\etl-transparencia-sergipe>radon raw src/
src\__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
src\common\file_utils.py
    LOC: 59
    LLOC: 33
    SLOC: 38
    Comments: 6
    Single comments: 4
    Multi: 4
    Blank: 13
    - Comment Stats
        (C % L): 10%
        (C % S): 16%
        (C + M % L): 17%
src\common\logging_setup.py
    LOC: 49
    LLOC: 31
    SLOC: 29
    Comments: 6
    Single comments: 7
    Multi: 0
    Blank: 13
    - Comment Stats
        (C % L): 12%
        (C % S): 21%
        (C + M % L): 12%
src\common\__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
src\scrapers\aracaju_barra_pirambu_scraper.py
    LOC: 359
    LLOC: 260
    SLOC: 262
    Comments: 40
    Single comments: 32
    Multi: 0
    Blank: 65
    - Comment Stats
        (C % L): 11%
        (C % S): 15%
        (C + M % L): 11%
src\scrapers\pacatuba_scraper.py
    LOC: 289
    LLOC: 195
    SLOC: 205
    Comments: 26
    Single comments: 26
    Multi: 3
    Blank: 55
    - Comment Stats
        (C % L): 9%
        (C % S): 13%
        (C + M % L): 10%
src\scrapers\__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%

-------------------------------------------------------------------------------------------------------------------

## Métricas de Halstead

- Esta é uma análise mais acadêmica que mede a complexidade com base nos "operadores" (como +, =, if) e "operandos" (variáveis, números) do seu código.

- É menos utilizado no dia a dia, mas pode ser interessante para uma análise mais profunda do código, medindo volume, dificuldade e o esforço estimado para entender um bloco de código.

(venv) PS C:\Users\user\Desktop\etl-transparencia-sergipe> radon hal src/   
src\__init__.py:
    h1: 0
    h2: 0
    N1: 0
    N2: 0
    vocabulary: 0
    length: 0
    calculated_length: 0
    volume: 0
    difficulty: 0
    effort: 0
    time: 0.0
    bugs: 0.0
src\common\file_utils.py:
    h1: 1
    h2: 3
    N1: 3
    N2: 3
    vocabulary: 4
    length: 6
    calculated_length: 4.754887502163469
    volume: 12.0
    difficulty: 0.5
    effort: 6.0
    time: 0.3333333333333333
    bugs: 0.004
src\common\logging_setup.py:
    h1: 0
    h2: 0
    N1: 0
    N2: 0
    vocabulary: 0
    length: 0
    calculated_length: 0
    volume: 0
    difficulty: 0
    effort: 0
    time: 0.0
    bugs: 0.0
src\common\__init__.py:
    h1: 0
    h2: 0
    N1: 0
    N2: 0
    vocabulary: 0
    length: 0
    calculated_length: 0
    volume: 0
    difficulty: 0
    effort: 0
    time: 0.0
    bugs: 0.0
src\scrapers\aracaju_barra_pirambu_scraper.py:
    h1: 7
    h2: 24
    N1: 15
    N2: 27
    vocabulary: 31
    length: 42
    calculated_length: 129.690584471711
    volume: 208.0762450362488
    difficulty: 3.9375
    effort: 819.3002148302296
    time: 45.51667860167942
    bugs: 0.06935874834541626
src\scrapers\pacatuba_scraper.py:
    h1: 7
    h2: 20
    N1: 13
    N2: 23
    vocabulary: 27
    length: 36
    calculated_length: 106.09004635215048
    volume: 171.1759500778849
    difficulty: 4.025
    effort: 688.9831990634867
    time: 38.27684439241593
    bugs: 0.05705865002596163
src\scrapers\__init__.py:
    h1: 0
    h2: 0
    N1: 0
    N2: 0
    vocabulary: 0
    length: 0
    calculated_length: 0
    volume: 0
    difficulty: 0
    effort: 0
    time: 0.0
    bugs: 0.0