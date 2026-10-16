"""Painel de Egressos do PPGDSTU/NAEA/UFPA.

Rodar:  streamlit run app.py
Dados:  gerados por ../etl/preparar_dados.py em data/
"""
from pathlib import Path

import streamlit as st

AQUI = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Egressos do PPGDSTU · NAEA/UFPA",
    page_icon=str(AQUI / "assets" / "naea.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

import core.theme  # noqa: E402,F401  (registra o modelo visual do Plotly)
from core import components as ui  # noqa: E402
from core import data  # noqa: E402

paginas = [
    st.Page(AQUI / "views" / "panorama.py", title="Panorama", url_path="panorama", default=True),
    st.Page(AQUI / "views" / "formacao.py", title="Formação", url_path="formacao"),
    st.Page(AQUI / "views" / "graduacao.py", title="Graduação", url_path="graduacao"),
    st.Page(AQUI / "views" / "orientacao.py", title="Orientação", url_path="orientacao"),
    st.Page(AQUI / "views" / "destino.py", title="Destino profissional", url_path="destino"),
    st.Page(AQUI / "views" / "territorio.py", title="Território", url_path="territorio"),
    st.Page(AQUI / "views" / "correlacoes.py", title="Correlações", url_path="correlacoes"),
    st.Page(AQUI / "views" / "consulta.py", title="Consulta", url_path="consulta"),
    st.Page(AQUI / "views" / "metodologia.py", title="Metodologia", url_path="metodologia"),
]
pagina = st.navigation(paginas, position="hidden")

ui.estilo()
meta = data.meta()
ui.cabecalho(meta)
ui.navegacao(paginas, pagina)
pagina.run()
ui.rodape(meta)
