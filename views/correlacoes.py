"""Correlações: quais características andam juntas, com testes estatísticos."""
import numpy as np
import pandas as pd
import streamlit as st

from core import charts, data, filters, stats
from core import components as ui
from core.theme import NOME_LINHA, num

r = filters.barra(data.titulacoes(), data.pessoas())
p = r.pessoas.copy()
if len(p) < 30:
    st.info("Pessoas insuficientes no recorte para medir associações (mínimo de 30).")
    st.stop()

p["LINHA_NOME"] = p["LINHA_SIGLA"].map(NOME_LINHA).where(p["LINHA_SIGLA"] != "N/I")
p["ESP"] = np.where(p["SETOR_LATTES"] == "Ensino Superior Público", "Sim", "Não")
p.loc[p["SETOR_LATTES"].isna(), "ESP"] = None     # sem Lattes compilado: fica fora do modelo
grandes = p["AREA_GRADUACAO"].value_counts()
p["AREA_AGRUP"] = p["AREA_GRADUACAO"].where(p["AREA_GRADUACAO"].isin(grandes[grandes >= 20].index), "Outras áreas")
p.loc[p["AREA_GRADUACAO"].isna(), "AREA_AGRUP"] = None

VARIAVEIS = {
    "Nível do título": "NIVEL_MAIS_ALTO",
    "Tempo desde a titulação": "COORTE",
    "Linha de pesquisa": "LINHA_NOME",
    "Área da graduação": "AREA_AGRUP",
    "Trajetória no programa": "TRAJETORIA",
    "Setor de atuação (Lattes)": "SETOR_LATTES",
    "Atua no ensino superior": "VINCULO_ACADEMICO",
    "Localizado em fonte oficial": "LOCALIZADO",
    "Carreira (fonte oficial)": "CARREIRA",
    "Esfera do vínculo": "ESFERA",
    "Atua na Amazônia Legal": "AMAZONIA_LEGAL",
    "Aposentado": "APOSENTADO",
}
ui.secao("Mapa das associações",
         "V de Cramér mede a força da associação entre duas características categóricas: 0 = nenhuma, 1 = "
         "total. Valores abaixo de 0,1 são desprezíveis; de 0,1 a 0,3, fracos a moderados; acima de 0,3, fortes. "
         "Pares com relação óbvia por construção (por exemplo, setor e “atua no ensino superior”) aparecem fortes "
         "por definição.")


@st.cache_data(show_spinner=False)
def matriz(df: pd.DataFrame, cols: tuple):
    nomes = list(cols)
    v = pd.DataFrame(np.nan, index=nomes, columns=nomes)
    pv = v.copy()
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            res = stats.cramer(df[VARIAVEIS[a]], df[VARIAVEIS[b]])
            if res:
                v.loc[a, b] = v.loc[b, a] = res["V"]
                pv.loc[a, b] = pv.loc[b, a] = res["p"]
    return v, pv


cols = tuple(VARIAVEIS)
v, pv = matriz(p[list(VARIAVEIS.values())], cols)
texto = v.map(lambda x: "" if np.isnan(x) else num(x, 2))
texto = texto.where(~(pv >= 0.05), texto + "†")
pares = (v.where(np.triu(np.ones(v.shape, dtype=bool), 1)).stack().sort_values(ascending=False))
obvios = {frozenset(x) for x in [("Setor de atuação (Lattes)", "Atua no ensino superior"),
                                 ("Setor de atuação (Lattes)", "Localizado em fonte oficial"),
                                 ("Carreira (fonte oficial)", "Esfera do vínculo"),
                                 ("Nível do título", "Trajetória no programa"),
                                 ("Atua no ensino superior", "Carreira (fonte oficial)"),
                                 ("Setor de atuação (Lattes)", "Carreira (fonte oficial)"),
                                 ("Tempo desde a titulação", "Aposentado"),
                                 ("Atua no ensino superior", "Esfera do vínculo"),
                                 ("Setor de atuação (Lattes)", "Esfera do vínculo")]}
nao_obvios = [(a, b, x) for (a, b), x in pares.items() if frozenset((a, b)) not in obvios]
destaque = ", ".join(f"{a.lower()} × {b.lower()} ({num(x, 2)})" for a, b, x in nao_obvios[:3])
lin = v.loc["Linha de pesquisa", "Setor de atuação (Lattes)"]
fig = charts.mapa_calor(v, formato="{:.2f}", zmin=0, zmax=0.6, rotulo_valor="", texto=texto,
                        largura_x=14, largura_y=28, altura=560)
coorte = v.loc["Tempo desde a titulação", "Setor de atuação (Lattes)"]
if not np.isnan(lin) and not np.isnan(coorte) and coorte > lin:
    tit_mapa = (f"Para o setor de atuação, pesa mais o tempo desde a titulação (V = {num(coorte, 2)}) do que a "
                f"linha de pesquisa (V = {num(lin, 2)})")
else:
    tit_mapa = "Associações entre as características dos egressos"
ui.grafico(fig, tit_mapa,
           f"V de Cramér entre pares de características ({num(len(p))} pessoas). Associações não óbvias mais fortes: "
           f"{destaque}.",
           "† = associação não significativa (teste qui-quadrado, p ≥ 0,05). V corrigido para viés (Bergsma, 2013).",
           v.round(3).reset_index().rename(columns={"index": "Característica"}), chave="cramer")

# ====================================================================== explorador
ui.secao("Explorar um cruzamento",
         "Escolha duas características. As células mostram a distribuição percentual de cada linha da tabela; "
         "a cor indica onde há mais (verde) ou menos (laranja) casos do que o esperado se não houvesse associação.")
c1, c2 = st.columns(2)
a = c1.selectbox("Linhas da tabela", cols, index=cols.index("Linha de pesquisa"), key="x_cruz_a")
b = c2.selectbox("Colunas da tabela", cols, index=cols.index("Setor de atuação (Lattes)"), key="x_cruz_b")
if a == b:
    st.caption("Escolha duas características diferentes.")
else:
    m = p[[VARIAVEIS[a], VARIAVEIS[b]]].dropna()
    tab = pd.crosstab(m.iloc[:, 0], m.iloc[:, 1])
    tab = tab.loc[tab.sum(axis=1) >= 5, tab.sum(axis=0) >= 5]
    if tab.shape[0] >= 2 and tab.shape[1] >= 2:
        res = stats.cramer(m.iloc[:, 0], m.iloc[:, 1])
        adj = stats.residuos(tab).clip(-6, 6)
        perc = tab.div(tab.sum(axis=1), axis=0) * 100
        rot = perc.map(lambda x: f"{num(x, 0)}%")
        adj.index = [f"{i} ({num(n)})" for i, n in zip(tab.index, tab.sum(axis=1))]
        rot.index = adj.index
        fig = charts.mapa_calor(adj, texto=rot, divergente=True, zmax=6, rotulo_valor=" (resíduo)",
                                largura_x=16, largura_y=30)
        sig = "estatisticamente significativa" if res["p"] < 0.05 else "não significativa"
        ui.grafico(fig, f"Associação {stats.forca(res['V'])} e {sig}: V = {num(res['V'], 2)}",
                   f"{a} × {b}: % de cada linha; cor = resíduo padronizado ajustado (|r| > 2 destoa do esperado). "
                   f"χ² = {num(res['chi2'], 1)}, {res['gl']} graus de liberdade, p = "
                   f"{'< 0,001' if res['p'] < 0.001 else num(res['p'], 3)}, n = {num(res['n'])}.",
                   "Categorias com menos de 5 pessoas omitidas.",
                   tab.reset_index(), chave="explorador")
    else:
        st.caption("Categorias insuficientes para o cruzamento no recorte atual.")

# ====================================================================== regressão
ui.secao("O que se associa a atuar no ensino superior público",
         "Regressão logística: compara a chance de atuar no ensino superior público entre grupos, mantendo as "
         "demais características constantes. Razão de chances acima de 1 = chance maior que a do grupo de "
         "referência; abaixo de 1 = menor. Pontos cinza: diferença não significativa (p ≥ 0,05).")
preditores = {"NIVEL_MAIS_ALTO": "Mestrado", "COORTE": "20 anos ou mais",
              "LINHA_NOME": "Sociedade, Urbanização e Estudos Populacionais", "AREA_AGRUP": "Ciências Sociais Aplicadas"}
rot_var = {"NIVEL_MAIS_ALTO": "Nível", "COORTE": "Tempo desde a titulação", "LINHA_NOME": "Linha",
           "AREA_AGRUP": "Graduação"}
mod = stats.logit(p[p["ESP"].notna()].assign(Y=lambda d: (d["ESP"] == "Sim").astype(int)), "Y",
                  {k: v_ for k, v_ in preditores.items() if p[k].nunique() >= 2})
if mod is None:
    st.caption("O modelo não pôde ser estimado com o recorte atual (poucos casos ou categorias sem variação).")
else:
    tab_or, n_mod, r2 = mod
    tab_or["TERMO"] = [f"{rot_var[v_]}: {c}" for v_, c in zip(tab_or["VARIAVEL"], tab_or["CATEGORIA"])]
    fig = charts.floresta(tab_or)
    dout = tab_or[(tab_or["VARIAVEL"] == "NIVEL_MAIS_ALTO") & (tab_or["CATEGORIA"] == "Doutorado")]
    tit = (f"Com as demais características constantes, ter doutorado multiplica por {num(dout['OR'].iloc[0], 1)} "
           "a chance de atuar no ensino superior público" if len(dout) and dout["SIGNIF"].iloc[0]
           else "Fatores associados a atuar no ensino superior público")
    refs = "; ".join(f"{rot_var[k]}: {v_}" for k, v_ in preditores.items() if k in set(tab_or["VARIAVEL"]))
    ui.grafico(fig, tit, f"Razões de chance com intervalo de confiança de 95% ({num(n_mod)} pessoas; pseudo-R² de "
                         f"McFadden = {num(r2, 2)}). Referências: {refs}.",
               "Desfecho: setor “Ensino Superior Público” no Currículo Lattes. Modelo logístico estimado com "
               "statsmodels.",
               tab_or[["TERMO", "OR", "LI", "LS", "P"]].round(3).rename(columns={
                   "TERMO": "Termo", "OR": "Razão de chances", "LI": "IC 95% inferior", "LS": "IC 95% superior",
                   "P": "p"}), chave="logit")
    ui.ressalva("Associação não é causalidade. O modelo descreve quem está onde; não prova que o título ou a "
                "linha causaram o destino. Turmas recentes ainda estão em inserção profissional.")
