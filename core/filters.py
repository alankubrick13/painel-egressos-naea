"""Filtros globais: uma faixa acima do conteúdo, a mesma em todas as páginas.

O recorte vale para tudo abaixo dele. Fica guardado em st.session_state (sobrevive
à troca de página) e espelhado na URL (link compartilhável).
"""
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from core.theme import NOME_LINHA, ORDEM_LINHAS, ORDEM_NIVEL, num


@dataclass
class Recorte:
    titulacoes: pd.DataFrame
    pessoas: pd.DataFrame
    ativo: bool          # algum filtro diferente do padrão?
    descricao: str


def _padrao(tit):
    return {"periodo": (int(tit["ANO"].min()), int(tit["ANO"].max())), "nivel": list(ORDEM_NIVEL),
            "linha": [], "orientador": [], "area": []}


def _da_url(padrao):
    q = st.query_params
    f = dict(padrao)
    try:
        if "periodo" in q:
            a, b = (int(x) for x in q["periodo"].split("-"))
            f["periodo"] = (max(a, padrao["periodo"][0]), min(b, padrao["periodo"][1]))
        if "nivel" in q:
            f["nivel"] = [x for x in q["nivel"].split(",") if x in ORDEM_NIVEL] or list(ORDEM_NIVEL)
        if "linha" in q:
            f["linha"] = [x for x in q["linha"].split(",") if x in NOME_LINHA]
        if "orientador" in q:
            f["orientador"] = q.get_all("orientador")
        if "area" in q:
            f["area"] = q.get_all("area")
    except ValueError:
        return padrao
    return f


def _para_url(f, padrao):
    q = {}
    if tuple(f["periodo"]) != padrao["periodo"]:
        q["periodo"] = f"{f['periodo'][0]}-{f['periodo'][1]}"
    if set(f["nivel"]) != set(padrao["nivel"]):
        q["nivel"] = ",".join(f["nivel"])
    if f["linha"]:
        q["linha"] = ",".join(f["linha"])
    if f["orientador"]:
        q["orientador"] = f["orientador"]
    if f["area"]:
        q["area"] = f["area"]
    st.query_params.from_dict(q)


def _iniciar(chave, valor):
    if chave not in st.session_state:
        st.session_state[chave] = valor


def limpar():
    for k in ("w_periodo", "w_nivel", "w_linha", "w_orientador", "w_area", "flt"):
        st.session_state.pop(k, None)
    st.query_params.clear()


def barra(tit: pd.DataFrame, pes: pd.DataFrame) -> Recorte:
    padrao = _padrao(tit)
    if "flt" not in st.session_state:
        st.session_state.flt = _da_url(padrao)
    f = st.session_state.flt

    _iniciar("w_periodo", tuple(f["periodo"]))
    _iniciar("w_nivel", list(f["nivel"]))
    _iniciar("w_linha", list(f["linha"]))
    _iniciar("w_orientador", list(f["orientador"]))
    _iniciar("w_area", list(f["area"]))

    with st.container(key="barra-filtros"):
        c1, c2, c3, c4, c5 = st.columns([3.2, 2.0, 3.4, 1.5, 0.9], vertical_alignment="bottom")
        c1.slider("Ano de defesa", padrao["periodo"][0], padrao["periodo"][1], key="w_periodo")
        c2.pills("Nível", ORDEM_NIVEL, selection_mode="multi", key="w_nivel")
        c3.multiselect("Linha de pesquisa", [s for s in ORDEM_LINHAS], key="w_linha",
                       format_func=lambda s: NOME_LINHA[s], placeholder="Todas as linhas")
        with c4.popover("Mais filtros", use_container_width=True):
            orient = sorted(tit["ORIENTADOR"].dropna().unique())
            if st.session_state.w_linha:   # orientadores das linhas escolhidas
                orient = sorted(tit.loc[tit["LINHA_SIGLA"].isin(st.session_state.w_linha),
                                        "ORIENTADOR"].dropna().unique())
            st.session_state.w_orientador = [o for o in st.session_state.w_orientador if o in orient]
            st.multiselect("Orientador(a)", orient, key="w_orientador", placeholder="Todos")
            st.multiselect("Área da graduação", sorted(tit["AREA_GRADUACAO"].dropna().unique()),
                           key="w_area", placeholder="Todas")
        c5.button("Limpar", on_click=limpar, use_container_width=True, type="tertiary")

    f = {"periodo": tuple(st.session_state.w_periodo),
         "nivel": list(st.session_state.w_nivel) or list(ORDEM_NIVEL),
         "linha": list(st.session_state.w_linha),
         "orientador": list(st.session_state.w_orientador),
         "area": list(st.session_state.w_area)}
    st.session_state.flt = f
    _para_url(f, padrao)

    t = tit[tit["ANO"].between(*f["periodo"]) & tit["NIVEL"].isin(f["nivel"])]
    if f["linha"]:
        t = t[t["LINHA_SIGLA"].isin(f["linha"])]
    if f["orientador"]:
        t = t[t["ORIENTADOR"].isin(f["orientador"])]
    if f["area"]:
        t = t[t["AREA_GRADUACAO"].isin(f["area"])]
    p = pes[pes["ID_PESSOA"].isin(t["ID_PESSOA"])]

    ativo = f != {**padrao, "periodo": tuple(padrao["periodo"])}
    partes = [f"{f['periodo'][0]}–{f['periodo'][1]}"]
    if set(f["nivel"]) != set(ORDEM_NIVEL):
        partes.append(" e ".join(f["nivel"]).lower())
    if f["linha"]:
        partes.append(", ".join(f["linha"]))
    if f["orientador"]:
        partes.append(f"{len(f['orientador'])} orientador(es)")
    if f["area"]:
        partes.append(f"{len(f['area'])} área(s) de graduação")
    desc = " · ".join(partes)
    st.markdown(
        f'<div class="recorte"><span>Recorte: {desc}</span>'
        f'<span><b>{num(len(t))}</b> titulações · <b>{num(len(p))}</b> pessoas</span></div>',
        unsafe_allow_html=True)
    return Recorte(t, p, ativo, desc)
