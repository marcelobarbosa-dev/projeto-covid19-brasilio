# Evolução da COVID-19 no Brasil e qualidade dos registros (2020–2022)

**Autor:** Marcelo Barbosa de Oliveira Junior · Universidade La Salle · Bacharelado em Sistemas de Informação, 6º período · Linguagem de Programação (Análise e Visualização de Dados com Python) · 2026. **Professor orientador:** Alexandre Louzada.

**Artigo:** [abrir artigo HTML](docs/index.html) · **Fonte:** [Brasil.IO — COVID-19, `caso_full`](https://brasil.io/dataset/covid19/caso_full/) · **Palavras-chave:** COVID-19; boletins estaduais; qualidade de dados; ciência aberta; FAIR.

## Resumo executivo

Análise descritiva dos boletins das Secretarias de Saúde das UFs, tratados por Álvaro Justen e colaboradores/Brasil.IO. Respondemos: (1) como variaram casos, óbitos e picos de notificação em dias com 27 UFs; (2) como variou a incidência acumulada estadual na última data disponível; (3) qual a frequência de linhas municipais repetidas e revisões negativas. A versão da base foi congelada por SHA-256 em `data/processed/manifest.json`. O artigo inclui seis gráficos em SVG, uma visualização interativa, metodologia, resultados e limitações. A fonte contém 3.853.648 observações até 27/03/2022; **não representa a situação atual da COVID-19**.

## Reproduzir

Requer Python 3.12 e aproximadamente 1 GB de espaço temporário. Na raiz:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.etl --download
python -m src.analysis
python -m notebooks.build_notebook
python -m src.render_article
```

O download (~92 MB comprimidos) é público e não necessita token. Se um bloqueio temporário impedir o download automatizado, obtenha o [CSV completo no Brasil.IO](https://data.brasil.io/dataset/covid19/caso_full.csv.gz) e salve como `data/raw/caso_full.csv.gz`; rode `python -m src.etl`. O ETL confere o SHA-256 de referência e **interrompe** se a fonte foi atualizada, para impedir misturar resultados de versões diferentes. Para analisar explicitamente uma versão nova, rode `python -m src.etl --allow-source-update` e revise todos os resultados e interpretações antes de publicar. O pipeline escreve `data/processed/*.csv*`, `manifest.json`, `analysis_summary.json`, o notebook executado e regenera `docs/index.html` e `docs/assets/*.svg`.

## Estrutura e decisões

```text
data/raw/                 original via script, fora do Git (>50 MB)
data/processed/           painéis, qualidade, picos, resumo e manifesto
data/data_dictionary.md   campos originais e derivados
src/etl.py                download, validação, agregações em blocos
src/analysis.py           estatísticas e picos de notificação auditáveis
src/render_article.py     figuras e artigo baseado nos dados processados
notebooks/build_notebook.py       gerador/executor do notebook
notebooks/analise_exploratoria.ipynb   exploração com resultados salvos
docs/index.html           artigo HTML responsivo para GitHub Pages
docs/assets/              seis gráficos vetoriais
```

O ETL valida datas, UFs e granularidade; rejeita chaves estaduais duplicadas e registra exclusões e nulos, sem apagar revisões negativas. Totais nacionais somam somente linhas estaduais, exigem 27 UFs no dia e médias de sete datas consecutivas. A análise calcula média, mediana, quartis, desvio padrão, IQR e coeficiente de variação da incidência, correlação descritiva de Spearman e picos de notificação por razão acima de Q3 + 1,5×IQR. O indicador de letalidade por casos confirmados não é probabilidade de morte após infecção. [Dicionário completo](data/data_dictionary.md).

## Publicar no GitHub Pages

O repositório está publicado em [marcelobarbosa-dev/projeto-covid19-brasilio](https://github.com/marcelobarbosa-dev/projeto-covid19-brasilio) e o artigo em [GitHub Pages](https://marcelobarbosa-dev.github.io/projeto-covid19-brasilio/). O Pages usa a branch `main` e a pasta `/docs`.

## FAIR e licenças

- **F:** README, palavras-chave, autoria, URL estável da fonte e hash da cópia analisada.
- **A:** repositório e artigo publicáveis sem autenticação; download público do original.
- **I:** CSV/CSV.gz, UTF-8, datas ISO 8601 e dicionário de dados.
- **R:** código sob MIT; dados processados e texto derivados da fonte sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), com atribuição: “Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e colaboradores/Brasil.IO”. Dependências diretas e transitivas do ambiente fixadas em `requirements.txt`.

O artigo e o código estão publicados nos endereços acima.
