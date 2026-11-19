"""Gera e executa o notebook exploratório a partir dos dados processados."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "notebooks" / "analise_exploratoria.ipynb"


def markdown(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source, scope, execution_count):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(source, f"notebook_cell_{execution_count}", "exec"), scope)
    outputs = []
    if output.getvalue():
        outputs.append({"output_type": "stream", "name": "stdout", "text": output.getvalue().splitlines(keepends=True)})
    for fig_number in plt.get_fignums():
        fig = plt.figure(fig_number)
        vector = io.StringIO()
        fig.savefig(vector, format="svg", bbox_inches="tight")
        outputs.append({"output_type": "display_data", "metadata": {}, "data": {"image/svg+xml": vector.getvalue().splitlines(keepends=True)}})
    plt.close("all")
    return {"cell_type": "code", "execution_count": execution_count, "metadata": {},
            "source": source.splitlines(keepends=True), "outputs": outputs}


def main():
    cells = [markdown("# Análise exploratória: COVID-19, Brasil.IO\n\nAutor: Marcelo Barbosa de Oliveira Junior. Professor: Alexandre Louzada. Fonte: `caso_full`, versão fixada no manifesto. Dados até 27/03/2022. Execute na raiz do repositório após `python -m src.etl`. A análise é descritiva e não estima causalidade.\n")]
    scope = {"__name__": "__main__"}
    blocks = [
        ("## 1. Carga e proveniência\nUsamos apenas o painel estadual para totais nacionais e o municipal para a auditoria de repetições.\n", """import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from src.analysis import summarize

root = Path.cwd()
out = root / 'data' / 'processed'
daily = pd.read_csv(out / 'national_daily.csv.gz', parse_dates=['date'])
states = pd.read_csv(out / 'state_latest.csv')
quality = pd.read_csv(out / 'quality_by_state.csv')
manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
print('SHA-256 do original:', manifest['source_sha256'])
print('Linhas brutas:', manifest['raw_rows'])
print('Dias com 27 UFs:', len(daily), '| UFs na última data:', len(states))
print('Nulos brutos auditados:', manifest['missing_values_by_raw_column'])
"""),
        ("## 2. Distribuição e tendência temporal\nAs séries são notificações diárias; valores negativos por revisão são mantidos. A média móvel exige sete dias consecutivos.\n", """print('Primeira e última data:', daily.date.min().date(), daily.date.max().date())
print('Casos nacionais negativos em dias completos:', int((daily.reported_cases < 0).sum()))
fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
for ax, raw, moving, label, color in [(axes[0], 'reported_cases', 'cases_7d', 'Casos', '#356ab2'),
                                      (axes[1], 'reported_deaths', 'deaths_7d', 'Óbitos', '#b75845')]:
    ax.plot(daily.date, daily[raw], color=color, alpha=.18, label='Boletim diário')
    ax.plot(daily.date, daily[moving], color=color, linewidth=1.7, label='Média 7 dias')
    ax.set_ylabel(label)
    ax.legend(loc='upper left')
fig.suptitle('Notificações em dias com 27 UFs')
fig.tight_layout()
"""),
        ("## 3. Variação entre UFs\nIncidência por 100 mil moradores na última data, 27/03/2022. O desvio padrão usa `ddof=1`; a correlação de Spearman é exploratória, pois incidência e letalidade por casos compartilham casos confirmados.\n", """stats = summarize()
print('Incidência (mín., Q1, mediana, Q3, máx.):',
      *(f'{stats["incidence"][key]:.1f}' for key in ('min','q1','median','q3','max')))
print('Média, DP amostral, IQR e CV%:',
      *(f'{stats["incidence"][key]:.1f}' for key in ('mean','std_sample','iqr','cv_pct')))
print('Spearman incidência × letalidade por casos:',
      f'{stats["rank_correlation_incidence_case_fatality"]:.3f}')
ranking = states.sort_values('incidence_100k')
plt.figure(figsize=(9, 8))
plt.barh(ranking.state, ranking.incidence_100k, color='#356ab2')
plt.xlabel('Casos acumulados por 100 mil habitantes')
plt.title('Incidência acumulada nas 27 UFs')
plt.tight_layout()
"""),
        ("## 4. Qualidade e picos de notificação\nUm pico é uma razão acima de Q3 + 1,5×IQR em 730 dias candidatos; a linha de base é a mediana dos sete dias anteriores consecutivos e deve superar 100 casos. Um pico não implica aumento real de infecções naquele dia.\n", """spikes = pd.read_csv(out / 'reporting_spikes.csv')
print('Linhas municipais:', stats['repeated']['rows'])
print('Repetidas:', stats['repeated']['count'],
      f'({stats["repeated"]["pct"]:.2f}%)')
print('Mediana estadual de repetição:', f'{stats["repeated"]["state_median_pct"]:.2f}%')
print('Dias candidatos / sinalizados:', stats['reporting_spikes']['candidate_days'], '/', len(spikes))
print('Limiar da razão:', f'{stats["reporting_spikes"]["upper_fence_ratio"]:.3f}')
print('Cinco maiores razões de notificação:')
print(spikes[['date','reported_cases','baseline_7d','ratio']].head().to_string(index=False))
"""),
    ]
    n = 0
    for explanation, source in blocks:
        cells.append(markdown(explanation))
        n += 1
        cells.append(code(source, scope, n))
    cells.append(markdown("## Interpretação e limites\nA heterogeneidade de incidência pode refletir testagem, acesso e critérios de registro, além da circulação do vírus. Linhas municipais repetidas são características de publicação, não novos casos. O último registro da fonte é de março de 2022. Consulte o artigo em `docs/index.html` para métodos, resultados, referências e a discussão completa.\n"))
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}, "nbformat": 4, "nbformat_minor": 5}
    DEST.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Notebook executado: {DEST}; {n} células de código, com {sum(bool(c.get('outputs')) for c in cells)} saídas.")


if __name__ == "__main__":
    main()
