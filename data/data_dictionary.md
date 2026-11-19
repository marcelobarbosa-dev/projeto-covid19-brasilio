# Dicionário de dados

Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e colaboradores/Brasil.IO. [Descrição oficial de `caso_full`](https://brasil.io/dataset/covid19/caso_full/). O recorte processado mantém a granularidade **UF × dia**; a análise de qualidade agrega a granularidade **município × dia**.

| Campo bruto | Tipo/formato | Significado e uso |
|---|---|---|
| `epidemiological_week` | inteiro AAAASS | Semana epidemiológica, não usada na análise. |
| `date` | data YYYY-MM-DD | Data da linha/boletim, chave temporal. |
| `order_for_place` | inteiro | Ordem do registro no local, não usada. |
| `state` | texto, UF | Unidade federativa; chave espacial. |
| `city` | texto/nulo | Município, vazio para `state`; municípios agregados apenas para qualidade. |
| `city_ibge_code` | texto/código | Identificador do local, lido como texto para preservar zeros. |
| `place_type` | categoria `city`/`state` | Granularidade; **somar apenas linhas `state`** para totais nacionais. |
| `last_available_date` | data YYYY-MM-DD/nulo | Data da informação efetivamente disponível. |
| `last_available_confirmed` | inteiro/nulo | Casos acumulados no último boletim disponível. |
| `last_available_confirmed_per_100k_inhabitants` | decimal/nulo | Incidência acumulada fornecida pela fonte; recalculada no projeto. |
| `new_confirmed` | inteiro/nulo | Novos casos desde boletim anterior; negativos representam revisões. |
| `last_available_deaths` | inteiro/nulo | Óbitos acumulados no último boletim. |
| `new_deaths` | inteiro/nulo | Novos óbitos; negativos representam revisões. |
| `last_available_death_rate` | decimal/nulo | Razão óbitos/casos calculada pela fonte, não usada diretamente. |
| `estimated_population` | inteiro/nulo | Estimativa populacional alternativa quando 2019 ausente. |
| `estimated_population_2019` | inteiro/nulo | Estimativa 2019 preferencial para denominador. |
| `is_last` | booleano | Indica registro mais recente por local na fonte. |
| `is_repeated` | booleano | `True` quando valor é carregado de boletim anterior. |

## Campos derivados

| Campo | Tipo/formato | Regra |
|---|---|---|
| `population` | inteiro/nulo | `estimated_population_2019`, com `estimated_population` como fallback. |
| `incidence_100k` | decimal | `last_available_confirmed / population × 100000`; nulo se população ausente. |
| `case_fatality_pct` | decimal (%) | `last_available_deaths / last_available_confirmed × 100`; nulo para zero casos. **Não equivale ao risco de morrer por infecção.** |
| `states_present` | inteiro | Número de UFs com registro na data. |
| `reported_cases`, `reported_deaths` | inteiro/dia | Soma de `new_*` apenas para registros estaduais em dias com 27 UFs. |
| `cases_7d`, `deaths_7d` | decimal/dia | Média móvel de 7 dias com 7 observações. |
| `city_rows`, `repeated`, `negative_cases`, `negative_deaths` | inteiro | Contagens municipais por UF em todo o arquivo. |
| `repeated_pct` | percentual | `100 × repeated / city_rows`. |
| `baseline_7d` | casos/dia | Mediana dos sete dias anteriores consecutivos com cobertura das 27 UFs; não inclui o dia avaliado. |
| `ratio` | número adimensional | `reported_cases / baseline_7d`; só elegível se linha de base >100 casos. |

## Saídas e auditoria

Arquivos em `data/processed/`: `state_daily.csv.gz` (UF × dia), `national_daily.csv.gz` (dia completo), `state_latest.csv` (uma linha por UF), `quality_by_state.csv` (uma linha por UF), `reporting_spikes.csv` (dia sinalizado, casos, linha de base, razão), `analysis_summary.json` (estatísticas descritivas e critérios) e `manifest.json` (proveniência e validações). O JSON usa valores numéricos completos, e os arredondamentos aparecem só na apresentação.

Em `reporting_spikes.csv`, o limite de sinalização é Q3 + 1,5 × IQR das razões dos dias candidatos. São exigidos sete dias imediatamente anteriores com 27 UFs e mediana >100. O limite resultante, o número de candidatos e a contagem sinalizada estão em `analysis_summary.json`. Picos são anomalias de **notificação**, sem atribuição causal a infecções ou a erros de registro.

O manifesto lista contagens de nulos nas colunas brutas usadas, linhas rejeitadas por chaves inválidas e duplicatas estaduais. Não há imputação de casos, óbitos ou população. Datas em ISO 8601, vírgula como separador e UTF-8. Nulos permanecem nulos; revisões negativas são preservadas. O SHA-256 do bruto deve corresponder à versão de referência, salvo uso explícito da opção `--allow-source-update`. Os dados derivados mantêm atribuição e licença **CC BY-SA 4.0** da fonte. O código do projeto tem licença MIT.
