# Evolução da COVID-19 no Brasil e qualidade dos registros (2020–2022)

**Autor:** Marcelo Barbosa de Oliveira Junior · Universidade La Salle · Bacharelado em Sistemas de Informação, 6º período · Linguagem de Programação (Análise e Visualização de Dados com Python) · 2026. **Professor orientador:** nome a confirmar.

**Artigo:** [abrir artigo HTML](docs/index.html) · **Fonte:** [Brasil.IO — COVID-19, `caso_full`](https://brasil.io/dataset/covid19/caso_full/) · **Palavras-chave:** COVID-19; boletins estaduais; qualidade de dados; ciência aberta; FAIR.

## Resumo executivo

Análise descritiva dos boletins das Secretarias de Saúde das UFs, tratados por Álvaro Justen e colaboradores/Brasil.IO. Respondemos: (1) como variaram os casos e óbitos comunicados em dias com 27 UFs; (2) como variou a incidência acumulada estadual na última data disponível; (3) qual a frequência de linhas municipais repetidas e revisões negativas. A versão da base foi congelada por SHA-256 em `data/processed/manifest.json`. O artigo inclui quatro gráficos em SVG, metodologia, resultados e limitações. A fonte contém 3.853.648 observações até 27/03/2022; **não representa a situação atual da COVID-19**.

## Reproduzir

Requer Python 3.11+ e aproximadamente 1 GB de espaço temporário. Na raiz:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.etl --download
python -m src.render_article
```

O download (~92 MB comprimidos) é público e não necessita token. Se um bloqueio temporário impedir o download automatizado, obtenha o [CSV completo no Brasil.IO](https://data.brasil.io/dataset/covid19/caso_full.csv.gz) e salve como `data/raw/caso_full.csv.gz`; rode `python -m src.etl`. Para reproduzir **exatamente** os resultados fornecidos, use um bruto cujo SHA-256 corresponda a `data/processed/manifest.json`; um download posterior pode ter outra versão. Rodar o pipeline escreve `data/processed/*.csv*`, `manifest.json` e regenera `docs/index.html` e `docs/assets/*.svg`.

## Estrutura e decisões

```text
data/raw/                 original via script, fora do Git (>50 MB)
data/processed/           painéis agregados, qualidade e manifesto de origem
data/data_dictionary.md   campos originais e derivados
src/etl.py                download, validação, agregações em blocos
src/render_article.py     figuras e artigo baseado nos dados processados
notebooks/analise_exploratoria.ipynb   exploração reexecutável
docs/index.html           artigo HTML responsivo para GitHub Pages
docs/assets/              quatro gráficos vetoriais
```

O ETL valida datas, UFs e granularidade; rejeita chaves estaduais duplicadas e registra exclusões, sem apagar revisões negativas. Totais nacionais somam somente linhas estaduais, exigem 27 UFs no dia e médias de sete datas consecutivas. O indicador de letalidade por casos confirmados não é probabilidade de morte após infecção. [Dicionário completo](data/data_dictionary.md).

## Publicar no GitHub Pages

Crie um repositório público chamado `projeto-covid19-brasilio` na conta `marcelobarbosa-dev`, envie o conteúdo desta pasta e em **Settings → Pages → Build and deployment** selecione **Deploy from a branch**, a branch principal e **/docs**. Preencha o nome do professor em `src/render_article.py` e regenere o artigo. URL esperada: `https://marcelobarbosa-dev.github.io/projeto-covid19-brasilio/`. O deploy depende do envio à conta e da ativação do GitHub Pages.

## FAIR e licenças

- **F:** README, palavras-chave, autoria, URL estável da fonte e hash da cópia analisada.
- **A:** repositório e artigo publicáveis sem autenticação; download público do original.
- **I:** CSV/CSV.gz, UTF-8, datas ISO 8601 e dicionário de dados.
- **R:** código sob MIT; dados processados e texto derivados da fonte sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), com atribuição: “Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e colaboradores/Brasil.IO”. Dependências diretas fixadas em `requirements.txt`.

O repositório local está pronto para publicação, mas ainda não possui URL pública nem o nome do professor confirmado.
