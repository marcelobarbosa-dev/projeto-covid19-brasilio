"""Produz figuras SVG e artigo HTML a partir dos CSVs gerados pelo ETL."""
from __future__ import annotations

import html
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .etl import OUT, ROOT

DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"


def fmt(n, digits=0):
    s = f"{n:,.{digits}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def run():
    ASSETS.mkdir(parents=True, exist_ok=True)
    meta = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    daily = pd.read_csv(OUT / "national_daily.csv.gz", parse_dates=["date"])
    latest = pd.read_csv(OUT / "state_latest.csv", parse_dates=["date"])
    quality = pd.read_csv(OUT / "quality_by_state.csv")
    end = daily.date.max().date()
    peak_cases = daily.loc[daily.cases_7d.idxmax()]
    peak_deaths = daily.loc[daily.deaths_7d.idxmax()]
    highest = latest.loc[latest.incidence_100k.idxmax()]
    lowest = latest.loc[latest.incidence_100k.idxmin()]
    latest = latest.sort_values("incidence_100k")
    repeats = int(quality.repeated.sum())
    rows = int(quality.city_rows.sum())
    corrections = int(quality.negative_cases.sum() + quality.negative_deaths.sum())
    top_repeat = quality.loc[quality.repeated_pct.idxmax()]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.bbox": "tight"})
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.plot(daily.date, daily.cases_7d, color="#1e3a8a", linewidth=1.8)
    ax.axvline(peak_cases.date, color="#e67e22", alpha=.7, linestyle="--")
    ax.set(title="Casos comunicados por dia: média móvel de 7 dias", ylabel="Casos/dia", xlabel="Data")
    ax.grid(axis="y", alpha=.2)
    fig.autofmt_xdate(); fig.savefig(ASSETS / "casos.svg"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.plot(daily.date, daily.deaths_7d, color="#ac3b41", linewidth=1.8)
    ax.axvline(peak_deaths.date, color="#e67e22", alpha=.7, linestyle="--")
    ax.set(title="Óbitos comunicados por dia: média móvel de 7 dias", ylabel="Óbitos/dia", xlabel="Data")
    ax.grid(axis="y", alpha=.2)
    fig.autofmt_xdate(); fig.savefig(ASSETS / "obitos.svg"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.barh(latest.state, latest.incidence_100k, color="#3974aa")
    ax.set(title="Incidência acumulada por UF no último registro disponível", xlabel="Casos confirmados / 100 mil habitantes")
    ax.grid(axis="x", alpha=.2)
    fig.savefig(ASSETS / "incidencia.svg"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    q = quality.sort_values("repeated_pct")
    ax.bar(q.state, q.repeated_pct, color="#ad7342")
    ax.set(title="Proporção de linhas municipais repetidas, por UF", ylabel="% dos registros município-dia", xlabel="UF")
    ax.grid(axis="y", alpha=.2)
    fig.savefig(ASSETS / "repeticoes.svg"); plt.close(fig)

    # O estilo e a ordem de seções seguem o template HTML disponibilizado pelo docente.
    template = (ROOT / "src/template_style.css").read_text(encoding="utf-8")
    title = "Evolução da COVID-19 no Brasil e qualidade dos registros municipais (2020–2022)"
    summary = (f"Este estudo examina a evolução dos casos e óbitos por COVID-19 no Brasil e a qualidade dos registros "
               f"municipais disponibilizados pelo Brasil.IO. O arquivo caso_full reúne boletins das secretarias estaduais "
               f"de saúde e registros preenchidos para datas sem nova publicação. Um pipeline em Python processou "
               f"{fmt(meta['raw_rows'])} linhas em blocos, separou observações estaduais das municipais, preservou revisões "
               f"negativas e calculou médias móveis em dias com registros das 27 unidades federativas. No recorte de "
               f"{meta['first_date']} a {meta['last_date']}, o maior valor da média móvel de casos comunicados foi "
               f"{fmt(peak_cases.cases_7d)} por dia em {peak_cases.date.date()}; para óbitos, "
               f"{fmt(peak_deaths.deaths_7d)} por dia em {peak_deaths.date.date()}. Na comparação da última observação "
               f"estadual, a incidência variou de {fmt(lowest.incidence_100k)} a {fmt(highest.incidence_100k)} "
               f"casos por 100 mil habitantes. Entre {fmt(rows)} linhas municipais, {fmt(repeats)} "
               f"({fmt(100*repeats/rows,1)}%) carregam valores repetidos. Os resultados descrevem datas de publicação "
               f"e casos confirmados, sujeitos a subnotificação, atraso de boletins e diferenças de testagem. O estudo "
               f"oferece arquivos abertos, dicionário de dados e código reproduzível conforme princípios FAIR.")
    repo = "https://github.com/marcelobarbosa-dev/projeto-covid19-brasilio"
    body = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Estudo reproduzível de COVID-19 e qualidade de dados Brasil.IO"><meta name="author" content="Marcelo Barbosa de Oliveira Junior"><title>{html.escape(title)}</title><style>{template}</style></head><body><main class="container">
<header><h1 class="paper-title">{html.escape(title)}</h1><div class="meta-block authors">Marcelo Barbosa de Oliveira Junior</div><div class="meta-block affiliations">Universidade La Salle · Bacharelado em Sistemas de Informação · 6º período<br>Disciplina: Linguagem de Programação (Análise e Visualização de Dados com Python)<br>Professor orientador: nome a confirmar</div><div class="badges"><span>Pesquisa quantitativa</span><span>Brasil.IO · caso_full</span><span>Python · FAIR</span></div><a class="repo-badge" href="{repo}" target="_blank" rel="noopener">Repositório e código-fonte</a></header>
<div class="abstract-box"><h3>Resumo</h3><p>{html.escape(summary)}</p><p class="keywords"><strong>Palavras-chave:</strong> COVID-19; Brasil.IO; análise exploratória; qualidade de dados; ciência aberta.</p></div>
<nav class="toc" aria-label="Sumário"><h4>Sumário</h4><ol><li><a href="#intro">Introdução</a></li><li><a href="#metodologia">Metodologia</a></li><li><a href="#resultados">Resultados e discussão</a></li><li><a href="#conclusao">Conclusão</a></li><li><a href="#fair">Disponibilidade e FAIR</a></li><li><a href="#referencias">Referências</a></li></ol></nav>
<section id="intro"><h2>1. Introdução</h2><p>Dados abertos permitem estudar a pandemia em diferentes escalas, mas acumulados estaduais e municipais coexistem na mesma tabela e a cobertura temporal é completada pela repetição de valores anteriores. Uma soma indiferenciada duplicaria totais; zeros em dias repetidos podem refletir a ausência de boletim.</p><p><strong>RQ1.</strong> Como evoluíram os casos e óbitos comunicados pelas 27 UFs em dias de cobertura completa? <strong>RQ2.</strong> Como varia a incidência acumulada entre as UFs no último registro disponível? <strong>RQ3.</strong> Qual a frequência de registros municipais repetidos e de revisões negativas?</p></section>
<section id="metodologia"><h2>2. Metodologia e pipeline de dados</h2><p>Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e colaboradores/Brasil.IO. A tabela <code>caso_full</code> contém uma linha por local e data e repete o último valor disponível quando não há boletim novo. A versão utilizada tem SHA-256 <code>{meta['source_sha256']}</code>, {fmt(meta['raw_rows'])} linhas e período {meta['first_date']} a {meta['last_date']}. Foram excluídas {fmt(meta['invalid_key_rows_excluded'])} linhas com chave temporal/espacial inválida; revisões negativas foram preservadas e contabilizadas.</p><pre><code>for chunk in pd.read_csv(source, compression="gzip", chunksize=150_000):
    chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
    states = chunk.loc[chunk["place_type"].eq("state")]
    # As linhas municipais são analisadas separadamente para qualidade.
national = states.groupby("date")["new_confirmed"].sum()</code></pre><p>O ETL converte datas e números, valida as chaves <code>state</code>/<code>date</code>, não preenche contagens ausentes com zero e preserva revisões. Para totais nacionais, utiliza somente <code>place_type=state</code> e dias com 27 UFs ({fmt(meta['complete_national_days'])} datas). Médias móveis exigem sete dias consecutivos na série filtrada; a incidência usa a estimativa populacional de 2019, com fallback documentado. As comparações entre UFs usam o último registro de cada uma, que pode ter datas distintas; não representam um painel perfeitamente sincronizado.</p></section>
<section id="resultados"><h2>3. Resultados e discussão</h2><h3>RQ1 · Evolução temporal</h3><p>O pico da média móvel de novos casos comunicados foi {fmt(peak_cases.cases_7d)} por dia em {peak_cases.date.date()}; o de óbitos foi {fmt(peak_deaths.deaths_7d)} por dia em {peak_deaths.date.date()}. As curvas medem registros publicados, e oscilações refletem tanto a pandemia quanto o calendário de notificações. Não se infere uma causa a partir de coincidência temporal.</p><figure><img src="assets/casos.svg" alt="Série temporal da média móvel de casos comunicados"><figcaption>Figura 1. Casos comunicados, média móvel de 7 dias; somente dias com 27 UFs. Fonte: Brasil.IO, processamento próprio.</figcaption></figure><figure><img src="assets/obitos.svg" alt="Série temporal da média móvel de óbitos comunicados"><figcaption>Figura 2. Óbitos comunicados, média móvel de 7 dias; mesma cobertura. Fonte: Brasil.IO, processamento próprio.</figcaption></figure><h3>RQ2 · Diferenças estaduais</h3><p>A incidência acumulada no último registro por UF variou de {fmt(lowest.incidence_100k)} por 100 mil habitantes ({lowest.state}, data {lowest.date.date()}) a {fmt(highest.incidence_100k)} ({highest.state}, data {highest.date.date()}). A razão entre esses extremos foi {fmt(highest.incidence_100k/lowest.incidence_100k,1)} vezes. Diferenças de testagem, população estimada e atualização de boletins impedem ler a ordenação como medida isolada de transmissão real.</p><figure><img src="assets/incidencia.svg" alt="Barras horizontais da incidência acumulada por UF"><figcaption>Figura 3. Incidência acumulada no último registro disponível por UF. Fonte: Brasil.IO, processamento próprio.</figcaption></figure><h3>RQ3 · Qualidade do registro</h3><p>Das {fmt(rows)} observações municipais, {fmt(repeats)} ({fmt(100*repeats/rows,1)}%) foram assinaladas como repetidas. A maior proporção estadual foi {fmt(top_repeat.repeated_pct,1)}% em {top_repeat.state}. Foram identificadas {fmt(corrections)} linhas municipais com revisão negativa em casos ou óbitos (uma linha com ambos conta duas vezes na soma de indicadores). A frequência de repetição varia por local e não indica, por si, erro no dado: documenta a diferença entre data da linha e data do boletim.</p><figure><img src="assets/repeticoes.svg" alt="Proporção de observações municipais repetidas por UF"><figcaption>Figura 4. Registros municipais repetidos por UF, todo o período. Fonte: Brasil.IO, processamento próprio.</figcaption></figure></section>
<section id="conclusao"><h2>4. Conclusão</h2><p>As respostas às três perguntas mostram ondas de casos e óbitos notificados, variação espacial na incidência acumulada e grande presença de datas preenchidas a partir de boletins anteriores. A separação entre registros municipais e estaduais é decisiva para evitar dupla contagem. O estudo é descritivo: casos dependem de testagem e notificação, óbitos sofrem atrasos e revisões, a população é estimada e a última data difere entre UFs. Trabalhos futuros podem comparar datas de boletim, usar séries por município com critérios de cobertura e relacionar resultados com políticas e dados de testagem.</p></section>
<section id="fair"><h2>5. Disponibilidade dos dados e declaração FAIR</h2><div class="fair-box"><p><strong>Localizável:</strong> README com autoria, resumo, palavras-chave, URL da fonte e hash da versão. <strong>Acessível:</strong> código e artigo estático; dados brutos disponíveis em acesso público no Brasil.IO. <strong>Interoperável:</strong> CSV/CSV.gz, datas ISO 8601 e <code>data/data_dictionary.md</code>. <strong>Reutilizável:</strong> código MIT; derivados e texto CC BY-SA 4.0 com atribuição à fonte, dependências fixadas e instruções de reprodução.</p></div><pre><code>git clone {repo}
cd projeto-covid19-brasilio
python -m venv .venv
python -m pip install -r requirements.txt
python -m src.etl --download
python -m src.render_article</code></pre><p>Para repetir exatamente esta versão, preserve o arquivo bruto cujo SHA-256 aparece na seção 2; o download futuro pode disponibilizar uma versão diferente.</p></section>
<section id="referencias" class="references"><h2>6. Referências</h2><ol><li>BRASIL.IO. <em>COVID-19: tabela caso_full</em>. Disponível em: <a href="https://brasil.io/dataset/covid19/caso_full/">brasil.io/dataset/covid19/caso_full/</a>. Acesso em: 18 nov. 2026.</li><li>JUSTEN, Álvaro et al. <em>covid19-br: documentação e licença dos dados</em>. Disponível em: <a href="https://github.com/turicas/covid19-br/blob/master/api.md">github.com/turicas/covid19-br</a>. Acesso em: 18 nov. 2026.</li><li>WILKINSON, Mark D. et al. The FAIR Guiding Principles for scientific data management and stewardship. <em>Scientific Data</em>, v. 3, 160018, 2016. DOI: 10.1038/sdata.2016.18.</li></ol></section><footer>Marcelo Barbosa de Oliveira Junior · artigo produzido a partir de dados abertos</footer></main></body></html>'''
    (DOCS / "index.html").write_text(body, encoding="utf-8")
    print(f"Artigo: {DOCS / 'index.html'}; {len(summary.split())} palavras no resumo")


if __name__ == "__main__":
    run()
