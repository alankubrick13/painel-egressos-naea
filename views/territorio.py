"""Território: onde atuam os egressos, do Brasil ao município paraense."""
import pandas as pd
import streamlit as st

from core import charts, data, filters
from core import components as ui
from core.theme import num, pct

AMAZONIA_LEGAL = ["AC", "AP", "AM", "MA", "MT", "PA", "RO", "RR", "TO"]

r = filters.barra(data.titulacoes(), data.pessoas())
p = r.pessoas
if p.empty:
    st.info("Nenhuma pessoa no recorte escolhido. Ajuste os filtros ou use **Limpar**.")
    st.stop()

com_uf = p[p["UF_ATUACAO"].notna()]
com_mun = p[p["LAT"].notna()]
n_uf = len(com_uf)
pa = com_uf["UF_ATUACAO"].eq("PA").sum()

st.html('<div style="height:10px"></div>')
ui.indicadores([
    ("Atuam no Pará", pct(pa / max(n_uf, 1), 0), f"{num(pa)} pessoas"),
    ("Na região Norte", pct(com_uf["REGIAO"].eq("Norte").mean(), 0), "entre quem tem local conhecido"),
    ("Na Amazônia Legal", pct(com_uf["AMAZONIA_LEGAL"].eq("Sim").mean(), 0), "nove estados"),
    ("Estados com egressos", num(com_uf["UF_ATUACAO"].nunique()), "de 27 unidades da federação"),
    ("Municípios com egressos", num(com_mun["MUNICIPIO_ATUACAO"].nunique()), "com município identificado"),
    ("Local conhecido", pct(n_uf / max(len(p), 1), 0), f"{num(n_uf)} de {num(len(p))} pessoas"),
])
ui.ressalva(f"O local é conhecido para {pct(n_uf / max(len(p), 1), 0)} dos egressos. Quem atua fora do serviço "
            "público é mais difícil de localizar, então os mapas tendem a superestimar a permanência na rede "
            "pública amazônica. Ordem de preferência: município declarado no Lattes; UF de exercício no SIAPE; "
            "sede da instituição.")

# ====================================================================== Brasil
ui.secao("Brasil")
c1, c2 = st.columns([1.25, 1], gap="medium")
cont_uf = com_uf["UF_ATUACAO"].value_counts()
with c1:
    fig = charts.mapa_uf(cont_uf, data.malha_uf(), n_uf)
    fig.update_layout(height=470)
    ui.grafico(fig, f"{pct(pa / max(n_uf, 1), 0)} dos egressos com local conhecido atuam no Pará",
               f"Egressos por unidade da federação ({num(n_uf)} pessoas)",
               "Escala logarítmica: cada tom mais escuro corresponde a cerca de três vezes mais egressos.",
               pd.DataFrame({"UF": cont_uf.index, "Pessoas": cont_uf.values,
                             "%": (cont_uf.values / max(n_uf, 1) * 100).round(1)}), chave="mapa-uf")
with c2:
    fora = cont_uf.drop("PA", errors="ignore").head(12)
    fig = charts.barras_h(fora.index, fora.values, total=n_uf, largura_rotulo=10)
    ui.grafico(fig, f"Fora do Pará, {fora.index[0]} recebe mais egressos ({num(fora.iloc[0])})" if len(fora)
               else "Egressos fora do Pará", "As 12 UFs com mais egressos, excluído o Pará",
               "Percentual sobre o total com local conhecido.",
               pd.DataFrame({"UF": fora.index, "Pessoas": fora.values}), chave="ufs-fora")

mun = (com_mun.groupby(["MUNICIPIO_ATUACAO", "UF_ATUACAO", "LAT", "LON"]).size().reset_index(name="N")
       .rename(columns={"MUNICIPIO_ATUACAO": "MUNICIPIO", "UF_ATUACAO": "UF"}).sort_values("N", ascending=False))
c3, c4 = st.columns([1.25, 1], gap="medium")
with c3:
    fig = charts.mapa_bolhas(mun, data.malha_uf(), destaque_ufs=AMAZONIA_LEGAL, altura=520)
    lider = mun.iloc[0]
    ui.grafico(fig, f"Os egressos estão em {num(len(mun))} municípios; {lider['MUNICIPIO']} reúne "
                    f"{pct(lider['N'] / mun['N'].sum(), 0)}",
               "Egressos por município de atuação (área do círculo proporcional; Amazônia Legal em verde-claro)",
               "Municípios identificados pelo Lattes, pelo campus no SIAPE ou pela sede da instituição.",
               mun[["MUNICIPIO", "UF", "N"]].rename(columns={"MUNICIPIO": "Município", "N": "Pessoas"}),
               chave="mapa-municipios")
with c4:
    top = mun.head(15)
    fig = charts.barras_h([f"{m} ({u})" for m, u in zip(top["MUNICIPIO"], top["UF"])], top["N"].values,
                          total=mun["N"].sum(), largura_rotulo=24)
    seguintes = mun.iloc[1:4]["MUNICIPIO"].tolist()
    tit_top = (f"Depois de {mun.iloc[0]['MUNICIPIO']}, os principais destinos são "
               + ", ".join(seguintes[:-1]) + f" e {seguintes[-1]}" if len(seguintes) >= 2
               else "Municípios com mais egressos")
    ui.grafico(fig, tit_top,
               "Os 15 municípios com mais egressos",
               "Percentual sobre os egressos com município identificado.",
               mun[["MUNICIPIO", "UF", "N"]].rename(columns={"MUNICIPIO": "Município", "N": "Pessoas"}),
               chave="top-municipios")

# ====================================================================== Amazônia Legal e regiões
c5, c6 = st.columns(2, gap="medium")
with c5:
    am = com_uf[com_uf["UF_ATUACAO"].isin(AMAZONIA_LEGAL)]["UF_ATUACAO"].value_counts()
    fig = charts.barras_h(am.index, am.values, total=am.sum(), largura_rotulo=8)
    ui.grafico(fig, f"Na Amazônia Legal, {num(am.size)} dos 9 estados têm egressos",
               "Egressos por estado da Amazônia Legal",
               "Maranhão incluído integralmente.",
               pd.DataFrame({"UF": am.index, "Pessoas": am.values}), chave="amazonia")
with c6:
    reg = com_uf["REGIAO"].value_counts()
    fig = charts.barras_h(reg.index, reg.values, total=reg.sum(), largura_rotulo=14)
    ui.grafico(fig, f"{pct(reg.get('Norte', 0) / max(reg.sum(), 1), 0)} permanecem na região Norte",
               "Egressos por grande região", "Mesma base do mapa por UF.",
               pd.DataFrame({"Região": reg.index, "Pessoas": reg.values}), chave="regioes")

# ====================================================================== Pará
ui.secao("Pará", "Municípios paraenses com egressos e as regiões geográficas intermediárias do IBGE.")
no_pa = com_mun[com_mun["UF_ATUACAO"] == "PA"]
if len(no_pa):
    cont_mun = no_pa.groupby("COD_MUNICIPIO").size()
    cont_mun.index = cont_mun.index.astype(int)
    c7, c8 = st.columns([1.35, 1], gap="medium")
    with c7:
        bol = (no_pa.groupby(["MUNICIPIO_ATUACAO", "LAT", "LON"]).size().reset_index(name="N")
               .rename(columns={"MUNICIPIO_ATUACAO": "MUNICIPIO"}))
        fig = charts.mapa_municipios(cont_mun, data.malha_pa(), altura=560, bolhas=bol)
        fora_belem = no_pa[no_pa["MUNICIPIO_ATUACAO"] != "Belém"]["MUNICIPIO_ATUACAO"].value_counts()
        tit = (f"Egressos em {num(len(cont_mun))} municípios paraenses; fora da capital, destacam-se "
               + " e ".join(fora_belem.index[:2]) if len(fora_belem) >= 2
               else f"Egressos em {num(len(cont_mun))} municípios paraenses")
        ui.grafico(fig, tit, f"Egressos por município do Pará ({num(len(no_pa))} pessoas com município)",
                   "Malha municipal: IBGE. Cor em escala logarítmica; círculos proporcionais ao número de egressos; "
                   "municípios sem egressos em cinza.",
                   no_pa["MUNICIPIO_ATUACAO"].value_counts().rename_axis("Município").reset_index(name="Pessoas"),
                   chave="mapa-pa")
    with c8:
        ri = no_pa["REGIAO_INTERMEDIARIA"].value_counts()
        fig = charts.barras_h([f"Região de {x}" for x in ri.index], ri.values, total=ri.sum(), largura_rotulo=26)
        interior = 1 - ri.get("Belém", 0) / max(ri.sum(), 1)
        ui.grafico(fig, f"{pct(interior, 0)} dos egressos no Pará atuam fora da região intermediária de Belém",
                   "Egressos por região geográfica intermediária (IBGE, 2017)",
                   "As regiões intermediárias agrupam municípios em torno de um polo urbano.",
                   pd.DataFrame({"Região intermediária": ri.index, "Pessoas": ri.values}), chave="regiao-int")
        interior_mun = no_pa[no_pa["MUNICIPIO_ATUACAO"] != "Belém"]["MUNICIPIO_ATUACAO"].value_counts().head(10)
        if len(interior_mun):
            fig = charts.barras_h(interior_mun.index, interior_mun.values, largura_rotulo=20)
            ui.grafico(fig, f"{interior_mun.index[0]} lidera no interior paraense",
                       "Os 10 municípios do Pará com mais egressos, exceto Belém",
                       "Inclui campi de universidades e institutos federais.",
                       interior_mun.rename_axis("Município").reset_index(name="Pessoas"), chave="interior-pa")
