"""Leitura das tabelas geradas por etl/preparar_dados.py."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

PASTA = Path(__file__).resolve().parent.parent
DADOS = PASTA / "data"
ASSETS = PASTA / "assets"


@st.cache_data(show_spinner=False)
def titulacoes() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "titulacoes.parquet")


@st.cache_data(show_spinner=False)
def pessoas() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "pessoas.parquet")


@st.cache_data(show_spinner=False)
def remuneracao() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "remuneracao.parquet")


@st.cache_data(show_spinner=False)
def validacao_capes() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "validacao_capes.parquet")


@st.cache_data(show_spinner=False)
def capes_incorporadas() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "capes_incorporadas.parquet")


@st.cache_data(show_spinner=False)
def meta() -> dict:
    return json.loads((DADOS / "meta.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def malha_uf() -> dict:
    return json.loads((ASSETS / "br_uf.geojson").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def malha_pa() -> dict:
    return json.loads((ASSETS / "pa_municipios.geojson").read_text(encoding="utf-8"))
