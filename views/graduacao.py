"""Graduação: de onde vêm os egressos e como a origem se liga à linha e ao destino."""
import pandas as pd
import streamlit as st

from core import charts, data, filters
from core import components as ui
from core.theme import COR_LINHA, NOME_LINHA, ORDEM_LINHAS, VERDE_NAEA, num, pct

r = filters.barra(data.titulacoes(), data.pessoas())
t, p_todos = r.titulacoes, r.pessoas
p = p_todos[p_todos["AREA_GRADUACAO"].notna()]          # quem entrou pela CAPES não tem graduação registrada
sem_grad = len(p_todos) - len(p)
if p.empty:
    st.info("Nenhuma pessoa no recorte escolhido. Ajuste os filtros ou use **Limpar**.")
    st.stop()

area = p["AREA_GRADUACAO"].value_counts()
curso = p["GRADUACAO"].value_counts()
sociais = area.get("Ciências Sociais Aplicadas", 0) + area.get("Ciências Humanas", 0)

st.html('<div style="height:10px"></div>')
ui.indicadores([
    ("Cursos de graduação de origem", num(curso.size), f"em {num(area.size)} grandes áreas"),
    ("Curso mais comum", curso.index[0], f"{pct(curso.iloc[0] / curso.sum(), 0)} dos egressos"),
    ("Ciências Sociais Aplicadas e Humanas", pct(sociais / area.sum(), 0), "das pessoas tituladas"),
    ("Demais áreas", pct(1 - sociais / area.sum(), 0),
     "Agrárias, Biológicas, Saúde, Engenharias, Exatas e outras"),
])

# ====================================================================== áreas e cursos
ui.secao("Formação de origem",
         "Curso de graduação de cada egresso, agrupado nas grandes áreas do conhecimento. Fonte: planilha do "
         "programa; para quem entrou na base pelos registros da CAPES, o Currículo Lattes consultado no "
         f"Escavador ({num(p['GRADUACAO_FONTE'].eq('Escavador (Currículo Lattes)').sum())} pessoas) ou a "
         f"informação da coordenação ({num(p['GRADUACAO_FONTE'].eq('Informado pela coordenação').sum())})."
         + (f" {num(sem_grad)} pessoas ainda sem graduação conhecida ficam fora desta página." if sem_grad else ""))
c1, c2 = st.columns(2, gap="medium")
with c1:
    fig = charts.barras_h(area.index, area.values, total=area.sum(), largura_rotulo=26)
    ui.grafico(fig, f"{pct(sociais / area.sum(), 0)} vêm das Ciências Sociais Aplicadas e Humanas",
               "Pessoas por grande área da graduação",
               "Agrupamento simplificado da tabela de áreas da CAPES.",
               pd.DataFrame({"Área": area.index, "Pessoas": area.values,
                             "%": (area.values / area.sum() * 100).round(1)}), chave="areas")
with c2:
    top = curso.head(15)
    fig = charts.barras_h(top.index, top.values, total=curso.sum(), largura_rotulo=26)
    ui.grafico(fig, f"{top.index[0]} é o curso de origem mais comum, com {pct(top.iloc[0] / curso.sum(), 0)}",
               f"Os 15 cursos mais frequentes, entre {num(curso.size)}",
               "Grafias unificadas (ex.: “Ciencias Sociais” e “CIências Sociais”).",
               pd.DataFrame({"Curso": curso.index, "Pessoas": curso.values}), chave="cursos")

# ====================================================================== área x linha
ui.secao("Origem e linha de pesquisa")
cruz = pd.crosstab(p["AREA_GRADUACAO"], p["LINHA_SIGLA"])
cruz = cruz.reindex(columns=[s for s in ORDEM_LINHAS[:4] if s in cruz.columns])
cruz = cruz[cruz.sum(axis=1) >= 8]
if not cruz.empty and cruz.shape[1] >= 2:
    lin_pct = cruz.div(cruz.sum(axis=1), axis=0) * 100
    lin_pct = lin_pct.loc[cruz.sum(axis=1).sort_values(ascending=False).index]
    maior = lin_pct.max(axis=1)
    a_ = maior[cruz.sum(axis=1).reindex(maior.index) >= 15].idxmax() if (cruz.sum(axis=1) >= 15).any() else maior.idxmax()
    s_ = lin_pct.loc[a_].idxmax()
    z = lin_pct.rename(columns=NOME_LINHA)
    z.index = [f"{i} ({num(cruz.sum(axis=1)[i])})" for i in z.index]
    fig = charts.mapa_calor(z, largura_x=22, largura_y=34)
    ui.grafico(fig, f"Quem vem de {a_} concentra-se em {NOME_LINHA[s_]} ({num(lin_pct.loc[a_, s_], 0)}%)",
               "Distribuição dos egressos de cada área de graduação entre as linhas de pesquisa "
               "(% da linha; entre parênteses, o número de pessoas)",
               "Áreas com pelo menos 8 pessoas no recorte. Linha: a da titulação mais recente.",
               lin_pct.round(1).rename(columns=NOME_LINHA).reset_index().rename(
                   columns={"AREA_GRADUACAO": "Área da graduação"}), chave="area-linha")

# ====================================================================== fluxo
ui.secao("Da graduação ao destino",
         "Cada faixa liga a área de graduação à linha de pesquisa cursada e ao setor de atuação declarado "
         "no Currículo Lattes. A largura é proporcional ao número de pessoas.")
f = p[p["LINHA_SIGLA"].isin(ORDEM_LINHAS[:4]) & p["SETOR_LATTES"].notna()].copy()
if len(f) >= 20:
    principais = f["AREA_GRADUACAO"].value_counts()
    principais = principais[principais >= 15].index
    f["A"] = f["AREA_GRADUACAO"].where(f["AREA_GRADUACAO"].isin(principais), "Outras áreas")
    setores = f["SETOR_LATTES"].value_counts()
    f["S"] = f["SETOR_LATTES"].where(f["SETOR_LATTES"].isin(setores[setores >= 15].index), "Outros setores")
    a_nos = list(f["A"].value_counts().index)
    l_nos = [s for s in ORDEM_LINHAS[:4] if s in set(f["LINHA_SIGLA"])]
    s_nos = list(f["S"].value_counts().index)
    rot = a_nos + [NOME_LINHA[s] for s in l_nos] + s_nos
    idx = {("A", a): i for i, a in enumerate(a_nos)}
    idx.update({("L", s): len(a_nos) + i for i, s in enumerate(l_nos)})
    idx.update({("S", s): len(a_nos) + len(l_nos) + i for i, s in enumerate(s_nos)})
    cores_nos = (["#8A877F"] * len(a_nos) + [COR_LINHA[s] for s in l_nos] + [VERDE_NAEA] * len(s_nos))

    def rgba(h, a=0.32):
        h = h.lstrip("#")
        return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"

    ligacoes = ([(idx[("A", a)], idx[("L", s)], int(n), s)
                 for (a, s), n in f.groupby(["A", "LINHA_SIGLA"]).size().items()]
                + [(idx[("L", s)], idx[("S", d)], int(n), s)
                   for (s, d), n in f.groupby(["LINHA_SIGLA", "S"]).size().items()])
    fig = charts.sankey(rot, cores_nos, [x[0] for x in ligacoes], [x[1] for x in ligacoes],
                        [x[2] for x in ligacoes], [rgba(COR_LINHA[x[3]]) for x in ligacoes], altura=560)
    esp = f.groupby("LINHA_SIGLA")["SETOR_LATTES"].apply(lambda s: (s == "Ensino Superior Público").mean())
    moda = f.groupby("LINHA_SIGLA")["SETOR_LATTES"].agg(lambda s: s.mode().iloc[0])
    titulo = (f"Em todas as linhas, o ensino superior público é o principal destino "
              f"({pct(esp.min(), 0)} a {pct(esp.max(), 0)} dos egressos)"
              if (moda == "Ensino Superior Público").all()
              else f"Da graduação ao destino: o percurso de {num(len(f))} egressos")
    tabela = (f.groupby(["A", "LINHA_SIGLA", "S"]).size().reset_index(name="Pessoas")
              .rename(columns={"A": "Área da graduação", "LINHA_SIGLA": "Linha", "S": "Setor de atuação"}))
    ui.grafico(fig, titulo,
               f"Área de graduação → linha de pesquisa → setor de atuação ({num(len(f))} pessoas)",
               "Áreas e setores com menos de 15 pessoas aparecem agrupados. Fontes: planilha do PPGDSTU e "
               "Currículo Lattes.", tabela, chave="sankey")

# ====================================================================== diversificação
ui.secao("Diversificação ao longo do tempo")
dec = p.assign(FORA=~p["AREA_GRADUACAO"].isin(["Ciências Sociais Aplicadas", "Ciências Humanas"]))
serie = dec.groupby("DECADA").agg(FORA=("FORA", "mean"), N=("FORA", "size"))
serie = serie[serie["N"] >= 10]
if len(serie) >= 2:
    fig = charts.linha_unica(list(serie.index), list(serie["FORA"] * 100))
    ui.grafico(fig, f"Egressos vindos de fora das Ciências Sociais e Humanas: de {pct(serie['FORA'].iloc[0], 0)} "
                    f"({serie.index[0].replace('Anos ', 'anos ')}) para {pct(serie['FORA'].iloc[-1], 0)} "
                    f"({serie.index[-1].replace('Anos ', 'anos ')})",
               "Percentual de egressos graduados em Agrárias, Biológicas, Saúde, Engenharias, Exatas e outras, "
               "por década da última titulação",
               "Décadas com pelo menos 10 pessoas no recorte.",
               serie.assign(FORA=(serie["FORA"] * 100).round(1)).reset_index().rename(
                   columns={"DECADA": "Década", "FORA": "% fora de Sociais e Humanas", "N": "Pessoas"}),
               chave="diversificacao")
