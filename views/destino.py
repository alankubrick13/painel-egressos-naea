"""Destino profissional: ocupação, setor, vínculos oficiais, gestão, ingresso e remuneração."""
import pandas as pd
import streamlit as st

from core import charts, data, filters
from core import components as ui
from core.theme import APAGADO, LARANJA_NAEA, NOME_LINHA, ORDEM_LINHAS, VERDE_NAEA, num, pct, reais

r = filters.barra(data.titulacoes(), data.pessoas())
p = r.pessoas
if p.empty:
    st.info("Nenhuma pessoa no recorte escolhido. Ajuste os filtros ou use **Limpar**.")
    st.stop()

setor = p["SETOR_LATTES"].value_counts()
lat = p[p["OCUPACAO_LATTES"].notna()]            # base das medidas do Lattes
loc = p[p["LOCALIZADO"] == "Sim"]
ativos_fed = p[p["TIPO_REGISTRO"] == "Folha federal – ativo"]

st.html('<div style="height:10px"></div>')
ui.indicadores([
    ("Ensino superior (público, privado ou exterior)", pct(lat["VINCULO_ACADEMICO"].eq("Sim").mean(), 0),
     f"segundo o Lattes ({num(len(lat))} pessoas com Lattes compilado)"),
    ("Setor público fora da academia", pct(setor.get("Setor Público (não acadêmico)", 0) / max(len(lat), 1), 0),
     "secretarias, ministérios, tribunais, autarquias"),
    ("Sociedade civil", pct(setor.get("Sociedade Civil", 0) / max(len(lat), 1), 0),
     "ONGs, empresas, consultoria, movimentos"),
    ("Localizados em fonte oficial", pct(len(loc) / max(len(p), 1), 0), f"{num(len(loc))} pessoas"),
    ("Em função de gestão", num(p["EXERCE_GESTAO"].eq("Sim").sum()),
     f"de {num(len(ativos_fed))} servidores federais ativos localizados"),
    ("Aposentados", num(p["APOSENTADO"].eq("Sim").sum()), "na folha federal"),
])

# ====================================================================== ocupação (Lattes)
ui.secao("Ocupação declarada",
         "Ocupação atual segundo o Currículo Lattes de cada egresso, compilado pela coordenação. Cobre "
         "inclusive quem não está no serviço público; não cobre quem entrou na base pelos registros da CAPES.")
c1, c2 = st.columns(2, gap="medium")
with c1:
    oc = p["OCUPACAO_LATTES"].value_counts()
    fig = charts.barras_h(oc.index, oc.values, total=oc.sum(), largura_rotulo=26)
    ui.grafico(fig, f"Docência em instituição pública de ensino superior é a ocupação de "
                    f"{pct(oc.get('IES Pública', 0) / max(oc.sum(), 1), 0)}",
               "Pessoas por ocupação declarada (9 categorias)",
               "Fonte: Currículo Lattes. “Servidor técnico – IES pública”: técnico-administrativo em universidade.",
               pd.DataFrame({"Ocupação": oc.index, "Pessoas": oc.values,
                             "%": (oc.values / oc.sum() * 100).round(1)}), chave="ocupacao")
with c2:
    fig = charts.barras_h(setor.index, setor.values, total=setor.sum(), largura_rotulo=26)
    ui.grafico(fig, f"{pct(setor.iloc[0] / setor.sum(), 0)} atuam em {setor.index[0].lower()}",
               "Pessoas por setor de atuação (ocupações agrupadas)",
               "Fonte: Currículo Lattes.",
               pd.DataFrame({"Setor": setor.index, "Pessoas": setor.values,
                             "%": (setor.values / setor.sum() * 100).round(1)}), chave="setor-destino")

ui.secao("Quem vai para onde",
         "Cada coluna soma 100%: a cor mais escura indica onde se concentra cada grupo.")
ordem_setor = list(setor.index)


def cruzamento(coluna, ordem_col, rotulos=None):
    tab = pd.crosstab(lat["SETOR_LATTES"], lat[coluna]).reindex(index=ordem_setor)
    tab = tab.reindex(columns=[c for c in ordem_col if c in tab.columns])
    tab = tab.loc[:, tab.sum() >= 5]
    pc = tab.div(tab.sum(), axis=1) * 100
    if rotulos:
        pc.columns = [rotulos.get(c, c) for c in pc.columns]
    pc.columns = [f"{c} ({num(n)})" for c, n in zip(pc.columns, tab.sum().values)]
    return tab, pc


c3, c4 = st.columns(2, gap="medium")
with c3:
    tab, pc = cruzamento("NIVEL_MAIS_ALTO", ["Mestrado", "Doutorado"])
    if tab.shape[1] == 2:
        esp = tab.loc["Ensino Superior Público"] / tab.sum()
        tit = (f"Doutores chegam mais ao ensino superior público ({pct(esp['Doutorado'], 0)}) que mestres "
               f"({pct(esp['Mestrado'], 0)})" if esp["Doutorado"] > esp["Mestrado"] else
               "Setor de atuação por nível do último título")
    else:
        tit = "Setor de atuação por nível do último título"
    ui.grafico(charts.mapa_calor(pc, largura_x=18, largura_y=26), tit,
               "Setor de atuação (% de cada nível; entre parênteses, o número de pessoas)",
               "Nível: o título mais alto obtido no PPGDSTU.",
               pc.round(1).reset_index().rename(columns={"SETOR_LATTES": "Setor"}), chave="setor-nivel")
with c4:
    coortes = ["Até 4 anos", "5 a 9 anos", "10 a 19 anos", "20 anos ou mais"]
    tab, pc = cruzamento("COORTE", coortes)
    tit = "Setor de atuação pelo tempo desde a titulação"
    if "Até 4 anos" in tab.columns and "Discente de Pós-Graduação" in tab.index:
        d = tab.loc["Discente de Pós-Graduação", "Até 4 anos"] / tab["Até 4 anos"].sum()
        tit = f"Entre os titulados há até 4 anos, {pct(d, 0)} seguem estudando em outra pós-graduação"
    ui.grafico(charts.mapa_calor(pc, largura_x=14, largura_y=26), tit,
               "Setor de atuação (% de cada faixa de tempo desde a última titulação)",
               "Tempo contado até 2026.",
               pc.round(1).reset_index().rename(columns={"SETOR_LATTES": "Setor"}), chave="setor-coorte")

tab, pc = cruzamento("LINHA_SIGLA", ORDEM_LINHAS[:4], NOME_LINHA)
if tab.shape[1] >= 2:
    esp = (tab.loc["Ensino Superior Público"] / tab.sum())
    ui.grafico(charts.mapa_calor(pc, largura_x=24, largura_y=30),
               f"O destino varia pouco entre as linhas: ensino superior público vai de {pct(esp.min(), 0)} "
               f"a {pct(esp.max(), 0)}",
               "Setor de atuação (% de cada linha de pesquisa)",
               "Linha: a da titulação mais recente. Teste de associação na página Correlações.",
               pc.round(1).reset_index().rename(columns={"SETOR_LATTES": "Setor"}), chave="setor-linha")

# ====================================================================== fontes oficiais
ui.secao("Vínculos em fontes oficiais",
         f"Para as {num(len(loc))} pessoas localizadas em folhas de pagamento públicas ou nos registros da "
         "CAPES. Quem atua fora do serviço público raramente aparece nessas fontes.")
c5, c6 = st.columns(2, gap="medium")
with c5:
    car = loc["CARREIRA"].value_counts()
    fig = charts.barras_h(car.index, car.values, total=car.sum(), largura_rotulo=28)
    ui.grafico(fig, f"{pct(car.get('Docente do ensino superior', 0) / max(car.sum(), 1), 0)} dos localizados "
                    "são docentes do ensino superior",
               "Carreira, a partir do cargo na folha de pagamento ou no registro da CAPES",
               "Fontes: SIAPE (Portal da Transparência), folhas do Pará, TJPA, MPPA, TCE-PA, Prefeitura de "
               "Belém, CAPES.", pd.DataFrame({"Carreira": car.index, "Pessoas": car.values}), chave="carreira")
with c6:
    ti = loc["TIPO_INSTITUICAO"].value_counts()
    fig = charts.barras_h(ti.index, ti.values, total=ti.sum(), largura_rotulo=26)
    ui.grafico(fig, f"Universidades federais empregam {pct(ti.get('Universidade federal', 0) / max(ti.sum(), 1), 0)} "
                    "dos localizados",
               "Tipo de instituição do vínculo principal",
               "Classificação feita a partir do órgão pagador.",
               pd.DataFrame({"Tipo": ti.index, "Pessoas": ti.values}), chave="tipo-inst")

c7, c8 = st.columns(2, gap="medium")
with c7:
    es = loc["ESFERA"].value_counts()
    fig = charts.barras_h(es.index, es.values, total=es.sum(), largura_rotulo=20)
    ui.grafico(fig, f"{pct(es.get('Federal', 0) / max(es.sum(), 1), 0)} dos vínculos localizados são federais",
               "Esfera do vínculo principal",
               "“Em formação”: localizados como discentes de outro programa de pós-graduação (CAPES).",
               pd.DataFrame({"Esfera": es.index, "Pessoas": es.values}), chave="esfera")
with c8:
    ge = p["FUNCAO_GESTAO"].value_counts()
    if len(ge):
        fig = charts.barras_h(ge.index, ge.values, largura_rotulo=26)
        ui.grafico(fig, f"{num(ge.sum())} egressos exercem função de gestão no serviço federal",
                   "Funções comissionadas e de confiança registradas no SIAPE, por tipo",
                   "Só servidores federais localizados com alta confiança; outras esferas não informam função.",
                   pd.DataFrame({"Função": ge.index, "Pessoas": ge.values}), chave="gestao")

# ====================================================================== docência na pós-graduação
CODIGO_PPGDSTU = "15001016002P5"
MINUSC = {"da", "de", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "a", "o", "para", "com"}


def nome_programa(s):
    """'DESENVOLVIMENTO SUSTENTÁVEL DO TRÓPICO ÚMIDO - PPGDSTU' -> 'Desenvolvimento Sustentável do Trópico Úmido – PPGDSTU'."""
    base, *sigla = str(s).split(" - ")
    base = " ".join(w if w in MINUSC else w.capitalize() for w in base.lower().split())
    return " – ".join([base[:1].upper() + base[1:]] + [x.strip() for x in sigla])


def tipo_programa(r):
    if r["NM_MODALIDADE_PROGRAMA"] == "PROFISSIONAL":
        return "Profissional"
    return "Acadêmico, com doutorado" if "DOUTORADO" in r["NM_GRAU_PROGRAMA"] else "Acadêmico, só mestrado"


doc = data.docencia_ppg()
ano_doc = data.meta().get("docencia_ppg", {}).get("ano")
if len(doc):
    dc = doc[doc["ID_PESSOA"].isin(p["ID_PESSOA"])]
    ui.secao("Docência na pós-graduação",
             f"Egressos que eram docentes de programas de pós-graduação stricto sensu em {ano_doc}, ano mais recente "
             "publicado pela CAPES (dados abertos de docentes, Coleta Sucupira). A ligação usa o código da pessoa na "
             "CAPES ou o nome conferido com o título obtido; detalhes na página Metodologia.")
    if dc.empty:
        st.caption("Nenhum docente de pós-graduação no recorte escolhido.")
    else:
        pdoc = dc.drop_duplicates("ID_PESSOA")
        dout = p[p["NIVEL_MAIS_ALTO"] == "Doutorado"]
        dout_doc = int(dout["DOCENTE_PPG"].eq("Sim").sum())
        perm = int(dc.groupby("ID_PESSOA")["DS_CATEGORIA_DOCENTE"].agg(lambda s: s.eq("PERMANENTE").any()).sum())
        no_prog = dc.loc[dc["CD_PROGRAMA_IES"] == CODIGO_PPGDSTU, "ID_PESSOA"].nunique()
        ui.indicadores([
            ("Docentes de pós-graduação", num(len(pdoc)), f"{pct(len(pdoc) / len(p), 0)} dos egressos do recorte"),
            ("Entre quem se doutorou aqui", pct(dout_doc / max(len(dout), 1), 0),
             f"{num(dout_doc)} de {num(len(dout))} doutores"),
            ("Permanentes em algum programa", pct(perm / len(pdoc), 0), "os demais são colaboradores ou visitantes"),
            ("Programas diferentes", num(dc["CD_PROGRAMA_IES"].nunique()),
             f"em {num(dc['SG_ENTIDADE_ENSINO'].nunique())} instituições"),
            ("No próprio PPGDSTU", num(no_prog), "docentes do programa em que se titularam"),
        ])
        st.html('<div style="height:12px"></div>')
        fonte_doc = (f"Fonte: CAPES – Dados Abertos, docentes da pós-graduação ({ano_doc}). Quem é docente em mais "
                     "de um programa conta uma vez em cada categoria.")
        c11, c12 = st.columns(2, gap="medium")
        with c11:
            ies = dc.drop_duplicates(["ID_PESSOA", "SG_ENTIDADE_ENSINO"])["SG_ENTIDADE_ENSINO"].value_counts()
            top = ies.head(12)
            fig = charts.barras_h(top.index, top.values, total=len(pdoc), largura_rotulo=14)
            ui.grafico(fig, f"{pct(ies.iloc[0] / len(pdoc), 0)} dão aula em programas da {ies.index[0]}",
                       "Egressos docentes por instituição do programa (as 12 com mais egressos)", fonte_doc,
                       pd.DataFrame({"Instituição": ies.index, "Egressos docentes": ies.values}), chave="ppg-ies")
        with c12:
            ar = dc.drop_duplicates(["ID_PESSOA", "NM_AREA_AVALIACAO"])["NM_AREA_AVALIACAO"].str.capitalize()
            ar = ar.value_counts()
            top = ar.head(12)
            fig = charts.barras_h(top.index, top.values, total=len(pdoc), largura_rotulo=30)
            ui.grafico(fig, f"{top.index[0]} é a área com mais egressos docentes ({num(top.iloc[0])})",
                       "Egressos docentes por área de avaliação do programa (as 12 maiores)", fonte_doc,
                       pd.DataFrame({"Área de avaliação": ar.index, "Egressos docentes": ar.values}), chave="ppg-area")
        c13, c14 = st.columns(2, gap="medium")
        with c13:
            uf = dc.drop_duplicates(["ID_PESSOA", "SG_UF_PROGRAMA"])["SG_UF_PROGRAMA"].value_counts()
            top = uf.head(10)
            fig = charts.barras_h(top.index, top.values, total=len(pdoc), largura_rotulo=8, destaque="PA")
            ui.grafico(fig, f"{pct(uf.get('PA', 0) / len(pdoc), 0)} atuam em programas do Pará",
                       "Egressos docentes por UF do programa (as 10 maiores)", fonte_doc,
                       pd.DataFrame({"UF": uf.index, "Egressos docentes": uf.values}), chave="ppg-uf")
        with c14:
            tp = dc.assign(TIPO=dc.apply(tipo_programa, axis=1)).drop_duplicates(["ID_PESSOA", "TIPO"])["TIPO"]
            tp = tp.value_counts().reindex(["Acadêmico, com doutorado", "Acadêmico, só mestrado", "Profissional"]).dropna()
            fig = charts.barras_h(tp.index, tp.values.astype(int), total=len(pdoc), largura_rotulo=24)
            ui.grafico(fig, f"{num(tp.get('Acadêmico, com doutorado', 0))} egressos formam doutores em programas "
                            "acadêmicos",
                       "Egressos docentes por tipo de programa", fonte_doc,
                       pd.DataFrame({"Tipo de programa": tp.index, "Egressos docentes": tp.values.astype(int)}),
                       chave="ppg-tipo")
        ORDEM_CONCEITO = ["7", "6", "5", "4", "3", "2", "A"]
        ROT_CONCEITO = {c: f"Conceito {c}" for c in ORDEM_CONCEITO} | {"A": "A (programa novo, ainda sem nota)"}
        co = (dc.drop_duplicates(["ID_PESSOA", "CD_CONCEITO_PROGRAMA"])["CD_CONCEITO_PROGRAMA"].value_counts()
              .reindex(ORDEM_CONCEITO).dropna().astype(int))
        excel = int(dc.loc[dc["CD_CONCEITO_PROGRAMA"].isin(["6", "7"]), "ID_PESSOA"].nunique())
        cinco = int(dc.loc[dc["CD_CONCEITO_PROGRAMA"].isin(["5", "6", "7"]), "ID_PESSOA"].nunique())
        rotulos_co = [ROT_CONCEITO[c] for c in co.index]
        fig = charts.barras_h(rotulos_co, co.values, total=len(pdoc), largura_rotulo=26)
        ui.grafico(fig, f"{num(cinco)} egressos ({pct(cinco / len(pdoc), 0)}) dão aula em programas com conceito "
                        f"5 ou mais; {num(excel)} em programas de excelência (6 ou 7)",
                   "Egressos docentes pelo conceito CAPES do programa (escala de 1 a 7)",
                   fonte_doc + " Conceito registrado pela CAPES no ano; 6 e 7 indicam padrão internacional.",
                   pd.DataFrame({"Conceito": rotulos_co, "Egressos docentes": co.values}), chave="ppg-conceito")
        with st.container(border=True, key="card-docentes-ppg"):
            st.html('<div class="card-titulo">Em que programas os egressos dão aula</div>'
                    f'<div class="card-sub">{num(dc["CD_PROGRAMA_IES"].nunique())} programas com egressos no corpo '
                    'docente, do que tem mais egressos para o que tem menos. Clique no cabeçalho de uma coluna '
                    'para ordenar, por exemplo, por instituição ou conceito.</div>')
            lista = (dc.assign(Tipo=dc.apply(tipo_programa, axis=1),
                               Perm=dc["DS_CATEGORIA_DOCENTE"].eq("PERMANENTE"))
                     .groupby(["CD_PROGRAMA_IES", "NM_PROGRAMA_IES", "SG_ENTIDADE_ENSINO", "SG_UF_PROGRAMA",
                               "NM_AREA_AVALIACAO", "Tipo", "CD_CONCEITO_PROGRAMA"])
                     .agg(Egressos=("ID_PESSOA", "nunique"), Permanentes=("Perm", "sum")).reset_index()
                     .assign(Programa=lambda d: d["NM_PROGRAMA_IES"].map(nome_programa),
                             Area=lambda d: d["NM_AREA_AVALIACAO"].str.capitalize())
                     .sort_values(["Egressos", "Programa"], ascending=[False, True])
                     [["Programa", "SG_ENTIDADE_ENSINO", "SG_UF_PROGRAMA", "CD_CONCEITO_PROGRAMA", "Area", "Tipo",
                       "Egressos", "Permanentes"]]
                     .rename(columns={"SG_ENTIDADE_ENSINO": "Instituição", "SG_UF_PROGRAMA": "UF",
                                      "CD_CONCEITO_PROGRAMA": "Conceito CAPES",
                                      "Area": "Área de avaliação", "Tipo": "Tipo de programa",
                                      "Egressos": "Egressos docentes", "Permanentes": "Dos quais permanentes"}))
            st.dataframe(lista, hide_index=True, use_container_width=True, height=380)
            st.html(f'<div class="card-fonte">{fonte_doc}</div>')

# ====================================================================== ingresso
ui.secao("Entrada no serviço público",
         "Compara o ano de ingresso no serviço público federal com o ano da última titulação no PPGDSTU.")
c9, c10 = st.columns([1, 1.6], gap="medium")
mi = p["MOMENTO_INGRESSO"].value_counts().reindex(["Já era servidor(a) antes", "No mesmo ano",
                                                   "Ingressou depois"]).dropna()
with c9:
    if mi.sum():
        fig = charts.barras_h(mi.index, mi.values, total=mi.sum(), largura_rotulo=20)
        fig.data[0].marker.color = [APAGADO, APAGADO, VERDE_NAEA][:len(mi)]
        ui.grafico(fig, f"{pct(mi.get('Já era servidor(a) antes', 0) / mi.sum(), 0)} já eram servidores antes "
                        "de se titular",
                   f"Momento do ingresso no serviço público federal ({num(mi.sum())} pessoas com data conhecida)",
                   "Fonte: SIAPE, data de ingresso no serviço público.",
                   pd.DataFrame({"Momento": mi.index, "Pessoas": mi.values}), chave="momento")
with c10:
    d = p["ANOS_TITULACAO_INGRESSO"].dropna().astype(int).clip(-30, 30)
    if len(d) >= 10:
        h = d.value_counts().sort_index().reindex(range(-30, 31), fill_value=0)
        cores = [APAGADO if x < 0 else (LARANJA_NAEA if x == 0 else VERDE_NAEA) for x in h.index]
        fig = charts.histograma(h, cores=cores, rotulo_x="anos entre a titulação e o ingresso (negativo = antes)")
        fig.update_layout(xaxis=dict(dtick=5))
        depois = d[d > 0]
        ui.grafico(fig, f"Quem ingressou depois de se titular levou, em mediana, {num(depois.median(), 0)} "
                        f"ano(s) para entrar" if len(depois) else "Anos entre a titulação e o ingresso",
                   "Distribuição dos anos entre a titulação e o ingresso no serviço público federal "
                   "(cinza: antes; laranja: mesmo ano; verde: depois)",
                   "Valores além de ±30 anos agrupados nas pontas.",
                   pd.DataFrame({"Anos": h.index, "Pessoas": h.values}), chave="hist-ingresso")
mud = p["MUDOU_ORGAO_APOS_TITULO"].value_counts()
if mud.sum():
    ui.ressalva(f"{pct(mud.get('Sim', 0) / mud.sum(), 0)} dos servidores federais com data conhecida "
                f"({num(mud.sum())}) entraram no órgão atual depois da titulação, o que indica mudança de "
                "instituição ou novo concurso após o curso.")

# ====================================================================== remuneração
meta_rem = data.meta().get("remuneracao", {}).get("fontes", {})
pequenos = {k: v for k, v in meta_rem.items() if not v.get("publicada")}
ui.secao("Remuneração",
         "Remuneração bruta mensal, antes dos descontos, dos egressos localizados em folhas de pagamento públicas: "
         "servidores federais ativos e aposentados (SIAPE, junho de 2026) e servidores do Executivo do Pará (julho de "
         "2026). Só aparecem grupos com pelo menos 10 pessoas; nenhum valor individual é publicado.")
rem = data.remuneracao()
f = rem.copy()
if r.ativo:
    flt = st.session_state.get("flt", {})
    if flt.get("linha"):
        f = f[f["LINHA_SIGLA"].isin(flt["linha"])]
    if flt.get("nivel"):
        f = f[f["NIVEL_MAIS_ALTO"].isin(flt["nivel"])]
ativos = f[f["SITUACAO"] == "Ativo(a)"]


def resumo(base, col, ordem=None, minimo=10):
    g = base.groupby(col)["REMUNERACAO_BRUTA"].agg(
        N="size", MEDIA="mean", P25=lambda x: x.quantile(0.25), MEDIANA="median", P75=lambda x: x.quantile(0.75))
    g = g[g["N"] >= minimo].reset_index().rename(columns={col: "GRUPO"})
    if ordem:
        g["o"] = g["GRUPO"].map({k: i for i, k in enumerate(ordem)})
        g = g.sort_values("o").drop(columns="o")
    else:
        g = g.sort_values("MEDIA", ascending=False)
    return g


def tabela_rem(g, rotulo):
    return g.round(0).rename(columns={"GRUPO": rotulo, "N": "Pessoas", "MEDIA": "Média", "MEDIANA": "Mediana",
                                      "P25": "1º quartil", "P75": "3º quartil"})


def media_de(base, fonte):
    x = base.loc[base["FONTE_SALARIO"] == fonte, "REMUNERACAO_BRUTA"]
    return (reais(x.mean()), f"mediana {reais(x.median())} · {num(len(x))} pessoas") if len(x) >= 10 else \
        ("–", "menos de 10 pessoas no recorte")


if len(ativos) >= 10:
    ui.indicadores([
        ("Média salarial dos servidores ativos", reais(ativos["REMUNERACAO_BRUTA"].mean()),
         f"mediana {reais(ativos['REMUNERACAO_BRUTA'].median())} · {num(len(ativos))} pessoas"),
        ("Federais ativos (SIAPE)", *media_de(f, "Federal – ativo (SIAPE)")),
        ("Executivo do Pará", *media_de(f, "Estadual – Executivo do Pará")),
        ("Aposentados federais (SIAPE)", *media_de(f, "Federal – aposentado (SIAPE)")),
    ])
    st.html('<div style="height:12px"></div>')
    g = resumo(f, "FONTE_SALARIO", ["Federal – ativo (SIAPE)", "Estadual – Executivo do Pará",
                                    "Federal – aposentado (SIAPE)"])
    if len(g):
        fed = g.set_index("GRUPO")
        tit = "Média e mediana da remuneração por fonte"
        if {"Federal – ativo (SIAPE)", "Estadual – Executivo do Pará"} <= set(fed.index):
            dif = fed.loc["Federal – ativo (SIAPE)", "MEDIA"] / fed.loc["Estadual – Executivo do Pará", "MEDIA"] - 1
            tit = f"No serviço federal, a média é {pct(dif, 0)} maior que no Executivo do Pará"
        nota = "Fontes: SIAPE/Portal da Transparência (06/2026) e Portal da Transparência do Pará (07/2026)."
        if pequenos:
            nota += (" Não aparecem, por terem menos de 10 pessoas: " + "; ".join(
                f"{k} ({v['n']}, competência {v['competencia']})" for k, v in pequenos.items()) + ".")
        ui.grafico(charts.faixa_mediana(g), tit, "Remuneração bruta mensal por fonte: média (losango), mediana "
                   "(círculo) e metade central (traço)", nota, tabela_rem(g, "Fonte"), chave="rem-fonte")

    c11, c12 = st.columns(2, gap="medium")
    with c11:
        g = resumo(ativos, "CARREIRA")
        if len(g):
            top = g.iloc[0]
            ui.grafico(charts.faixa_mediana(g), f"{top['GRUPO']} tem a maior média: {reais(top['MEDIA'])}",
                       "Servidores ativos por carreira: média, mediana e metade central",
                       "Carreira deduzida do cargo na folha de pagamento.", tabela_rem(g, "Carreira"),
                       chave="rem-carreira")
    with c12:
        g = resumo(ativos, "NIVEL_MAIS_ALTO", ["Mestrado", "Doutorado"])
        if len(g) == 2:
            gi = g.set_index("GRUPO")
            dif = gi.loc["Doutorado", "MEDIA"] / gi.loc["Mestrado", "MEDIA"] - 1
            tit = (f"A média de quem tem doutorado ({reais(gi.loc['Doutorado', 'MEDIA'])}) é {pct(dif, 0)} maior "
                   f"que a de quem tem mestrado ({reais(gi.loc['Mestrado', 'MEDIA'])})")
        else:
            tit = "Remuneração por nível do último título"
        if len(g):
            ui.grafico(charts.faixa_mediana(g), tit, "Servidores ativos por nível do título obtido no PPGDSTU",
                       "Parte da diferença reflete carreira e tempo de serviço, não só o título.",
                       tabela_rem(g, "Nível"), chave="rem-nivel")
    g = resumo(ativos, "COORTE", ["Até 4 anos", "5 a 9 anos", "10 a 19 anos", "20 anos ou mais"])
    if len(g) >= 2:
        rho = ativos[["ANOS_DESDE_TITULACAO", "REMUNERACAO_BRUTA"]].corr(method="spearman").iloc[0, 1]
        ui.grafico(charts.faixa_mediana(g),
                   f"A média sobe de {reais(g['MEDIA'].iloc[0])} ({g['GRUPO'].iloc[0].lower()}) para "
                   f"{reais(g['MEDIA'].iloc[-1])} ({g['GRUPO'].iloc[-1].lower()} desde a titulação)",
                   f"Servidores ativos por tempo desde a última titulação (correlação de Spearman = {num(rho, 2)})",
                   "Reflete progressão na carreira. Nesta seção, só os filtros de linha e nível se aplicam "
                   "(a tabela de remuneração não tem identificação individual).",
                   tabela_rem(g, "Tempo desde a titulação"), chave="rem-coorte")
else:
    st.caption("Menos de 10 servidores ativos com remuneração no recorte: valores não exibidos.")
