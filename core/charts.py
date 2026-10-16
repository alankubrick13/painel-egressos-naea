"""Gráficos reutilizáveis, todos no modelo visual 'naea' (core/theme.py)."""
import math
import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.theme import (APAGADO, BASE, COR_NIVEL, ESCALA_VERDE_MAPA, FONTE, GRADE, ORDEM_NIVEL,
                        SUPERFICIE, TINTA, TINTA_2, TINTA_3, VERDE_NAEA, num, pct)

GAP = dict(color=SUPERFICIE, width=1.5)   # 2px de "respiro" entre segmentos empilhados


def quebrar(s, largura=30):
    return "<br>".join(textwrap.wrap(str(s), largura)) or str(s)


def barras_h(rotulos, valores, total=None, cor=VERDE_NAEA, destaque=None, largura_rotulo=30,
             sufixo="", formato_valor=None):
    """Barras horizontais de uma série (mesma cor em todas), valor na ponta.

    destaque: rótulo a pintar no verde e o resto em cinza (ênfase), opcional.
    """
    rot = [quebrar(r, largura_rotulo) for r in rotulos]
    vals = list(valores)
    if formato_valor is None:
        def formato_valor(v):
            base = num(v)
            return f"{base}{sufixo}" + (f"  ·  {pct(v / total)}" if total else "")
    cores = [cor if destaque is None or r == destaque else APAGADO for r in rotulos]
    fig = go.Figure(go.Bar(
        x=vals, y=rot, orientation="h", marker=dict(color=cores, line=GAP),
        text=[formato_valor(v) for v in vals], textposition="outside", cliponaxis=False,
        textfont=dict(size=12, color=TINTA_2),
        hovertemplate="<b>%{text}</b><br>%{y}<extra></extra>",
    ))
    n = len(rot)
    linhas_max = max((r.count("<br>") + 1 for r in rot), default=1)
    altura = max(160, n * (30 + 9 * (linhas_max - 1)) + 30)
    fig.update_layout(
        height=altura, bargap=0.38, showlegend=False,
        xaxis=dict(visible=False, range=[0, max(vals or [1]) * 1.45]),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=12.5, color=TINTA_2),
                   ticklabelstandoff=8),
        margin=dict(l=4, r=8, t=4, b=4),
    )
    return fig


def colunas_por_ano(t, anos, parcial=None):
    """Colunas empilhadas por nível, um ano por coluna.

    parcial: dict {ano: texto} para anos com registro incompleto (barra esmaecida + nota).
    """
    tab = (t.groupby(["ANO", "NIVEL"]).size().unstack(fill_value=0)
           .reindex(index=anos, columns=ORDEM_NIVEL, fill_value=0))
    parcial = parcial or {}
    fig = go.Figure()
    for nivel in ORDEM_NIVEL:
        if tab[nivel].sum() == 0:
            continue
        opac = [0.45 if a in parcial else 1 for a in tab.index]
        nome = "Dissertações (mestrado)" if nivel == "Mestrado" else "Teses (doutorado)"
        fig.add_bar(x=tab.index, y=tab[nivel], name=nome,
                    marker=dict(color=COR_NIVEL[nivel], opacity=opac, line=GAP),
                    hovertemplate=f"<b>%{{y}}</b> {nome.split(' ')[0].lower()}<extra></extra>")
    total = tab.sum(axis=1)
    topo = max(total.max(), 1) * 1.28
    for a, texto in parcial.items():
        if a in tab.index:
            fig.add_annotation(x=a, y=total[a], text=texto, showarrow=True, arrowhead=0, arrowwidth=1,
                               arrowcolor=BASE, axref="x", ayref="y", ax=a - 0.6, ay=topo * 0.93,
                               xanchor="right", yanchor="middle", align="right",
                               font=dict(size=11.5, color=TINTA_2))
    fig.update_layout(
        barmode="stack", bargap=0.28, height=330, hovermode="x unified",
        legend=dict(y=1.02), margin=dict(l=4, r=8, t=30, b=4),
        xaxis=dict(dtick=5 if len(anos) > 15 else 1, tickformat="d", showspikes=False),
        yaxis=dict(title_text="", range=[0, topo]),
        hoverlabel=dict(namelength=-1),
    )
    fig.update_xaxes(hoverformat="d")
    return fig, tab


def mapa_uf(contagem: pd.Series, malha: dict, total_conhecido: int):
    """Coroplético por UF, escala logarítmica em verde (o Pará domina a escala linear)."""
    todas = [f["properties"]["UF"] for f in malha["features"]]
    base = go.Choropleth(
        geojson=malha, featureidkey="properties.UF", locations=todas, z=[0] * len(todas),
        colorscale=[[0, "#F1F0EB"], [1, "#F1F0EB"]], showscale=False,
        marker=dict(line=dict(color=SUPERFICIE, width=0.8)), hoverinfo="skip")
    c = contagem[contagem > 0]
    z = np.log10(c.values)
    ticks = [v for v in (1, 3, 10, 30, 100, 300, 1000) if v <= max(c.max(), 1) * 1.01]
    camada = go.Choropleth(
        geojson=malha, featureidkey="properties.UF", locations=c.index, z=z,
        zmin=0, zmax=max(math.log10(max(c.max(), 2)), 0.5),
        colorscale=ESCALA_VERDE_MAPA, marker=dict(line=dict(color=SUPERFICIE, width=0.8)),
        customdata=np.stack([c.values, c.values / max(total_conhecido, 1) * 100], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b> egressos · %{customdata[1]:.1f}%<br>%{location}<extra></extra>",
        colorbar=dict(orientation="h", thickness=8, len=0.55, x=0.5, xanchor="center", y=-0.02,
                      yanchor="top", outlinewidth=0, tickvals=[math.log10(v) for v in ticks],
                      ticktext=[str(v) for v in ticks], tickfont=dict(size=11, color=TINTA_3),
                      title=dict(text="egressos (escala log)", side="top", font=dict(size=11, color=TINTA_3))),
    )
    fig = go.Figure([base, camada])
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator",
                    bgcolor=SUPERFICIE)
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=40), dragmode=False)
    return fig


# ====================================================================== composição e cruzamentos
def colunas_100(tab: pd.DataFrame, cores: dict, nomes: dict | None = None, horizontal=False,
                altura=330, ordem=None, largura_rotulo=16):
    """Barras 100% empilhadas. tab: linhas = categorias do eixo, colunas = séries (contagens)."""
    nomes = nomes or {}
    ordem = [c for c in (ordem or tab.columns) if c in tab.columns and tab[c].sum() > 0]
    tot = tab[ordem].sum(axis=1).replace(0, np.nan)
    fig = go.Figure()
    eixo = [quebrar(i, largura_rotulo) for i in tab.index]
    for c in ordem:
        share = tab[c] / tot * 100
        nome = nomes.get(c, c)
        kw = dict(x=share, y=eixo, orientation="h") if horizontal else dict(x=eixo, y=share)
        fig.add_bar(name=nome, marker=dict(color=cores.get(c, APAGADO), line=GAP),
                    customdata=np.stack([tab[c].values], axis=-1),
                    hovertemplate=(f"<b>%{{{'x' if horizontal else 'y'}:.1f}}%</b> {nome}"
                                   " (%{customdata[0]})<extra></extra>"), **kw)
    fig.update_layout(barmode="stack", height=altura, bargap=0.3,
                      hovermode="y unified" if horizontal else "x unified",
                      legend=dict(y=1.02, traceorder="normal"), margin=dict(l=4, r=8, t=34, b=4))
    eixo_val = dict(range=[0, 100], ticksuffix="%", showgrid=True, gridcolor=GRADE)
    if horizontal:
        fig.update_layout(xaxis=eixo_val, yaxis=dict(autorange="reversed", showgrid=False,
                                                     ticklabelstandoff=8))
    else:
        fig.update_layout(yaxis=eixo_val, xaxis=dict(type="category"))
    return fig


def mapa_calor(z: pd.DataFrame, formato="{:.0f}%", escala=None, altura=None, rotulo_valor="%",
               zmin=None, zmax=None, largura_x=14, largura_y=30, texto: pd.DataFrame | None = None,
               divergente=False):
    """Mapa de calor com valor escrito em cada célula (tinta clara ou escura conforme o fundo)."""
    from core.theme import ESCALA_DIVERGENTE, ESCALA_VERDE
    escala = escala or (ESCALA_DIVERGENTE if divergente else ESCALA_VERDE)
    xs = [quebrar(c, largura_x) for c in z.columns]
    ys = [quebrar(i, largura_y) for i in z.index]
    vals = z.values.astype(float)
    if zmax is None:
        zmax = np.nanmax(np.abs(vals)) if divergente else np.nanmax(vals)
    if zmin is None:
        zmin = -zmax if divergente else 0
    fig = go.Figure(go.Heatmap(
        z=vals, x=xs, y=ys, colorscale=escala, zmin=zmin, zmax=zmax, xgap=2, ygap=2,
        showscale=False, hovertemplate="%{y}<br>%{x}<br><b>%{z:.1f}" + rotulo_valor + "</b><extra></extra>"))
    txt = texto.values if texto is not None else vals
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            v = vals[i, j]
            if np.isnan(v):
                continue
            intens = abs(v) / zmax if divergente else (v - zmin) / max(zmax - zmin, 1e-9)
            cor = "#FFFFFF" if intens > 0.55 else TINTA
            rot = txt[i, j] if texto is not None else formato.format(v)
            fig.add_annotation(x=x, y=y, text=str(rot), showarrow=False,
                               font=dict(size=11.5, color=cor))
    fig.update_layout(
        height=altura or max(220, 40 * len(ys) + 70),
        xaxis=dict(side="top", showline=False, tickfont=dict(size=11.5, color=TINTA_2), type="category"),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=12, color=TINTA_2),
                   ticklabelstandoff=6, type="category"),
        margin=dict(l=4, r=4, t=8, b=4))
    return fig


def sankey(rotulos, cores_nos, fontes, alvos, valores, cores_links, altura=520):
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=rotulos, color=cores_nos, pad=14, thickness=14, line=dict(color=SUPERFICIE, width=1),
                  hovertemplate="<b>%{value}</b> pessoas<br>%{label}<extra></extra>"),
        link=dict(source=fontes, target=alvos, value=valores, color=cores_links,
                  hovertemplate="<b>%{value}</b> pessoas<br>%{source.label} → %{target.label}<extra></extra>"),
        textfont=dict(family=FONTE, size=12, color=TINTA, shadow="1px 1px 2px #FFFFFF, -1px -1px 2px #FFFFFF")))
    fig.update_layout(height=altura, margin=dict(l=4, r=4, t=8, b=8))
    return fig


def linha_unica(x, y, rotulo_y="%", cor=VERDE_NAEA, sufixo="%", altura=280, casas=0):
    """Uma série no tempo, com o último valor rotulado na ponta."""
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="lines+markers", line=dict(color=cor, width=2),
        marker=dict(size=8, color=cor, line=dict(color=SUPERFICIE, width=2)),
        hovertemplate=f"<b>%{{y:.{casas}f}}{sufixo}</b><br>%{{x}}<extra></extra>"))
    if len(x):
        fig.add_annotation(x=x[-1], y=y[-1], text=f"{num(y[-1], casas)}{sufixo}", showarrow=False,
                           xanchor="left", xshift=10, font=dict(size=12, color=TINTA))
    fig.update_layout(height=altura, showlegend=False, xaxis=dict(type="category"),
                      yaxis=dict(rangemode="tozero", ticksuffix=sufixo), margin=dict(l=4, r=40, t=12, b=4))
    return fig


def histograma(valores_por_bin: pd.Series, cor=VERDE_NAEA, cores=None, altura=280, rotulo_x="",
               hover="pessoas"):
    fig = go.Figure(go.Bar(
        x=valores_por_bin.index, y=valores_por_bin.values,
        marker=dict(color=cores or cor, line=GAP),
        hovertemplate=f"<b>%{{y}}</b> {hover}<br>%{{x}}<extra></extra>"))
    fig.update_layout(height=altura, bargap=0.12, showlegend=False,
                      xaxis=dict(title_text=rotulo_x), margin=dict(l=4, r=8, t=8, b=4))
    return fig


# ====================================================================== mapas
def mapa_bolhas(df: pd.DataFrame, malha_uf: dict, destaque_ufs=None, altura=520):
    """Bolhas por município (tamanho ~ raiz do número de egressos) sobre o contorno das UFs."""
    todas = [f["properties"]["UF"] for f in malha_uf["features"]]
    destaque_ufs = set(destaque_ufs or [])
    fundo = go.Choropleth(
        geojson=malha_uf, featureidkey="properties.UF", locations=todas,
        z=[1 if u in destaque_ufs else 0 for u in todas],
        colorscale=[[0, "#F1F0EB"], [1, "#E4EFE3"]], zmin=0, zmax=1, showscale=False,
        marker=dict(line=dict(color="#FFFFFF", width=0.9)), hoverinfo="skip")
    n = df["N"].astype(float)
    tam = np.sqrt(n) / np.sqrt(max(n.max(), 1)) * 46 + 6
    bolhas = go.Scattergeo(
        lon=df["LON"], lat=df["LAT"], mode="markers",
        marker=dict(size=tam, color=VERDE_NAEA, opacity=0.78, line=dict(color=SUPERFICIE, width=1.5),
                    sizemode="diameter"),
        customdata=np.stack([df["MUNICIPIO"], df["UF"], df["N"]], axis=-1),
        hovertemplate="<b>%{customdata[2]}</b> egressos<br>%{customdata[0]} – %{customdata[1]}<extra></extra>")
    fig = go.Figure([fundo, bolhas])
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator", bgcolor=SUPERFICIE)
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=0, b=0), dragmode=False, showlegend=False)
    return fig


def mapa_municipios(contagem: pd.Series, malha: dict, altura=560, bolhas: pd.DataFrame | None = None):
    """Coroplético municipal (código IBGE -> egressos), escala log em verde; sem egressos em cinza."""
    from core.theme import ESCALA_VERDE_MAPA
    cods = [f["properties"]["COD"] for f in malha["features"]]
    nomes = {f["properties"]["COD"]: f["properties"]["NOME"] for f in malha["features"]}
    base = go.Choropleth(
        geojson=malha, featureidkey="properties.COD", locations=cods, z=[0] * len(cods),
        colorscale=[[0, "#F1F0EB"], [1, "#F1F0EB"]], showscale=False,
        marker=dict(line=dict(color=SUPERFICIE, width=0.5)),
        customdata=[nomes[c] for c in cods], hovertemplate="%{customdata}<br>sem egressos<extra></extra>")
    c = contagem[contagem > 0]
    zmax = max(math.log10(max(c.max(), 2)), 0.5) if len(c) else 1
    ticks = [v for v in (1, 3, 10, 30, 100, 300) if v <= max(c.max() if len(c) else 1, 1) * 1.01]
    camada = go.Choropleth(
        geojson=malha, featureidkey="properties.COD", locations=c.index, z=np.log10(c.values),
        zmin=0, zmax=zmax, colorscale=ESCALA_VERDE_MAPA, marker=dict(line=dict(color=SUPERFICIE, width=0.5)),
        customdata=np.stack([[nomes.get(i, i) for i in c.index], c.values], axis=-1),
        hovertemplate="<b>%{customdata[1]}</b> egressos<br>%{customdata[0]}<extra></extra>",
        colorbar=dict(orientation="h", thickness=8, len=0.5, x=0.5, xanchor="center", y=-0.01, yanchor="top",
                      outlinewidth=0, tickvals=[math.log10(v) for v in ticks], ticktext=[str(v) for v in ticks],
                      tickfont=dict(size=11, color=TINTA_3),
                      title=dict(text="egressos (escala log)", side="top", font=dict(size=11, color=TINTA_3))))
    camadas = [base, camada]
    if bolhas is not None and len(bolhas):      # círculos proporcionais: municípios pequenos e populosos aparecem
        n = bolhas["N"].astype(float)
        camadas.append(go.Scattergeo(
            lon=bolhas["LON"], lat=bolhas["LAT"], mode="markers", showlegend=False,
            marker=dict(size=np.sqrt(n) / np.sqrt(max(n.max(), 1)) * 40 + 5, color="rgba(0,0,0,0)",
                        line=dict(color=TINTA, width=1.2), sizemode="diameter"),
            customdata=np.stack([bolhas["MUNICIPIO"], bolhas["N"]], axis=-1),
            hovertemplate="<b>%{customdata[1]}</b> egressos<br>%{customdata[0]}<extra></extra>"))
    fig = go.Figure(camadas)
    fig.update_geos(fitbounds="geojson", visible=False, projection_type="mercator", bgcolor=SUPERFICIE)
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=0, b=36), dragmode=False)
    return fig


# ====================================================================== estatística
def faixa_mediana(df: pd.DataFrame, cor=VERDE_NAEA, prefixo="R$ ", altura=None):
    """Média (losango, com valor), mediana (círculo vazado) e metade central (traço) por grupo.

    df: GRUPO, P25, MEDIANA, P75, N e, opcionalmente, MEDIA.
    """
    ys = [quebrar(g, 30) for g in df["GRUPO"]]
    tem_media = "MEDIA" in df
    fig = go.Figure()
    for i, (y, r) in enumerate(zip(ys, df.itertuples())):
        fig.add_trace(go.Scatter(x=[r.P25, r.P75], y=[y, y], mode="lines", line=dict(color=APAGADO, width=6),
                                 name="Metade central", legendgroup="faixa",
                                 showlegend=i == 0, hoverinfo="skip"))
    cd = np.stack([df["P25"], df["P75"], df["N"]], axis=-1)
    fig.add_trace(go.Scatter(
        x=df["MEDIANA"], y=ys, mode="markers", name="Mediana",
        marker=dict(size=11, color=SUPERFICIE, line=dict(color=TINTA_2, width=2)),
        customdata=cd,
        hovertemplate=("<b>" + prefixo + "%{x:,.0f}</b> mediana<br>metade entre " + prefixo +
                       "%{customdata[0]:,.0f} e " + prefixo + "%{customdata[1]:,.0f}<br>%{customdata[2]} pessoas"
                       "<extra></extra>")))
    if tem_media:
        fig.add_trace(go.Scatter(
            x=df["MEDIA"], y=ys, mode="markers+text", name="Média",
            marker=dict(size=13, symbol="diamond", color=cor, line=dict(color=SUPERFICIE, width=2)),
            text=[f"{prefixo}{num(v)}" for v in df["MEDIA"]], textposition="bottom center",
            textfont=dict(size=11.5, color=TINTA), customdata=cd,
            hovertemplate="<b>" + prefixo + "%{x:,.0f}</b> média<br>%{customdata[2]} pessoas<extra></extra>"))
    fig.update_layout(height=altura or max(220, 60 * len(ys) + 80), hovermode="closest",
                      legend=dict(y=1.02, traceorder="reversed"),
                      # folga embaixo para o rótulo da última linha não encostar no eixo
                      yaxis=dict(range=[len(ys) - 0.35, -0.6], showgrid=False, ticklabelstandoff=8),
                      xaxis=dict(showgrid=True, gridcolor=GRADE, tickprefix=prefixo, showline=False),
                      margin=dict(l=4, r=16, t=40, b=4))
    return fig


def floresta(df: pd.DataFrame, altura=None):
    """Razões de chance com IC 95% em escala log. df: TERMO, OR, LI, LS, SIGNIF."""
    ys = [quebrar(t, 34) for t in df["TERMO"]]
    cores = [VERDE_NAEA if s else APAGADO for s in df["SIGNIF"]]
    fig = go.Figure()
    fig.add_vline(x=1, line=dict(color=BASE, width=1))
    for y, r in zip(ys, df.itertuples()):
        fig.add_trace(go.Scatter(x=[r.LI, r.LS], y=[y, y], mode="lines", line=dict(color=APAGADO, width=2),
                                 hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=df["OR"], y=ys, mode="markers", marker=dict(size=11, color=cores, line=dict(color=SUPERFICIE, width=2)),
        customdata=np.stack([df["LI"], df["LS"]], axis=-1), showlegend=False,
        hovertemplate="<b>%{x:.2f}</b> (razão de chances)<br>IC 95%: %{customdata[0]:.2f} a %{customdata[1]:.2f}"
                      "<extra></extra>"))
    fig.update_layout(height=altura or max(220, 40 * len(ys) + 60),
                      xaxis=dict(type="log", showgrid=True, gridcolor=GRADE, showline=False,
                                 tickvals=[0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20],
                                 ticktext=["0,05", "0,1", "0,2", "0,5", "1", "2", "5", "10", "20"],
                                 title_text="razão de chances (escala log; 1 = sem efeito)"),
                      yaxis=dict(autorange="reversed", showgrid=False, ticklabelstandoff=8),
                      margin=dict(l=4, r=16, t=8, b=4))
    return fig
