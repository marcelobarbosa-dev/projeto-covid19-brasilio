"""Ingestão em blocos, limpeza auditável e indicadores estaduais."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://data.brasil.io/dataset/covid19/caso_full.csv.gz"
RAW = ROOT / "data/raw/caso_full.csv.gz"
OUT = ROOT / "data/processed"
COLS = ["date", "state", "city", "city_ibge_code", "place_type",
        "last_available_date", "last_available_confirmed", "new_confirmed",
        "last_available_deaths", "new_deaths", "estimated_population_2019",
        "estimated_population", "is_last", "is_repeated"]
NUMS = ["last_available_confirmed", "new_confirmed", "last_available_deaths",
        "new_deaths", "estimated_population_2019", "estimated_population"]


def download(force=False):
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if RAW.exists() and not force:
        return RAW
    request = Request(URL, headers={"User-Agent": "Mozilla/5.0 (academic research)",
                                    "Referer": "https://brasil.io/"})
    temp = RAW.with_suffix(".part")
    with urlopen(request, timeout=120) as response, temp.open("wb") as target:
        while block := response.read(1024 * 1024):
            target.write(block)
    temp.replace(RAW)
    return RAW


def build(source=RAW):
    OUT.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256()
    with Path(source).open("rb") as f:
        while block := f.read(1024 * 1024):
            sha.update(block)
    state_parts, quality_parts = [], []
    n_raw = n_invalid = n_negative = 0
    for chunk in pd.read_csv(source, compression="gzip", usecols=COLS, chunksize=150_000,
                             dtype={"state": "string", "city": "string", "place_type": "string",
                                    "city_ibge_code": "string"}, low_memory=False):
        n_raw += len(chunk)
        chunk["date"] = pd.to_datetime(chunk["date"], errors="coerce")
        chunk["last_available_date"] = pd.to_datetime(chunk["last_available_date"], errors="coerce")
        for col in NUMS:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        chunk["is_repeated"] = chunk["is_repeated"].astype("string").str.lower().eq("true")
        valid = chunk["date"].notna() & chunk["state"].str.fullmatch("[A-Z]{2}").fillna(False)
        valid &= chunk["place_type"].isin(["city", "state"])
        n_invalid += int((~valid).sum())
        chunk = chunk.loc[valid].copy()
        n_negative += int(((chunk["new_confirmed"] < 0) | (chunk["new_deaths"] < 0)).sum())
        state_parts.append(chunk.loc[chunk.place_type.eq("state")].copy())
        city = chunk.loc[chunk.place_type.eq("city")].copy()
        if not city.empty:
            quality_parts.append(city.groupby("state", observed=True).agg(
                city_rows=("date", "size"), repeated=("is_repeated", "sum"),
                negative_cases=("new_confirmed", lambda x: int((x < 0).sum())),
                negative_deaths=("new_deaths", lambda x: int((x < 0).sum()))).reset_index())
    states = pd.concat(state_parts, ignore_index=True).sort_values(["state", "date"])
    dup = int(states.duplicated(["state", "date"]).sum())
    if dup:
        raise ValueError(f"{dup} linhas estaduais com chave state/date duplicada; verificar fonte")
    states["population"] = states["estimated_population_2019"].fillna(states["estimated_population"])
    states["incidence_100k"] = states["last_available_confirmed"] / states["population"] * 100_000
    states["case_fatality_pct"] = states["last_available_deaths"] / states["last_available_confirmed"].replace(0, np.nan) * 100
    state_cols = ["date", "state", "last_available_date", "last_available_confirmed",
                  "new_confirmed", "last_available_deaths", "new_deaths", "population",
                  "is_repeated", "incidence_100k", "case_fatality_pct"]
    states[state_cols].to_csv(OUT / "state_daily.csv.gz", index=False, compression="gzip")
    daily = states.groupby("date", observed=True).agg(
        states_present=("state", "nunique"), reported_cases=("new_confirmed", "sum"),
        reported_deaths=("new_deaths", "sum"), repeated_states=("is_repeated", "sum")).reset_index()
    daily = daily.loc[daily.states_present.eq(27)].copy().sort_values("date")
    daily["cases_7d"] = daily["reported_cases"].rolling(7, min_periods=7).mean()
    daily["deaths_7d"] = daily["reported_deaths"].rolling(7, min_periods=7).mean()
    consecutive = daily["date"].diff(6).eq(pd.Timedelta(days=6))
    daily.loc[~consecutive, ["cases_7d", "deaths_7d"]] = np.nan
    daily.to_csv(OUT / "national_daily.csv.gz", index=False, compression="gzip")
    latest = states.sort_values("date").drop_duplicates("state", keep="last").copy()
    latest[state_cols].to_csv(OUT / "state_latest.csv", index=False)
    quality = pd.concat(quality_parts).groupby("state", as_index=False).sum(numeric_only=True)
    quality["repeated_pct"] = 100 * quality.repeated / quality.city_rows
    quality.to_csv(OUT / "quality_by_state.csv", index=False)
    manifest = {"source": URL, "source_sha256": sha.hexdigest(), "raw_rows": n_raw,
                "invalid_key_rows_excluded": n_invalid, "negative_daily_rows_preserved": n_negative,
                "state_rows": len(states), "city_rows": int(quality.city_rows.sum()),
                "first_date": str(states.date.min().date()), "last_date": str(states.date.max().date()),
                "complete_national_days": len(daily), "state_count_latest": len(latest),
                "population_note": "2019 preferred; estimated_population fallback when 2019 missing"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Baixa a versão disponível no Brasil.IO")
    parser.add_argument("--force", action="store_true", help="Substitui o bruto local")
    args = parser.parse_args()
    if args.download:
        download(args.force)
    if not RAW.exists():
        parser.error("Arquivo bruto ausente. Use --download ou copie caso_full.csv.gz para data/raw/.")
    print(json.dumps(build(), ensure_ascii=False, indent=2))
