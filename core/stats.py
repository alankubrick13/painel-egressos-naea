"""Estatística do painel: associação entre categorias, regressão logística e termos dos títulos."""
import re

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats


# ---------------------------------------------------------------- associação entre duas categorias
def cramer(x: pd.Series, y: pd.Series):
    """V de Cramér com correção de viés (Bergsma, 2013) e teste qui-quadrado.

    Devolve dict com V, chi2, gl, p e n; None se a tabela não permitir o cálculo.
    """
    m = pd.concat([x, y], axis=1).dropna()
    if len(m) < 20:
        return None
    tab = pd.crosstab(m.iloc[:, 0], m.iloc[:, 1])
    tab = tab.loc[tab.sum(axis=1) > 0, tab.sum(axis=0) > 0]
    r, k = tab.shape
    if r < 2 or k < 2:
        return None
    chi2, p, gl, _ = stats.chi2_contingency(tab, correction=False)
    n = tab.values.sum()
    phi2 = chi2 / n
    phi2c = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    v = np.sqrt(phi2c / max(min(kc - 1, rc - 1), 1e-9))
    return {"V": float(v), "chi2": float(chi2), "gl": int(gl), "p": float(p), "n": int(n)}


def residuos(tab: pd.DataFrame) -> pd.DataFrame:
    """Resíduos padronizados ajustados: > 2 indica mais casos que o esperado; < -2, menos."""
    obs = tab.values.astype(float)
    n = obs.sum()
    lin, col = obs.sum(axis=1, keepdims=True), obs.sum(axis=0, keepdims=True)
    esp = lin @ col / n
    with np.errstate(divide="ignore", invalid="ignore"):
        adj = (obs - esp) / np.sqrt(esp * (1 - lin / n) * (1 - col / n))
    return pd.DataFrame(adj, index=tab.index, columns=tab.columns)


def forca(v):
    if v is None:
        return "–"
    if v < 0.1:
        return "desprezível"
    if v < 0.2:
        return "fraca"
    if v < 0.3:
        return "moderada"
    return "forte"


# ---------------------------------------------------------------- regressão logística
def logit(df: pd.DataFrame, desfecho: str, preditores: dict):
    """Regressão logística com variáveis categóricas.

    preditores: {coluna: categoria_de_referência}. Devolve (tabela de razões de chance, n, pseudo-R²)
    ou None se o modelo não convergir.
    """
    import statsmodels.formula.api as smf

    cols = [desfecho, *preditores]
    d = df[cols].dropna().copy()
    if len(d) < 80 or d[desfecho].nunique() < 2:
        return None
    nomes = {c: f"x{i}" for i, c in enumerate(preditores)}
    d = d.rename(columns={desfecho: "y", **nomes})
    termos = []
    for c, ref in preditores.items():
        if ref not in set(d[nomes[c]]):
            ref = d[nomes[c]].value_counts().index[0]
        termos.append(f"C({nomes[c]}, Treatment(reference={ref!r}))")
    try:
        mod = smf.logit("y ~ " + " + ".join(termos), data=d).fit(disp=False, maxiter=200)
    except Exception:
        return None
    ic = mod.conf_int()
    linhas = []
    for nome in mod.params.index:
        if nome == "Intercept":
            continue
        m = re.match(r"C\((x\d+), .*\)\[T\.(.*)\]", nome)
        var = next(c for c, k in nomes.items() if k == m.group(1))
        linhas.append({"VARIAVEL": var, "CATEGORIA": m.group(2), "OR": float(np.exp(mod.params[nome])),
                       "LI": float(np.exp(ic.loc[nome, 0])), "LS": float(np.exp(ic.loc[nome, 1])),
                       "P": float(mod.pvalues[nome])})
    t = pd.DataFrame(linhas)
    t["SIGNIF"] = t["P"] < 0.05
    return t, int(mod.nobs), float(mod.prsquared)


# ---------------------------------------------------------------- termos característicos dos títulos
_STOP = set("""a o e é de da do das dos em no na nos nas para por pelo pela pelos pelas com sem um uma uns
umas os as ao aos à às sua seu suas seus entre sobre como que ou se sob até após ante desde mas nem não
caso estudo estudos análise analise partir perspectiva contribuição contribuicao algumas alguns
aspectos através atraves frente acerca diante dentro novo nova novos novas outro outra outros outras
município municipio municipal região regiao estado pará para amazônia amazonia amazônica amazonico
amazônico amazônicas amazônicos brasil brasileira brasileiro paraense belém belem são luís paulo mato
grosso sul norte nordeste sócio""".split())
_LIGA = {"de", "do", "da", "dos", "das"}


def _tokens(titulo):
    w = [x for x in re.findall(r"[a-záéíóúâêôãõçàü]+", str(titulo).lower()) if len(x) > 1]
    ok = lambda x: x not in _STOP and len(x) > 2  # noqa: E731
    uni = [x for x in w if ok(x)]
    bi = [f"{a} {b}" for a, b in zip(w, w[1:]) if ok(a) and ok(b)]
    tri = [f"{a} {m} {b}" for a, m, b in zip(w, w[1:], w[2:]) if m in _LIGA and ok(a) and ok(b)]
    return uni + bi + tri


@st.cache_data(show_spinner=False)
def termos_distintivos(grupos: tuple, n=10, alpha=0.5, minimo=3) -> pd.DataFrame:
    """Termos que mais distinguem cada grupo de títulos dos demais.

    Log-odds com prior de Dirichlet informativo (Monroe, Colaresi e Quinn, 2008).
    grupos: tupla de (nome_do_grupo, tupla_de_títulos) — hashável para o cache.
    """
    cont = {g: pd.Series([w for tt in tits for w in _tokens(tt)]).value_counts() for g, tits in grupos}
    cont = {g: c for g, c in cont.items() if len(c)}
    if len(cont) < 2:
        return pd.DataFrame(columns=["GRUPO", "TERMO", "Z", "FREQ"])
    tot = pd.concat(cont.values(), axis=1).fillna(0).sum(axis=1)
    a_w = alpha * tot / tot.sum() * len(tot)
    a0 = a_w.sum()
    saida = []
    for g, y_i in cont.items():
        y_i = y_i.reindex(tot.index, fill_value=0)
        y_j = tot - y_i
        n_i, n_j = y_i.sum(), y_j.sum()
        d = (np.log((y_i + a_w) / (n_i + a0 - y_i - a_w)) - np.log((y_j + a_w) / (n_j + a0 - y_j - a_w)))
        z = d / np.sqrt(1 / (y_i + a_w) + 1 / (y_j + a_w))
        cand = z[y_i >= minimo].sort_values(ascending=False).head(n * 3)
        frases = [c for c in cand.index if " " in c]
        manter = [c for c in cand.index if " " in c or not any(
            c in fr.split() and y_i[c] <= 1.5 * y_i[fr] for fr in frases)]
        for termo, sc in cand[manter].head(n).items():
            saida.append({"GRUPO": g, "TERMO": termo, "Z": round(float(sc), 2), "FREQ": int(y_i[termo])})
    return pd.DataFrame(saida)
