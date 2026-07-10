"""
dune_helper.py — utilidades reutilizables para trabajar con Dune Analytics.

Uso típico:
    from scripts.dune_helper import run_query, latest_result, run_sql

Notas de plan (importante):
- La cuenta actual es plan **Free**: la API permite EJECUTAR queries en el cluster
  gratuito (omitiendo el parámetro `performance`) y LEER resultados cacheados.
  Los tiers "medium"/"large" NO están disponibles (devuelven "Invalid performance tier").
- Por eso ejecutamos vía REST omitiendo `performance`, en vez de usar
  DuneClient.run_query_dataframe (que fuerza el cluster medium).

Reglas del proyecto:
- La API key SIEMPRE sale de la env var DUNE_API_KEY (nunca hardcodeada, nunca impresa).
- Resultados se cachean en ./data/ como parquet y se reutilizan en la sesión.
- Para no gastar créditos, preferí latest_result() (lee lo ya ejecutado) sobre run_query().
"""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
BASE = "https://api.dune.com/api/v1"


def _key() -> str:
    k = os.environ.get("DUNE_API_KEY")
    if not k:
        raise RuntimeError(
            "DUNE_API_KEY no está configurada. Ponela en .env o exportala en el shell."
        )
    return k


def _headers() -> dict:
    return {"X-Dune-API-Key": _key()}


def get_client():
    """DuneClient del SDK oficial (útil para create_query/update_query/lecturas)."""
    from dune_client.client import DuneClient
    return DuneClient(_key())


def _cache_path(tag: str, key_material: str) -> Path:
    h = hashlib.md5(key_material.encode()).hexdigest()[:10]
    return DATA_DIR / f"dune_{tag}_{h}.parquet"


def _rows_to_df(result_json: dict) -> pd.DataFrame:
    rows = result_json.get("result", {}).get("rows", [])
    return pd.DataFrame(rows)


def _safe_to_parquet(df: pd.DataFrame, path: Path) -> None:
    """
    Guarda a parquet de forma robusta. Las tablas decodificadas de Solana traen
    columnas con listas/dicts anidados (ej. call_inner_instructions) que pyarrow
    no serializa directo -> se convierten a JSON string. Si aun así falla, no rompe.
    """
    import json
    try:
        df.to_parquet(path)
        return
    except Exception:
        safe = df.copy()
        for col in safe.columns:
            if safe[col].dtype == object:
                safe[col] = safe[col].apply(
                    lambda v: json.dumps(v, default=str) if isinstance(v, (list, dict)) else v
                )
        try:
            safe.to_parquet(path)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] no se pudo cachear en parquet ({e}); resultado NO cacheado.")


def latest_result(query_id: int, cache: bool = True) -> pd.DataFrame:
    """
    Lee el ÚLTIMO resultado cacheado de una query en Dune SIN re-ejecutarla.
    Es la vía más barata (no gasta créditos de ejecución). Ideal para queries
    públicas/propias que ya corrieron.
    """
    cache_path = _cache_path(f"latest_{query_id}", str(query_id))
    if cache and cache_path.exists():
        print(f"[cache local] {cache_path.name}")
        return pd.read_parquet(cache_path)

    r = requests.get(f"{BASE}/query/{query_id}/results", headers=_headers(), timeout=60)
    r.raise_for_status()
    df = _rows_to_df(r.json())
    if cache and not df.empty:
        _safe_to_parquet(df, cache_path)
    print(f"[dune latest] query {query_id}: {len(df)} filas (resultado cacheado en Dune)")
    return df


def execute_query(query_id: int, params: dict | None = None,
                  cache: bool = True, ping: float = 2.0, timeout_s: int = 300) -> pd.DataFrame:
    """
    EJECUTA una query existente (por ID) en el cluster gratuito (plan Free) y espera
    el resultado. Gasta créditos de ejecución -> usar con criterio.

    - params: parámetros de la query {nombre: valor}.
    - cache: guarda/lee en ./data/ para no re-ejecutar en la misma sesión.
    """
    cache_path = _cache_path(f"exec_{query_id}", f"{query_id}-{sorted((params or {}).items())}")
    if cache and cache_path.exists():
        print(f"[cache local] {cache_path.name} (sin gastar créditos)")
        return pd.read_parquet(cache_path)

    body = {}
    if params:
        body["query_parameters"] = params
    # Clave: NO enviar 'performance' -> usa cluster gratuito del plan Free.
    r = requests.post(f"{BASE}/query/{query_id}/execute", headers=_headers(), json=body, timeout=60)
    r.raise_for_status()
    eid = r.json()["execution_id"]
    print(f"[dune exec] query {query_id} -> execution {eid} (cluster free)")

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        st = requests.get(f"{BASE}/execution/{eid}/status", headers=_headers(), timeout=60).json()
        state = st.get("state")
        if state == "QUERY_STATE_COMPLETED":
            res = requests.get(f"{BASE}/execution/{eid}/results", headers=_headers(), timeout=120).json()
            df = _rows_to_df(res)
            if cache and not df.empty:
                _safe_to_parquet(df, cache_path)
            print(f"[dune exec] completado: {len(df)} filas")
            return df
        if state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED", "QUERY_STATE_EXPIRED"):
            raise RuntimeError(f"Ejecución {eid} terminó en estado {state}: {st}")
        time.sleep(ping)
    raise TimeoutError(f"Ejecución {eid} no completó en {timeout_s}s")


def run_sql(sql: str, name: str = "adhoc_query", params: dict | None = None,
            keep: bool = False, cache: bool = True) -> pd.DataFrame:
    """
    Crea una query ad-hoc con SQL crudo, la ejecuta en el cluster gratuito y devuelve
    un DataFrame. Por defecto la archiva al terminar (keep=False) para no ensuciar Dune.

    Útil para exploración. Para análisis reproducibles, guardá el SQL en ./queries/
    y usá execute_query() con el ID persistente.
    """
    client = get_client()
    q = client.create_query(name=name, query_sql=sql)
    qid = q.base.query_id
    try:
        return execute_query(qid, params=params, cache=cache)
    finally:
        if not keep:
            try:
                client.archive_query(qid)
            except Exception as e:  # noqa: BLE001
                print(f"[warn] no se pudo archivar query {qid}: {e}")


if __name__ == "__main__":
    # Smoke test end-to-end en cluster free.
    try:
        df = run_sql("SELECT 1 AS ok, now() AS ts", name="smoke_test_delete_me")
        print("OK end-to-end:", df.to_dict(orient="records"))
    except Exception as e:  # noqa: BLE001
        print(f"FALLO: {type(e).__name__}: {e}")
