"""Panorama: os números do programa num relance."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import charts, data, filters
from core import components as ui
from core.theme import COR_NIVEL, GRADE, NOME_LINHA, ORDEM_LINHAS, num, pct

tit_all, pes_all, meta = data.titulacoes(), data.pessoas(), data.meta()
r = filters.barra(tit_all, pes_all)
t, p = r.titulacoes, r.pessoas

if t.empty:
    st.info("Nenhuma titulação no recorte escolhido. Ajuste os filtros ou use **Limpar**.")
    st.stop()

a0, a1 = int(t["ANO"].min()), int(t["ANO"].max())
n_m, n_d = int((t["NIVEL"] == "Mestrado").sum()), int((t["NIVEL"] == "Doutorado").sum())
comp = meta.get("complemento_capes", {})
n_capes = int((t["FONTE_REGISTRO"] != "Planilha do programa").sum())
FONTE_TIT = ("Fonte: quadro geral de egressos do PPGDSTU, complementado com os titulados registrados pela CAPES "
             "(Coleta Sucupira e Catálogo de Teses e Dissertações) e, para 2025, com a lista do site do programa; "
             "conferido com o Repositório Institucional da UFPA.")
com_lattes = p[p["OCUPACAO_LATTES"].notna()]       # quem tem ocupação compilada do Lattes

# ====================================================================== número principal
st.html('<div style="height:10px"></div>')
c_hero, c_kpi = st.columns([1.05, 2.6], gap="large")
with c_hero:
    partes = []
    if n_m:
        partes.append(f"{num(n_m)} dissertações de mestrado")
    if n_d:
        partes.append(f"{num(n_d)} teses de doutorado")
    ui.destaque(num(len(t)), "titulações defendidas no programa",
                f"{' e '.join(partes)}, de {a0} a {a1}, por {num(len(p))} pessoas.")

with c_kpi:
    ambos = p["TRAJETORIA"].eq("Mestrado e doutorado").sum()
    cont_or = t["ORIENTADOR"].value_counts()
    top10 = cont_or.head(10).sum() / max(cont_or.sum(), 1)
    acad = com_lattes["VINCULO_ACADEMICO"].eq("Sim").mean() if len(com_lattes) else None
    loc = p["LOCALIZADO"].eq("Sim").mean() if len(p) else None
    com_uf = p["UF_ATUACAO"].notna()
    amz = p.loc[com_uf, "AMAZONIA_LEGAL"].eq("Sim").mean() if com_uf.any() else None
    gestao = int(p["EXERCE_GESTAO"].eq("Sim").sum())
    ui.indicadores([
        ("Pessoas tituladas", num(len(p)), f"{num(ambos)} fizeram mestrado e doutorado aqui"),
        ("Orientadores(as)", num(t["ORIENTADOR"].nunique()),
         f"os 10 mais frequentes orientaram {pct(top10, 0)} dos trabalhos" if len(cont_or) > 10
         else "com ao menos uma orientação no recorte"),
        ("Atuam no ensino superior", pct(acad, 0), f"segundo o Lattes, entre {num(len(com_lattes))} com Lattes compilado"),
        ("Localizados em fonte oficial", pct(loc, 0), "folhas públicas ou registros da CAPES"),
        ("Atuam na Amazônia Legal", pct(amz, 0), f"entre os {num(com_uf.sum())} com local conhecido"),
        ("Em função de gestão", num(gestao), "reitoria, direção, coordenação ou chefia (SIAPE)"),
    ])

# ====================================================================== série anual
ui.secao("Formação")
anos = list(range(a0, a1 + 1))
fig, tab = charts.colunas_por_ano(t, anos)
if 1999 in anos and n_d and "Doutorado" in tab and tab.loc[1999, "Doutorado"] > 0:
    fig.add_annotation(x=1999, y=int(tab.loc[1999].sum()), text="1999: primeiras teses",
                       showarrow=True, arrowhead=0, arrowcolor="#C9C6BD", ax=-8, ay=-40,
                       font=dict(size=11.5, color="#55574F"))

ult = t[t["ANO"] > a1 - 8]
if n_m and n_d and (ult["NIVEL"] == "Doutorado").sum() > (ult["NIVEL"] == "Mestrado").sum():
    titulo = (f"Nos últimos oito anos do recorte, as teses ({num((ult['NIVEL'] == 'Doutorado').sum())}) "
              f"superaram as dissertações ({num((ult['NIVEL'] == 'Mestrado').sum())})")
else:
    pico = tab.sum(axis=1).idxmax()
    titulo = f"{num(len(t))} titulações entre {a0} e {a1}; o ano com mais defesas foi {pico}"
tabela = tab.rename(columns={"Mestrado": "Dissertações", "Doutorado": "Teses"})
tabela["Total"] = tabela.sum(axis=1)
ui.grafico(fig, titulo, "Titulações por ano de defesa e nível", FONTE_TIT,
           tabela.reset_index().rename(columns={"ANO": "Ano"}), chave="anual")

if n_capes:
    tc = t[t["FONTE_REGISTRO"] != "Planilha do programa"]
    anos_c = [str(a) for a in tc["ANO"].value_counts().head(3).sort_index().index]
    anos_c = ", ".join(anos_c[:-1]) + " e " + anos_c[-1] if len(anos_c) > 1 else anos_c[0]
    do_site = tc["FONTE_REGISTRO"].eq("Site do programa").any()
    fontes = ("dos registros de titulados da CAPES e, para as defesas mais recentes, da lista publicada no site do "
              "programa" if do_site else "dos registros de titulados da CAPES")
    origem = ("veio da Plataforma Sucupira ou é a do(a) orientador(a)"
              if tc["LINHA_ORIGEM"].isin(["Informada na Sucupira", "Linha do orientador (site do programa)"]).any()
              else "foi atribuída pelo orientador")
    ui.ressalva(f"{num(n_capes)} das {num(len(t))} titulações do recorte não constavam na planilha do programa e foram "
                f"incluídas a partir {fontes}, concentradas em {anos_c}. "
                f"Para elas, a linha de pesquisa {origem}. A lista está na página Metodologia.")
    st.html('<div style="height:6px"></div>')

c1, c2 = st.columns(2, gap="medium")
with c1:
    lin = t["LINHA_SIGLA"].value_counts().reindex(ORDEM_LINHAS).dropna()
    lin = lin[lin > 0].sort_values(ascending=False)
    lin_nome = [NOME_LINHA[s] for s in lin.index]
    fig = charts.barras_h(lin_nome, lin.values, total=lin.sum(), largura_rotulo=34)
    lider = lin.index[0]
    n_antiga = int((t["LINHA_ORIGINAL"] == "Desenvolvimento Regional e Agrário").sum())
    ui.grafico(fig, f"{NOME_LINHA[lider]} reúne {pct(lin.iloc[0] / lin.sum(), 0)} das titulações",
               "Titulações por linha de pesquisa",
               f"“Desenvolvimento Regional e Agrário” (nome antigo, {num(n_antiga)} trabalhos no recorte) "
               "está somada a “Desenvolvimento Econômico, Regional e Agrário”. "
               "“Não informada”: teses sem linha registrada na planilha.",
               pd.DataFrame({"Linha de pesquisa": lin_nome, "Titulações": lin.values,
                             "%": (lin.values / lin.sum() * 100).round(1)}), chave="linhas")
with c2:
    per = t.groupby(["PERIODO_CAPES", "NIVEL"]).size().unstack(fill_value=0)
    per = per[[c for c in ["Mestrado", "Doutorado"] if c in per.columns]]
    ordem_per = sorted(per.index, key=lambda s: (s != "Antes de 1998", s))
    per = per.reindex(ordem_per)
    figp = go.Figure()
    for nivel in per.columns:
        nome = "Dissertações" if nivel == "Mestrado" else "Teses"
        figp.add_bar(y=[charts.quebrar(x, 14) for x in per.index], x=per[nivel], name=nome,
                     orientation="h", marker=dict(color=COR_NIVEL[nivel], line=charts.GAP),
                     hovertemplate=f"<b>%{{x}}</b> {nome.lower()}<extra></extra>")
    figp.update_layout(barmode="stack", height=max(220, 34 * len(per) + 60), bargap=0.36,
                       yaxis=dict(autorange="reversed", showgrid=False, ticklabelstandoff=8),
                       xaxis=dict(showgrid=True, gridcolor=GRADE, showline=False),
                       hovermode="y unified", legend=dict(y=1.04, traceorder="normal"),
                       margin=dict(l=4, r=8, t=28, b=4))
    tot_per = per.sum(axis=1)
    melhor = tot_per.idxmax()
    ui.grafico(figp, f"O período {melhor} foi o de maior produção, com {num(tot_per.max())} titulações",
               "Titulações por período de avaliação da CAPES (triênios até 2012, quadriênios desde 2013)",
               FONTE_TIT,
               per.reset_index().rename(columns={"PERIODO_CAPES": "Período", "Mestrado": "Dissertações",
                                                 "Doutorado": "Teses"}), chave="periodos")

# ====================================================================== destino e território
ui.secao("Onde estão os egressos",
         "Atuação atual segundo o Currículo Lattes e, para quem foi localizado, as folhas de pagamento "
         "públicas e os registros da CAPES. Cada pessoa conta uma vez. Quem entrou na base pelos registros "
         "da CAPES não tem Lattes compilado e aparece só nas fontes oficiais.")
c3, c4 = st.columns(2, gap="medium")
with c3:
    st_ = p["SETOR_LATTES"].value_counts()
    fig = charts.barras_h(st_.index, st_.values, total=st_.sum(), largura_rotulo=30)
    ui.grafico(fig, f"{pct(st_.get('Ensino Superior Público', 0) / max(st_.sum(), 1), 0)} atuam no "
                    "ensino superior público",
               f"Setor de atuação declarado no Currículo Lattes ({num(len(com_lattes))} pessoas com Lattes compilado)",
               "Fonte: Currículo Lattes, compilado pela coordenação do PPGDSTU.",
               pd.DataFrame({"Setor": st_.index, "Pessoas": st_.values,
                             "%": (st_.values / st_.sum() * 100).round(1)}), chave="setor")
with c4:
    inst = p["INSTITUICAO_ATUACAO"].value_counts()
    top = inst.head(10)
    fig = charts.barras_h(top.index, top.values, total=inst.sum(), largura_rotulo=20)
    ui.grafico(fig, f"{top.index[0]} é a principal instituição de destino, com {pct(top.iloc[0] / inst.sum(), 0)}"
                    " dos egressos com instituição conhecida",
               f"As 10 instituições com mais egressos, entre {num(inst.sum())} pessoas com instituição conhecida",
               "Fonte: Currículo Lattes (instituição declarada) e, na falta dele, o órgão da folha de "
               "pagamento ou do registro da CAPES.",
               pd.DataFrame({"Instituição": inst.index, "Pessoas": inst.values}), chave="instituicoes")

com_uf = p[p["UF_ATUACAO"].notna()]
cont_uf = com_uf["UF_ATUACAO"].value_counts()
c5, c6 = st.columns([1.35, 1], gap="medium")
with c5:
    fig = charts.mapa_uf(cont_uf, data.malha_uf(), len(com_uf))
    pa = cont_uf.get("PA", 0) / max(len(com_uf), 1)
    ui.grafico(fig, f"{pct(pa, 0)} dos egressos com local conhecido atuam no Pará",
               f"Egressos por unidade da federação de atuação ({num(len(com_uf))} de {num(len(p))} pessoas)",
               "Local: município declarado no Lattes; na falta dele, UF de exercício no SIAPE ou sede da "
               "instituição. Escala logarítmica.",
               pd.DataFrame({"UF": cont_uf.index, "Pessoas": cont_uf.values,
                             "%": (cont_uf.values / max(len(com_uf), 1) * 100).round(1)}), chave="mapa")
with c6:
    reg = com_uf["REGIAO"].value_counts()
    fig = charts.barras_h(reg.index, reg.values, total=reg.sum(), largura_rotulo=16)
    ui.grafico(fig, f"{pct(reg.get('Norte', 0) / max(reg.sum(), 1), 0)} permanecem na região Norte",
               "Egressos por região de atuação",
               "Mesma base do mapa.",
               pd.DataFrame({"Região": reg.index, "Pessoas": reg.values}), chave="regiao")
    sem = len(p) - len(com_uf)
    ui.ressalva(f"{num(sem)} egressos ({pct(sem / max(len(p), 1), 0)}) não têm local de atuação conhecido — "
                "sobretudo quem atua fora do serviço público. O retrato territorial tende a "
                "superestimar a permanência na rede pública amazônica.")

# ====================================================================== achados
ui.secao("Destaques")
achados = []
mi = p["MOMENTO_INGRESSO"].dropna()
if len(mi) >= 20:
    antes = mi.eq("Já era servidor(a) antes").mean()
    achados.append((pct(antes, 0), f"dos egressos no serviço público federal com data de ingresso conhecida "
                    f"já eram servidores antes de se titular ({num(len(mi))} pessoas). O programa também "
                    "qualifica quem já está no Estado."))
esp = com_lattes.groupby("LINHA_SIGLA")["SETOR_LATTES"].apply(lambda s: (s == "Ensino Superior Público").mean())
esp = esp[[s for s in esp.index if s != "N/I"]]
if len(esp) >= 2:
    achados.append((f"{pct(esp.min(), 0)} a {pct(esp.max(), 0)}",
                    "é a faixa de egressos no ensino superior público entre as linhas de pesquisa: a linha "
                    "cursada pouco altera o destino profissional."))
rec = com_lattes[com_lattes["ANO_ULTIMA_TITULACAO"] >= 2020]
if len(rec) >= 20:
    disc = rec["SETOR_LATTES"].eq("Discente de Pós-Graduação").mean()
    achados.append((pct(disc, 0), f"dos titulados desde 2020 seguem estudando em outra pós-graduação "
                    f"({num(len(rec))} pessoas). A inserção profissional das turmas recentes ainda está em curso."))
if achados:
    st.html('<div class="achados">' + "".join(
        f'<div class="achado"><div class="achado-num">{v}</div><p>{txt}</p></div>' for v, txt in achados)
        + "</div>")
