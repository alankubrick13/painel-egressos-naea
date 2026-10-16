"""Formação: linhas de pesquisa, níveis, trajetórias e temas dos trabalhos."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import charts, data, filters, stats
from core import components as ui
from core.theme import COR_LINHA, COR_NIVEL, NOME_LINHA, ORDEM_LINHAS, VERDE_NAEA, num, pct

r = filters.barra(data.titulacoes(), data.pessoas())
t, p = r.titulacoes, r.pessoas
if t.empty:
    st.info("Nenhuma titulação no recorte escolhido. Ajuste os filtros ou use **Limpar**.")
    st.stop()

ORDEM_PER = ["Antes de 1998", "1998–2000", "2001–2003", "2004–2006", "2007–2009", "2010–2012",
             "2013–2016", "2017–2020", "2021–2024"]

# ====================================================================== indicadores
ambos = p[p["TRAJETORIA"] == "Mestrado e doutorado"]
gap = ambos["ANOS_MESTRADO_DOUTORADO"].dropna()
st.html('<div style="height:10px"></div>')
ui.indicadores([
    ("Dissertações de mestrado", num((t["NIVEL"] == "Mestrado").sum()), "desde 1981"),
    ("Teses de doutorado", num((t["NIVEL"] == "Doutorado").sum()), "desde 1999"),
    ("Fizeram mestrado e doutorado aqui", num(len(ambos)), f"{pct(len(ambos) / max(len(p), 1), 0)} das pessoas"),
    ("Intervalo mestrado → doutorado", f"{num(gap.median(), 0)} anos" if len(gap) else "–",
     "mediana, para quem fez os dois no programa"),
    ("Linha com mais titulações", t["LINHA_SIGLA"].replace("N/I", pd.NA).mode().iloc[0]
     if t["LINHA_SIGLA"].ne("N/I").any() else "–",
     NOME_LINHA.get(t["LINHA_SIGLA"].replace("N/I", pd.NA).mode().iloc[0], "")
     if t["LINHA_SIGLA"].ne("N/I").any() else ""),
    ("Sem linha de pesquisa", num((t["LINHA_SIGLA"] == "N/I").sum()), "trabalhos sem linha registrada ou atribuível"),
])

# ====================================================================== linhas no tempo
ui.secao("Linhas de pesquisa",
         "O PPGDSTU organiza-se em quatro linhas. A composição mudou ao longo dos períodos de avaliação "
         "da CAPES.")
tab = t.groupby(["PERIODO_CAPES", "LINHA_SIGLA"]).size().unstack(fill_value=0)
tab = tab.reindex([p_ for p_ in ORDEM_PER if p_ in tab.index])
share = tab.div(tab.sum(axis=1), axis=0)
validos = tab.index[tab.sum(axis=1) >= 10]
titulo = "Composição das titulações por linha de pesquisa em cada período"
if len(validos) >= 2:
    ini, fim = validos[0], validos[-1]
    var = (share.loc[fim] - share.loc[ini]).drop("N/I", errors="ignore")
    if len(var):
        s = var.idxmax()
        titulo = (f"{NOME_LINHA[s]} foi a linha que mais ganhou espaço: de {pct(share.loc[ini, s], 0)} "
                  f"({ini.replace('Antes', 'antes')}) para {pct(share.loc[fim, s], 0)} ({fim})")
fig = charts.colunas_100(tab, COR_LINHA, NOME_LINHA, ordem=ORDEM_LINHAS, altura=360)
ui.grafico(fig, titulo, "Participação de cada linha nas titulações, por período de avaliação da CAPES",
           "Fonte: quadro geral de egressos do PPGDSTU e titulados registrados pela CAPES. “Desenvolvimento Regional "
           "e Agrário” (nome antigo) somada a “Desenvolvimento Econômico, Regional e Agrário”. Nas titulações "
           "vindas da CAPES, a linha é a predominante do orientador.",
           tab.rename(columns=NOME_LINHA).reset_index().rename(columns={"PERIODO_CAPES": "Período"}),
           chave="linhas-tempo")

c1, c2 = st.columns(2, gap="medium")
with c1:
    nv = t.groupby(["LINHA_SIGLA", "NIVEL"]).size().unstack(fill_value=0).reindex(
        [s for s in ORDEM_LINHAS if s in t["LINHA_SIGLA"].unique()])
    nv = nv.reindex(columns=["Mestrado", "Doutorado"], fill_value=0)
    nv.index = [NOME_LINHA[s] for s in nv.index]
    fig = charts.colunas_100(nv, COR_NIVEL, {"Mestrado": "Dissertações", "Doutorado": "Teses"},
                             horizontal=True, altura=max(260, 62 * len(nv) + 70), largura_rotulo=28)
    dout = (nv["Doutorado"] / nv.sum(axis=1)).drop("Não informada", errors="ignore")
    tit = (f"{dout.idxmax()} é a linha mais voltada ao doutorado: {pct(dout.max(), 0)} são teses"
           if len(dout) else "Dissertações e teses por linha")
    ui.grafico(fig, tit, "Participação de dissertações e teses em cada linha",
               "“Não informada”: trabalhos sem linha registrada na planilha nem orientador com linha definida.",
               nv.rename(columns={"Mestrado": "Dissertações", "Doutorado": "Teses"}).reset_index()
               .rename(columns={"index": "Linha"}), chave="linha-nivel")
with c2:
    tr = p["TRAJETORIA"].value_counts().reindex(["Somente mestrado", "Somente doutorado",
                                                  "Mestrado e doutorado"]).dropna()
    fig = charts.barras_h(tr.index, tr.values, total=tr.sum(), largura_rotulo=22)
    ui.grafico(fig, f"{pct(tr.get('Somente mestrado', 0) / max(tr.sum(), 1), 0)} das pessoas fizeram só o "
                    "mestrado no programa",
               "Trajetória de cada pessoa dentro do PPGDSTU",
               "Cada pessoa conta uma vez. “Somente doutorado”: o mestrado foi feito em outro programa.",
               pd.DataFrame({"Trajetória": tr.index, "Pessoas": tr.values}), chave="trajetoria")

if len(gap) >= 5:
    h = gap.astype(int).value_counts().sort_index()
    h = h.reindex(range(int(h.index.min()), int(h.index.max()) + 1), fill_value=0)
    fig = charts.histograma(h, rotulo_x="anos entre a dissertação e a tese")
    fig.update_layout(xaxis=dict(dtick=2))
    ui.grafico(fig, f"Metade de quem fez os dois níveis no programa defendeu a tese até {num(gap.median(), 0)} "
                    f"anos depois da dissertação",
               f"Anos entre a dissertação e a tese ({num(len(gap))} pessoas)",
               "Diferença entre os anos de defesa registrados na planilha.",
               pd.DataFrame({"Anos": h.index, "Pessoas": h.values}), chave="intervalo")

# ====================================================================== temas
ui.secao("Temas dos trabalhos",
         "Palavras e expressões que mais distinguem os títulos de cada grupo em relação aos demais "
         "(log-odds com prior de Dirichlet informativo). Não são as mais frequentes, e sim as mais "
         "características de cada grupo.")


def periodo_tema(a):
    return "Até 1999" if a < 2000 else ("2000–2009" if a < 2010 else ("2010–2019" if a < 2020 else "Desde 2020"))


def painel_termos(grupos, colunas=2, cores=None):
    tm = stats.termos_distintivos(tuple((g, tuple(tits)) for g, tits in grupos))
    if tm.empty:
        st.caption("Títulos insuficientes no recorte para comparar grupos.")
        return
    cols = st.columns(colunas, gap="medium")
    for i, (g, _) in enumerate(grupos):
        x = tm[tm["GRUPO"] == g].head(10)
        if x.empty:
            continue
        cor = (cores or {}).get(g, VERDE_NAEA)
        fig = go.Figure(go.Bar(
            x=x["Z"], y=x["TERMO"], orientation="h", marker=dict(color=cor, line=charts.GAP),
            customdata=x["FREQ"], text=[f"{f}×" for f in x["FREQ"]], textposition="outside",
            textfont=dict(size=11.5, color="#55574F"), cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>aparece em %{customdata} títulos<extra></extra>"))
        fig.update_layout(height=330, showlegend=False, bargap=0.32,
                          xaxis=dict(visible=False, range=[0, x["Z"].max() * 1.25]),
                          yaxis=dict(autorange="reversed", showgrid=False, ticklabelstandoff=8),
                          margin=dict(l=4, r=8, t=4, b=4))
        n_tit = len(dict(grupos)[g])
        with cols[i % colunas]:
            ui.grafico(fig, g, f"{num(n_tit)} títulos · número ao lado = em quantos títulos o termo aparece",
                       "Fonte: títulos das dissertações e teses.", x[["TERMO", "FREQ", "Z"]].rename(
                           columns={"TERMO": "Termo", "FREQ": "Títulos", "Z": "Força distintiva (z)"}),
                       chave=f"termos-{g}")


aba_p, aba_l = st.tabs(["Por período", "Por linha de pesquisa"])
with aba_p:
    per = t["ANO"].map(periodo_tema)
    grupos = [(g, list(t.loc[per == g, "TRABALHO_CONCLUSAO"])) for g in
              ["Até 1999", "2000–2009", "2010–2019", "Desde 2020"] if (per == g).sum() >= 15]
    painel_termos(grupos)
with aba_l:
    grupos = [(NOME_LINHA[s], list(t.loc[t["LINHA_SIGLA"] == s, "TRABALHO_CONCLUSAO"]))
              for s in ORDEM_LINHAS[:4] if (t["LINHA_SIGLA"] == s).sum() >= 15]
    painel_termos(grupos, cores={NOME_LINHA[s]: COR_LINHA[s] for s in ORDEM_LINHAS[:4]})
