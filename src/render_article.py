"""Produz figuras SVG e artigo HTML a partir dos CSVs gerados pelo ETL."""
from __future__ import annotations

import html
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .analysis import summarize
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
    stats = summarize()
    spikes = pd.read_csv(OUT / "reporting_spikes.csv", parse_dates=["date"])
    if stats["source_sha256"] != meta["source_sha256"]:
        raise ValueError("O resumo estatístico não corresponde à versão da fonte")
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

    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.scatter(spikes.date, spikes.ratio, color="#b45343", s=20, alpha=.8,
               label="Dia sinalizado")
    ax.axhline(stats["reporting_spikes"]["upper_fence_ratio"], color="#1e3a8a",
               linestyle="--", label="Limite de 1,5 × IQR")
    ax.set(title="Picos de notificações em relação à mediana dos 7 dias anteriores",
           ylabel="Razão diária", xlabel="Data")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.2)
    fig.autofmt_xdate(); fig.savefig(ASSETS / "picos_notificacao.svg"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.7, 5.3))
    ax.scatter(latest.incidence_100k, latest.case_fatality_pct, color="#3974aa", alpha=.8)
    for row in latest.itertuples():
        ax.annotate(row.state, (row.incidence_100k, row.case_fatality_pct),
                    xytext=(3, 3), textcoords="offset points", fontsize=7)
    ax.set(title="Incidência e razão óbitos/casos confirmados nas 27 UFs",
           xlabel="Casos confirmados / 100 mil habitantes", ylabel="Óbitos / casos confirmados (%)")
    ax.grid(alpha=.2); fig.savefig(ASSETS / "correlacao_ufs.svg"); plt.close(fig)

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
               f"({fmt(100*repeats/rows,1)}%) carregam valores repetidos. A mediana da incidência entre UFs foi "
               f"{fmt(stats['incidence']['median'])} por 100 mil e {stats['reporting_spikes']['count']} dias "
               f"foram sinalizados como picos relativos de notificação. Os resultados descrevem datas de publicação "
               f"e casos confirmados, sujeitos a subnotificação, atraso de boletins e diferenças de testagem. O estudo "
               f"oferece arquivos abertos, dicionário de dados e código reproduzível conforme princípios FAIR.")
    repo = "https://github.com/marcelobarbosa-dev/projeto-covid19-brasilio"
    body = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Estudo reproduzível de COVID-19 e qualidade de dados Brasil.IO"><meta name="author" content="Marcelo Barbosa de Oliveira Junior"><title>{html.escape(title)}</title><style>{template}</style></head><body><main class="container">
<header><h1 class="paper-title">{html.escape(title)}</h1><div class="meta-block authors">Marcelo Barbosa de Oliveira Junior</div><div class="meta-block affiliations">Universidade La Salle · Bacharelado em Sistemas de Informação · 6º período<br>Disciplina: Linguagem de Programação (Análise e Visualização de Dados com Python)<br>Professor orientador: Alexandre Louzada</div><div class="badges"><span>Pesquisa quantitativa</span><span>Brasil.IO · caso_full</span><span>Python · FAIR</span></div><a class="repo-badge" href="{repo}" target="_blank" rel="noopener">Repositório e código-fonte</a></header>
<div class="abstract-box"><h3>Resumo</h3><p>{html.escape(summary)}</p><p class="keywords"><strong>Palavras-chave:</strong> COVID-19; Brasil.IO; análise exploratória; qualidade de dados; ciência aberta.</p></div>
<nav class="toc" aria-label="Sumário"><h4>Sumário</h4><ol><li><a href="#intro">Introdução</a></li><li><a href="#metodologia">Metodologia</a></li><li><a href="#resultados">Resultados e discussão</a></li><li><a href="#conclusao">Conclusão</a></li><li><a href="#fair">Disponibilidade e FAIR</a></li><li><a href="#referencias">Referências</a></li></ol></nav>
<section id="intro"><h2>1. Introdução</h2><p>Dados abertos permitem estudar a pandemia em diferentes escalas, mas acumulados estaduais e municipais coexistem na mesma tabela e a cobertura temporal é completada pela repetição de valores anteriores. Uma soma indiferenciada duplicaria totais; zeros em dias repetidos podem refletir a ausência de boletim.</p><p><strong>RQ1.</strong> Como evoluíram os casos e óbitos comunicados pelas 27 UFs em dias de cobertura completa? <strong>RQ2.</strong> Como varia a incidência acumulada entre as UFs no último registro disponível? <strong>RQ3.</strong> Qual a frequência de registros municipais repetidos e de revisões negativas?</p></section>
<section id="metodologia"><h2>2. Metodologia e pipeline de dados</h2><p>Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e colaboradores/Brasil.IO. A tabela <code>caso_full</code> contém uma linha por local e data e repete o último valor disponível quando não há boletim novo. A versão utilizada tem SHA-256 <code>{meta['source_sha256']}</code>, {fmt(meta['raw_rows'])} linhas e período {meta['first_date']} a {meta['last_date']}. Foram excluídas {fmt(meta['invalid_key_rows_excluded'])} linhas com chave temporal/espacial inválida; revisões negativas foram preservadas e contabilizadas.</p><pre><code>state_parts = []
for chunk in pd.read_csv(source, compression="gzip", chunksize=150_000):
    chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
    state_parts.append(chunk.loc[chunk["place_type"].eq("state")])
states = pd.concat(state_parts, ignore_index=True)
national = states.groupby("date")["new_confirmed"].sum()</code></pre><p>O trecho ilustra a separação da granularidade; a implementação completa valida tipos e chaves, exige cobertura das 27 UFs e calcula as médias móveis. O ETL não preenche contagens ausentes com zero e preserva revisões. Para totais nacionais, utiliza somente <code>place_type=state</code> e dias com 27 UFs ({fmt(meta['complete_national_days'])} datas). Médias móveis exigem sete dias consecutivos na série filtrada; a incidência usa a estimativa populacional de 2019, com fallback documentado. Nesta versão, os últimos registros das 27 UFs são de 2022-03-27; versões futuras devem verificar a sincronia das datas antes da comparação.</p></section>
<section id="resultados"><h2>3. Resultados e discussão</h2><h3>RQ1 · Evolução temporal</h3><p>O pico da média móvel de novos casos comunicados foi {fmt(peak_cases.cases_7d)} por dia em {peak_cases.date.date()}; o de óbitos foi {fmt(peak_deaths.deaths_7d)} por dia em {peak_deaths.date.date()}. As curvas medem registros publicados, e oscilações refletem tanto a pandemia quanto o calendário de notificações. Não se infere uma causa a partir de coincidência temporal.</p><figure><img src="assets/casos.svg" alt="Série temporal da média móvel de casos comunicados"><figcaption>Figura 1. Casos comunicados, média móvel de 7 dias; somente dias com 27 UFs. Fonte: Brasil.IO, processamento próprio.</figcaption></figure><figure><img src="assets/obitos.svg" alt="Série temporal da média móvel de óbitos comunicados"><figcaption>Figura 2. Óbitos comunicados, média móvel de 7 dias; mesma cobertura. Fonte: Brasil.IO, processamento próprio.</figcaption></figure><h3>RQ2 · Diferenças estaduais</h3><p>A incidência acumulada no último registro por UF variou de {fmt(lowest.incidence_100k)} por 100 mil habitantes ({lowest.state}, data {lowest.date.date()}) a {fmt(highest.incidence_100k)} ({highest.state}, data {highest.date.date()}). A razão entre esses extremos foi {fmt(highest.incidence_100k/lowest.incidence_100k,1)} vezes. Diferenças de testagem, população estimada e atualização de boletins impedem ler a ordenação como medida isolada de transmissão real.</p><figure><img src="assets/incidencia.svg" alt="Barras horizontais da incidência acumulada por UF"><figcaption>Figura 3. Incidência acumulada no último registro disponível por UF. Fonte: Brasil.IO, processamento próprio.</figcaption></figure><h3>RQ3 · Qualidade do registro</h3><p>Das {fmt(rows)} observações municipais, {fmt(repeats)} ({fmt(100*repeats/rows,1)}%) foram assinaladas como repetidas. A maior proporção estadual foi {fmt(top_repeat.repeated_pct,1)}% em {top_repeat.state}. Foram identificadas {fmt(corrections)} ocorrências de revisão negativa nas contagens municipais de casos ou óbitos; uma linha com ambos os indicadores negativos contribui com duas ocorrências. A frequência de repetição varia por local e não indica, por si, erro no dado: documenta a diferença entre data da linha e data do boletim.</p><figure><img src="assets/repeticoes.svg" alt="Proporção de observações municipais repetidas por UF"><figcaption>Figura 4. Registros municipais repetidos por UF, todo o período. Fonte: Brasil.IO, processamento próprio.</figcaption></figure></section>
<section id="conclusao"><h2>4. Conclusão</h2><p>As respostas às três perguntas mostram ondas de casos e óbitos notificados, variação espacial na incidência acumulada e grande presença de datas preenchidas a partir de boletins anteriores. A separação entre registros municipais e estaduais é decisiva para evitar dupla contagem. O estudo é descritivo: casos dependem de testagem e notificação, óbitos sofrem atrasos e revisões, a população é estimada e a última data difere entre UFs. Trabalhos futuros podem comparar datas de boletim, usar séries por município com critérios de cobertura e relacionar resultados com políticas e dados de testagem.</p></section>
<section id="fair"><h2>5. Disponibilidade dos dados e declaração FAIR</h2><div class="fair-box"><p><strong>Localizável:</strong> README com autoria, resumo, palavras-chave, URL da fonte e hash da versão. <strong>Acessível:</strong> código e artigo estático; dados brutos disponíveis em acesso público no Brasil.IO. <strong>Interoperável:</strong> CSV/CSV.gz, datas ISO 8601 e <code>data/data_dictionary.md</code>. <strong>Reutilizável:</strong> código MIT; derivados e texto CC BY-SA 4.0 com atribuição à fonte, dependências fixadas e instruções de reprodução.</p></div><pre><code>git clone {repo}
cd projeto-covid19-brasilio
python -m venv .venv
python -m pip install -r requirements.txt
python -m src.etl --download
python -m src.render_article</code></pre><p>Para repetir exatamente esta versão, preserve o arquivo bruto cujo SHA-256 aparece na seção 2; o download futuro pode disponibilizar uma versão diferente.</p></section>
<section id="referencias" class="references"><h2>6. Referências</h2><ol><li>BRASIL.IO. <em>COVID-19: tabela caso_full</em>. Disponível em: <a href="https://brasil.io/dataset/covid19/caso_full/">brasil.io/dataset/covid19/caso_full/</a>. Acesso em: 18 nov. 2026.</li><li>JUSTEN, Álvaro et al. <em>covid19-br: documentação e licença dos dados</em>. Disponível em: <a href="https://github.com/turicas/covid19-br/blob/master/api.md">github.com/turicas/covid19-br</a>. Acesso em: 18 nov. 2026.</li><li>WILKINSON, Mark D. et al. The FAIR Guiding Principles for scientific data management and stewardship. <em>Scientific Data</em>, v. 3, 160018, 2016. DOI: 10.1038/sdata.2016.18.</li></ol></section><footer>Marcelo Barbosa de Oliveira Junior · artigo produzido a partir de dados abertos</footer></main></body></html>'''
    inc = stats["incidence"]
    rpt = stats["repeated"]
    spike = stats["reporting_spikes"]
    method_extra = (f"<p><strong>Auditoria de nulos:</strong> o manifesto registra a ausência em cada coluna bruta. "
                    f"Nos {fmt(meta['state_rows'])} registros estaduais, casos, óbitos e população utilizados nas "
                    f"métricas não apresentam nulos; nessas variáveis nenhuma imputação foi necessária. Nulos "
                    f"municipais permanecem ausentes, sem conversão em zero. O bruto tem checksum SHA-256 "
                    f"fixado no ETL; uma versão alterada é recusada por padrão. Picos relativos usam a razão "
                    f"entre casos do dia e a mediana dos sete dias anteriores, apenas com sete datas consecutivas "
                    f"e mediana acima de 100. O limite superior é Q3 + 1,5 × (Q3 − Q1) dessa razão, uma "
                    f"regra descritiva de identificação de extremos, não um teste de causalidade.</p>")
    body = body.replace("<h2>2. Metodologia e pipeline de dados</h2>",
                        "<h2>2. Metodologia e pipeline de dados</h2>" + method_extra, 1)

    extra_results = f'''<h3>RQ1 · Dispersão e valores extremos de notificações</h3>
<p>Entre {fmt(spike['candidate_days'])} dias elegíveis, {fmt(spike['count'])} ultrapassaram a razão de {fmt(spike['upper_fence_ratio'],2)} entre casos comunicados no dia e a mediana dos sete dias anteriores. O maior valor ocorreu em {spike['top_date']}: {fmt(spike['top_cases'])} casos, equivalentes a {fmt(spike['top_ratio'],2)} vezes a mediana anterior ({fmt(spike['top_baseline'])}). A triagem identifica saltos nos <em>boletins</em>; não autoriza afirmar que houve aumento súbito de infecções naquela data.</p>
<figure><img src="assets/picos_notificacao.svg" alt="Picos relativos de notificações sinalizados pela regra do intervalo interquartil"><figcaption>Figura 5. Dias acima da cerca superior de Tukey para a razão de notificações; método e janela definidos na seção 2. Fonte: Brasil.IO, processamento próprio.</figcaption></figure>
<h3>RQ2 · Dispersão e associação entre indicadores</h3>
<p>Em {fmt(stats['states'])} UFs, a incidência acumulada teve mediana de {fmt(inc['median'])} casos/100 mil, Q1 de {fmt(inc['q1'])}, Q3 de {fmt(inc['q3'])} e intervalo interquartil de {fmt(inc['iqr'])}. O desvio padrão amostral foi {fmt(inc['std_sample'])}; o coeficiente de variação, {fmt(inc['cv_pct'],1)}%. A correlação de postos de Spearman entre incidência e razão óbitos/casos confirmados foi {fmt(stats['rank_correlation_incidence_case_fatality'],2)} (27 UFs, descritiva, sem teste de significância). Os dois índices compartilham casos confirmados no cálculo e dependem da testagem; portanto a associação não demonstra proteção ou causalidade.</p>
<figure><img src="assets/correlacao_ufs.svg" alt="Dispersão da incidência e proporção óbitos sobre casos por UF"><figcaption>Figura 6. Relação exploratória entre incidência e razão óbitos/casos confirmados, último registro das 27 UFs. Fonte: Brasil.IO, processamento próprio.</figcaption></figure>
<p><strong>Variação na qualidade:</strong> a proporção de registros municipais repetidos por UF teve mediana de {fmt(rpt['state_median_pct'],1)}%, Q1 de {fmt(rpt['state_q1_pct'],1)}% e Q3 de {fmt(rpt['state_q3_pct'],1)}%. A média ponderada por linha, {fmt(rpt['pct'],1)}%, responde a uma pergunta diferente da mediana das 27 UFs.</p>
<div class="explorer"><label for="metric-choice">Explore o indicador por UF:</label> <select id="metric-choice"><option value="incidencia">Incidência / 100 mil</option><option value="letalidade">Óbitos / casos confirmados (%)</option><option value="repetidos">Registros municipais repetidos (%)</option></select><div id="metric-bars" role="list" aria-live="polite"></div><p class="note">Gráfico interativo: selecione a métrica para comparar as 27 UFs. A razão óbitos/casos não equivale à letalidade entre infectados.</p></div>'''
    boundary = '</section>\n<section id="conclusao">'
    assert body.count(boundary) == 1
    body = body.replace(boundary, extra_results + boundary, 1)

    body = body.replace("a população é estimada e a última data difere entre UFs.",
                        "a população é estimada e o período termina em março de 2022.", 1)
    body = body.replace("O estudo é descritivo: casos dependem de testagem e notificação,",
                        "Picos de notificação, dispersão estadual e correlação ampliam a resposta exploratória, mas não identificam causas. O estudo é descritivo: casos dependem de testagem e notificação,", 1)
    body = body.replace("python -m src.render_article</code>",
                        "python -m src.analysis\npython -m notebooks.build_notebook\npython -m src.render_article</code>", 1)
    refs = ('''<li>PANDAS DEVELOPMENT TEAM. <em>pandas documentation: windowing operations</em>. Disponível em: <a href="https://pandas.pydata.org/docs/user_guide/window.html">pandas.pydata.org/docs/user_guide/window.html</a>. Acesso em: 19 nov. 2026.</li>'''
            '''<li>NUMPY DEVELOPERS. <em>NumPy statistics reference</em>. Disponível em: <a href="https://numpy.org/doc/stable/reference/routines.statistics.html">numpy.org/doc/stable/reference/routines.statistics.html</a>. Acesso em: 19 nov. 2026.</li>'''
            '''<li>MATPLOTLIB DEVELOPMENT TEAM. <em>Matplotlib documentation</em>. Disponível em: <a href="https://matplotlib.org/stable/">matplotlib.org/stable/</a>. Acesso em: 19 nov. 2026.</li>'''
            '''<li>NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY. <em>Box Plot</em>. Disponível em: <a href="https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm">itl.nist.gov/div898/handbook/eda/section3/boxplot.htm</a>. Acesso em: 19 nov. 2026.</li>''')
    body = body.replace('</ol></section><footer>', refs + '</ol></section><footer>', 1)

    enriched = latest.merge(quality[["state", "repeated_pct"]], on="state", validate="one_to_one")
    payload = json.dumps([{"uf": r.state, "incidencia": round(r.incidence_100k, 1),
                           "letalidade": round(r.case_fatality_pct, 2),
                           "repetidos": round(r.repeated_pct, 1)} for r in enriched.itertuples()],
                         ensure_ascii=False)
    script = '''<script>
const stateData = __PAYLOAD__;
const select = document.getElementById('metric-choice');
const bars = document.getElementById('metric-bars');
function renderMetric() {
  const key = select.value;
  const data = [...stateData].sort((a,b) => b[key] - a[key]);
  const max = data[0][key];
  bars.replaceChildren();
  for (const item of data) {
    const row = document.createElement('div'); row.className = 'metric-row'; row.role = 'listitem';
    const label = document.createElement('strong'); label.textContent = item.uf;
    const track = document.createElement('div'); track.className = 'metric-track';
    const fill = document.createElement('div'); fill.className = 'metric-fill';
    fill.style.width = (100 * item[key] / max).toFixed(2) + '%'; track.append(fill);
    const value = document.createElement('span'); value.textContent = item[key].toLocaleString('pt-BR');
    row.append(label, track, value); bars.append(row);
  }
}
select.addEventListener('change', renderMetric); renderMetric();
</script>'''.replace('__PAYLOAD__', payload)
    body = body.replace('</body>', script + '</body>', 1)
    (DOCS / "index.html").write_text(body, encoding="utf-8")
    print(f"Artigo: {DOCS / 'index.html'}; {len(summary.split())} palavras no resumo")


if __name__ == "__main__":
    run()
