"""Orientação: quem orientou, quanto, em que linha e por quanto tempo."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import charts, data, filters
from core import components as ui
from core.theme import (COR_LINHA, COR_NIVEL, GRADE, NOME_LINHA, ORDEM_LINHAS, SUPERFICIE,
                        num, pct)

r = filters.barra(data.titulacoes(), data.pessoas())
t = r.titulacoes
if t.empty:
    st.info("Nenhuma titulação no recorte escolhido. Ajuste os filtros ou use **Limpar**.")
    st.stop()

o = t.groupby("ORIENTADOR").agg(
    TOTAL=("ID_REGISTRO", "size"),
    DISSERTACOES=("NIVEL", lambda s: int((s == "Mestrado").sum())),
    TESES=("NIVEL", lambda s: int((s == "Doutorado").sum())),
    PRIMEIRO=("ANO", "min"), ULTIMO=("ANO", "max"),
    LINHA=("LINHA_SIGLA", lambda s: (s[s != "N/I"].mode().iloc[0] if (s != "N/I").any() else "N/I")),
).sort_values("TOTAL", ascending=False)
o["ANOS_ATIVIDADE"] = o["ULTIMO"] - o["PRIMEIRO"] + 1
top10 = o["TOTAL"].head(10).sum() / o["TOTAL"].sum()
um = int((o["TOTAL"] == 1).sum())

st.html('<div style="height:10px"></div>')
ui.indicadores([
    ("Orientadores(as)", num(len(o)), "com ao menos uma orientação no recorte"),
    ("Orientações por orientador(a)", num(o["TOTAL"].median(), 0), f"mediana; média de {num(o['TOTAL'].mean(), 1)}"),
    ("Os 10 mais frequentes", pct(top10, 0), "das orientações do recorte"),
    ("Orientaram uma única vez", num(um), f"{pct(um / len(o), 0)} dos orientadores"),
])

# ====================================================================== ranking
ui.secao("Quem mais orientou")
top = o.head(20)
fig = go.Figure()
for nivel, col, nome in [("Mestrado", "DISSERTACOES", "Dissertações"), ("Doutorado", "TESES", "Teses")]:
    fig.add_bar(y=top.index, x=top[col], name=nome, orientation="h",
                marker=dict(color=COR_NIVEL[nivel], line=charts.GAP),
                hovertemplate=f"<b>%{{x}}</b> {nome.lower()}<extra></extra>")
fig.add_trace(go.Scatter(y=top.index, x=top["TOTAL"], mode="text", text=[num(v) for v in top["TOTAL"]],
                         textposition="middle right", textfont=dict(size=12, color="#55574F"),
                         showlegend=False, hoverinfo="skip"))
fig.update_layout(barmode="stack", height=22 * len(top) + 90, bargap=0.3, hovermode="y unified",
                  legend=dict(y=1.02, traceorder="normal"),
                  yaxis=dict(autorange="reversed", showgrid=False, ticklabelstandoff=8),
                  xaxis=dict(showgrid=True, gridcolor=GRADE, showline=False, range=[0, top["TOTAL"].max() * 1.12]),
                  margin=dict(l=4, r=8, t=34, b=4))
ui.grafico(fig, f"{top.index[0]} é quem mais orientou: {num(top['TOTAL'].iloc[0])} trabalhos "
                f"({num(top['TESES'].iloc[0])} teses)",
           "Os 20 orientadores com mais dissertações e teses no recorte",
           "Fonte: quadro geral de egressos do PPGDSTU. Grafias do mesmo nome unificadas.",
           o.reset_index().rename(columns={"ORIENTADOR": "Orientador(a)", "TOTAL": "Total",
                                           "DISSERTACOES": "Dissertações", "TESES": "Teses",
                                           "PRIMEIRO": "Primeira defesa", "ULTIMO": "Última defesa",
                                           "LINHA": "Linha principal", "ANOS_ATIVIDADE": "Anos de atividade"}),
           chave="ranking")

c1, c2 = st.columns(2, gap="medium")
with c1:
    faixas = pd.cut(o["TOTAL"], [0, 1, 5, 10, 20, 1000], labels=["1", "2 a 5", "6 a 10", "11 a 20", "Mais de 20"])
    fx = faixas.value_counts().reindex(["1", "2 a 5", "6 a 10", "11 a 20", "Mais de 20"])
    orient_fx = o.groupby(faixas, observed=False)["TOTAL"].sum().reindex(fx.index)
    fig = charts.barras_h([f"{i} orientação" if i == "1" else f"{i} orientações" for i in fx.index],
                          fx.values, total=fx.sum(), largura_rotulo=20)
    grandes = o["TOTAL"] > 20
    ui.grafico(fig, f"{num(grandes.sum())} orientadores com mais de 20 trabalhos respondem por "
                    f"{pct(o.loc[grandes, 'TOTAL'].sum() / o['TOTAL'].sum(), 0)} das orientações",
               "Orientadores por número de orientações no recorte",
               "Cada orientador(a) conta uma vez.",
               pd.DataFrame({"Faixa": fx.index, "Orientadores": fx.values, "Orientações": orient_fx.values}),
               chave="faixas")
with c2:
    pl = o["LINHA"].value_counts().reindex(ORDEM_LINHAS).dropna().astype(int)
    pl = pl[pl > 0]
    fig = charts.barras_h([NOME_LINHA[s] for s in pl.index], pl.values, total=pl.sum(), largura_rotulo=30)
    fig.data[0].marker.color = [COR_LINHA[s] for s in pl.index]
    ui.grafico(fig, f"{NOME_LINHA[pl.idxmax()]} reúne o maior grupo de orientadores ({num(pl.max())})",
               "Orientadores pela linha em que mais orientaram",
               "Quase todo orientador atua numa única linha; aqui vale a linha predominante.",
               pd.DataFrame({"Linha": [NOME_LINHA[s] for s in pl.index], "Orientadores": pl.values}),
               chave="orient-linha")

# ====================================================================== trajetórias no tempo
ui.secao("Trajetórias de orientação",
         "Período de atividade dos 25 orientadores com mais trabalhos: o traço vai da primeira à última defesa; "
         "cada círculo é um ano com defesas, maior quanto mais trabalhos.")
top25 = o.head(25)
anual = t[t["ORIENTADOR"].isin(top25.index)].groupby(["ORIENTADOR", "ANO"]).size().reset_index(name="N")
fig = go.Figure()
for nome, row in top25.iterrows():
    fig.add_trace(go.Scatter(x=[row["PRIMEIRO"], row["ULTIMO"]], y=[nome, nome], mode="lines",
                             line=dict(color=GRADE, width=3), hoverinfo="skip", showlegend=False))
for s in [x for x in ORDEM_LINHAS if x in set(top25["LINHA"])]:
    nomes = top25.index[top25["LINHA"] == s]
    a = anual[anual["ORIENTADOR"].isin(nomes)]
    fig.add_trace(go.Scatter(
        x=a["ANO"], y=a["ORIENTADOR"], mode="markers", name=NOME_LINHA[s],
        marker=dict(size=np.sqrt(a["N"]) * 7 + 3, color=COR_LINHA[s], line=dict(color=SUPERFICIE, width=1.5)),
        customdata=a["N"], hovertemplate="<b>%{customdata}</b> defesas em %{x}<br>%{y}<extra></extra>"))
fig.update_layout(height=26 * len(top25) + 90, hovermode="closest",
                  legend=dict(y=1.01, traceorder="normal", itemsizing="constant"),
                  yaxis=dict(autorange="reversed", showgrid=False, ticklabelstandoff=8, categoryorder="array",
                             categoryarray=list(top25.index)),
                  xaxis=dict(showgrid=True, gridcolor=GRADE, dtick=5, tickformat="d", showline=False),
                  margin=dict(l=4, r=8, t=34, b=4))
longo = top25["ANOS_ATIVIDADE"].idxmax()
ui.grafico(fig, f"{longo} tem a trajetória mais longa entre os que mais orientaram: "
                f"{num(top25.loc[longo, 'ANOS_ATIVIDADE'])} anos ({top25.loc[longo, 'PRIMEIRO']}–"
                f"{top25.loc[longo, 'ULTIMO']})",
           "Anos com defesas de cada orientador(a), cor pela linha predominante",
           "Fonte: quadro geral de egressos do PPGDSTU.",
           anual.rename(columns={"ORIENTADOR": "Orientador(a)", "ANO": "Ano", "N": "Defesas"}), chave="timeline")

# ====================================================================== consulta
ui.secao("Todos os orientadores")
busca = st.text_input("Buscar orientador(a)", placeholder="Digite parte do nome", key="busca_orient",
                      label_visibility="collapsed")
tab = o.reset_index()
if busca:
    tab = tab[tab["ORIENTADOR"].str.contains(busca, case=False, regex=False)]
st.dataframe(
    tab.assign(LINHA=tab["LINHA"].map(NOME_LINHA)).rename(columns={
        "ORIENTADOR": "Orientador(a)", "TOTAL": "Total", "DISSERTACOES": "Dissertações", "TESES": "Teses",
        "PRIMEIRO": "Primeira defesa", "ULTIMO": "Última defesa", "LINHA": "Linha principal",
        "ANOS_ATIVIDADE": "Anos de atividade"}),
    hide_index=True, use_container_width=True, height=380,
    column_config={"Total": st.column_config.ProgressColumn("Total", format="%d", min_value=0,
                                                            max_value=int(o["TOTAL"].max()), color="#00742A"),
                   "Primeira defesa": st.column_config.NumberColumn(format="%d"),
                   "Última defesa": st.column_config.NumberColumn(format="%d")})
