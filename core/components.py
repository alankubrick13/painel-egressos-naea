"""Peças visuais do painel: cabeçalho, navegação, indicadores, cartões de gráfico, rodapé."""
import base64
import html
import re
import unicodedata
from functools import lru_cache

import pandas as pd
import streamlit as st

from core.data import ASSETS
from core.theme import CONFIG_PLOTLY, SUPERFICIE


@lru_cache
def _img64(nome):
    return base64.b64encode((ASSETS / nome).read_bytes()).decode()


@lru_cache
def _css():
    return (ASSETS / "styles.css").read_text(encoding="utf-8")


def estilo():
    st.html(f"<style>{_css()}</style>")


def cabecalho(meta):
    st.html(f"""
<header class="masthead">
  <div class="mh-marca">
    <img class="mh-naea" src="data:image/png;base64,{_img64('naea.png')}" alt="Logotipo do NAEA">
    <div class="mh-texto">
      <div class="mh-inst">Universidade Federal do Pará · Núcleo de Altos Estudos Amazônicos</div>
      <h1 class="mh-titulo">Egressos do PPGDSTU</h1>
      <div class="mh-sub">Programa de Pós-Graduação em Desenvolvimento Sustentável do Trópico Úmido
        · defesas de {meta['primeiro_ano']} a {meta['ultimo_ano']}</div>
    </div>
  </div>
  <img class="mh-ufpa" src="data:image/png;base64,{_img64('ufpa_descritivo.png')}" alt="Brasão da UFPA">
</header>
<div class="mh-regua"><span></span><span></span></div>
""")


def navegacao(paginas, atual):
    with st.container(key="nav", horizontal=True, gap="small"):
        for i, p in enumerate(paginas):
            estado = "on" if p.url_path == atual.url_path else "off"
            with st.container(key=f"navitem-{estado}-{i}", width="content"):
                st.page_link(p)


def secao(titulo, texto=None):
    corpo = f'<p class="secao-texto">{texto}</p>' if texto else ""
    st.html(f'<div class="secao"><h2>{titulo}</h2>{corpo}</div>')


def destaque(valor, rotulo, detalhe):
    """Número principal da página (um por página)."""
    st.html(f"""<div class="hero"><div class="hero-valor">{valor}</div>
<div class="hero-rotulo">{rotulo}</div><div class="hero-detalhe">{detalhe}</div></div>""")


def indicadores(itens):
    """Fileira de indicadores. itens: lista de (rótulo, valor, nota)."""
    blocos = "".join(
        f'<div class="kpi"><div class="kpi-rotulo">{html.escape(str(r))}</div>'
        f'<div class="kpi-valor">{html.escape(str(v))}</div>'
        f'<div class="kpi-nota">{html.escape(str(n))}</div></div>' for r, v, n in itens)
    colunas = 4 if len(itens) in (4, 7, 8) else 3
    st.html(f'<div class="kpis kpis-{colunas}">{blocos}</div>')


def ressalva(texto):
    st.html(f'<div class="ressalva"><span class="ressalva-marca">Nota</span><span>{texto}</span></div>')


def grafico(fig, titulo, subtitulo, fonte, tabela: pd.DataFrame | None = None, chave=None,
            altura=None):
    """Cartão com título-afirmação, subtítulo (base e n), gráfico, tabela gêmea e fonte."""
    with st.container(border=True, key=f"card-{_slug(chave)}" if chave else None):
        st.html(f'<div class="card-titulo">{html.escape(titulo)}</div>'
                f'<div class="card-sub">{html.escape(subtitulo)}</div>')
        # o Streamlit troca o modelo padrão do Plotly e pinta fundos transparentes com a cor da página
        fig.update_layout(template="naea", paper_bgcolor=SUPERFICIE, plot_bgcolor=SUPERFICIE)
        if altura:
            fig.update_layout(height=altura)
        if tabela is not None:
            aba_g, aba_t = st.tabs(["Gráfico", "Tabela"])
            with aba_g:
                st.plotly_chart(fig, use_container_width=True, config=CONFIG_PLOTLY, theme=None)
            with aba_t:
                st.dataframe(tabela, hide_index=True, use_container_width=True)
        else:
            st.plotly_chart(fig, use_container_width=True, config=CONFIG_PLOTLY, theme=None)
        st.html(f'<div class="card-fonte">{html.escape(fonte)}</div>')


def _slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def texto_seguro(s):
    return html.escape(str(s))


def rodape(meta):
    st.html(f"""
<div class="rodape">
  <div>
    <b>Núcleo de Altos Estudos Amazônicos – NAEA/UFPA</b><br>
    Programa de Pós-Graduação em Desenvolvimento Sustentável do Trópico Úmido (PPGDSTU)
  </div>
  <div>
    <b>Fontes</b>: quadro geral de egressos da coordenação do PPGDSTU; Currículo Lattes;
    Portal da Transparência (SIAPE, competência {meta['competencia_folha']}); folhas públicas do
    Pará; CAPES – Dados Abertos (discentes, Coleta Sucupira); Repositório Institucional da UFPA.
    Detalhes na página <i>Metodologia</i>.
  </div>
</div>
""")
