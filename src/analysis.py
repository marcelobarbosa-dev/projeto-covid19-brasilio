"""Estatísticas descritivas e verificações reproduzíveis do estudo."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .etl import OUT


def summarize() -> dict:
    daily = pd.read_csv(OUT / "national_daily.csv.gz", parse_dates=["date"]).sort_values("date")
    states = pd.read_csv(OUT / "state_latest.csv", parse_dates=["date"])
    quality = pd.read_csv(OUT / "quality_by_state.csv")
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))

    incidence = states["incidence_100k"].dropna()
    q1, median, q3 = incidence.quantile([.25, .5, .75])
    repeat_q = quality["repeated_pct"].quantile([.25, .5, .75])
    # A comparação é exploratória: incidência e letalidade por casos compartilham
    # o denominador de casos confirmados e dependem de testagem/notificação.
    rank_corr = states[["incidence_100k", "case_fatality_pct"]].dropna().corr(method="spearman").iloc[0, 1]

    # Picos de notificação: dias com cobertura de 27 UFs, sete dias anteriores
    # consecutivos, e mediana anterior >100 casos. Limite superior de Tukey
    # aplicado à razão (casos do dia / mediana dos sete dias anteriores).
    daily["baseline_7d"] = daily["reported_cases"].shift(1).rolling(7, min_periods=7).median()
    complete_window = daily["date"].diff(7).eq(pd.Timedelta(days=7))
    candidates = daily.loc[complete_window & daily["baseline_7d"].gt(100)].copy()
    candidates["ratio"] = candidates["reported_cases"] / candidates["baseline_7d"]
    r1, r3 = candidates["ratio"].quantile([.25, .75])
    cutoff = r3 + 1.5 * (r3 - r1)
    spikes = candidates.loc[candidates.ratio.gt(cutoff)].sort_values("ratio", ascending=False)
    top = spikes.iloc[0]
    # Exporta a trilha completa dos dias sinalizados para permitir auditoria.
    spikes[["date", "reported_cases", "baseline_7d", "ratio"]].to_csv(
        OUT / "reporting_spikes.csv", index=False, date_format="%Y-%m-%d")

    result = {
        "source_sha256": manifest["source_sha256"],
        "states": int(len(states)),
        "latest_dates": sorted(states["date"].dt.strftime("%Y-%m-%d").unique().tolist()),
        "incidence": {"min": float(incidence.min()), "q1": float(q1),
                      "median": float(median), "q3": float(q3),
                      "max": float(incidence.max()),
                      "mean": float(incidence.mean()),
                      "std_sample": float(incidence.std(ddof=1)),
                      "iqr": float(q3-q1),
                      "cv_pct": float(100*incidence.std(ddof=1)/incidence.mean())},
        "rank_correlation_incidence_case_fatality": float(rank_corr),
        "repeated": {"rows": int(quality.city_rows.sum()),
                     "count": int(quality.repeated.sum()),
                     "pct": float(100*quality.repeated.sum()/quality.city_rows.sum()),
                     "state_q1_pct": float(repeat_q.iloc[0]),
                     "state_median_pct": float(repeat_q.iloc[1]),
                     "state_q3_pct": float(repeat_q.iloc[2])},
        "reporting_spikes": {"candidate_days": int(len(candidates)),
                             "upper_fence_ratio": float(cutoff),
                             "count": int(len(spikes)),
                             "top_date": str(top.date.date()),
                             "top_ratio": float(top.ratio),
                             "top_cases": int(top.reported_cases),
                             "top_baseline": float(top.baseline_7d)},
        "negative_national_case_days": int(daily.reported_cases.lt(0).sum())
    }
    (OUT / "analysis_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(summarize(), ensure_ascii=False, indent=2))
