"""Consulta: busca de dissertações e teses e ficha acadêmica de cada egresso.

Mostra apenas informação acadêmica e a atuação declarada no Currículo Lattes, sem o nome dos egressos
(as tabelas publicadas não o trazem). Dados de folha de pagamento não aparecem individualmente.
"""
import html

import pandas as pd
import streamlit as st

from core import data, filters
from core import components as ui
from core.theme import NOME_LINHA, num

tit_all, pes_all = data.titulacoes(), data.pessoas()
r = filters.barra(tit_all, pes_all)
t = r.titulacoes

ui.secao("Dissertações e teses",
         "Busque por título do trabalho, orientador(a) ou curso de graduação. A busca respeita os filtros acima. "
         "Os nomes dos egressos não são exibidos.")
busca = st.text_input("Buscar", placeholder="Ex.: agricultura familiar, Marajó, Acevedo Marin…",
                      key="busca_consulta", label_visibility="collapsed")
v = t.copy()
if busca:
    alvo = (v["TRABALHO_CONCLUSAO"] + " " + v["ORIENTADOR"].fillna("") + " " + v["GRADUACAO"].fillna("")).str.lower()
    for termo in busca.lower().split():
        v = v[alvo.loc[v.index].str.contains(termo, regex=False)]

tabela = (v.sort_values(["ANO", "TRABALHO_CONCLUSAO"], ascending=[False, True])
          .assign(LINHA=lambda d: d["LINHA_SIGLA"].map(NOME_LINHA))
          .assign(FONTE=lambda d: d["FONTE_REGISTRO"].map({"Planilha do programa": "Planilha",
                                                           "CAPES (Coleta Sucupira)": "CAPES",
                                                           "Site do programa": "Site do programa"}))
          [["NIVEL", "ANO", "TRABALHO_CONCLUSAO", "ORIENTADOR", "LINHA", "GRADUACAO", "FONTE", "ID_PESSOA"]]
          .rename(columns={"NIVEL": "Nível", "ANO": "Ano", "TRABALHO_CONCLUSAO": "Título",
                           "ORIENTADOR": "Orientador(a)", "LINHA": "Linha de pesquisa", "GRADUACAO": "Graduação",
                           "FONTE": "Fonte do registro"}))
st.html(f'<div class="recorte"><span>{num(len(tabela))} trabalhos encontrados</span>'
        '<span>Selecione uma linha para ver a ficha do egresso</span></div>')
sel = st.dataframe(
    tabela.drop(columns="ID_PESSOA"), hide_index=True, use_container_width=True, height=440,
    on_select="rerun", selection_mode="single-row", key="tabela_consulta",
    column_config={"Ano": st.column_config.NumberColumn(format="%d", width="small"),
                   "Nível": st.column_config.TextColumn(width="small"),
                   "Título": st.column_config.TextColumn(width="large")})

c1, c2 = st.columns([1, 3], vertical_alignment="center")
c1.download_button("Baixar resultado (CSV)", tabela.drop(columns="ID_PESSOA").to_csv(index=False).encode("utf-8-sig"),
                   file_name="egressos_ppgdstu.csv", mime="text/csv", use_container_width=True)
c2.caption("O arquivo traz só os campos acadêmicos mostrados na tabela.")

linhas = sel.selection.rows if sel and sel.selection else []
if linhas:
    idp = int(tabela.iloc[linhas[0]]["ID_PESSOA"])
    pessoa = pes_all.set_index("ID_PESSOA").loc[idp]
    trabalhos = tit_all[tit_all["ID_PESSOA"] == idp].sort_values("ANO")
    esc = lambda s: html.escape(str(s)) if s is not None and str(s) != "nan" else "–"  # noqa: E731
    itens = "".join(
        f'<li><b>{esc(w.NIVEL)} · {esc(w.ANO)}</b> — {esc(w.TRABALHO_CONCLUSAO)}<br>'
        f'<span>Orientação: {esc(w.ORIENTADOR)} · Linha: {esc(NOME_LINHA.get(w.LINHA_SIGLA, w.LINHA_SIGLA))}'
        f'{" (atribuída pelo orientador)" if w.LINHA_ORIGEM == "Inferida pelo orientador" else ""}'
        f'{" (linha do orientador)" if w.LINHA_ORIGEM == "Linha do orientador (site do programa)" else ""}'
        f'{" · registro da CAPES" if w.FONTE_REGISTRO == "CAPES (Coleta Sucupira)" else ""}'
        f'{" · registro do site do programa" if w.FONTE_REGISTRO == "Site do programa" else ""}</span></li>'
        for w in trabalhos.itertuples())
    atuacao = esc(pessoa["OCUPACAO_LATTES"])
    if pessoa["IES_LATTES_SIGLA"] is not None and str(pessoa["IES_LATTES_SIGLA"]) != "nan":
        atuacao += f" · {esc(pessoa['IES_LATTES_SIGLA'])}"
    if pd.isna(pessoa["OCUPACAO_LATTES"]):
        atuacao = "Não compilada (titulação incluída a partir dos registros da CAPES)"
    elif pessoa["ATUACAO_FONTE"] not in (None, "Planilha do programa") and pd.notna(pessoa["ATUACAO_FONTE"]):
        atuacao += f" <span>· fonte: {esc(pessoa['ATUACAO_FONTE'])}</span>"
    doc = data.docencia_ppg()
    doc = doc[doc["ID_PESSOA"] == idp] if len(doc) else doc
    ano_doc = data.meta().get("docencia_ppg", {}).get("ano")
    minusc = {"da", "de", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "a", "o", "para", "com"}
    programa = lambda s: " ".join(w if w in minusc else w.capitalize()  # noqa: E731
                                  for w in str(s).split(" - ")[0].lower().split())
    docencia = "; ".join(
        f"{esc(programa(r.NM_PROGRAMA_IES))} · {esc(r.SG_ENTIDADE_ENSINO)} "
        f"<span>({esc(str(r.DS_CATEGORIA_DOCENTE).lower())})</span>" for r in doc.itertuples()) or "Não consta"
    ui.secao("Ficha do egresso", f"{esc(pessoa['TRAJETORIA'])} no PPGDSTU · última titulação em "
                                 f"{esc(pessoa['ANO_ULTIMA_TITULACAO'])}")
    st.html(f"""<div class="ficha">
<div class="ficha-col"><div class="ficha-rot">Trabalhos no PPGDSTU</div><ul>{itens}</ul></div>
<div class="ficha-col ficha-lado">
  <div class="ficha-rot">Graduação</div><p>{esc(pessoa['GRADUACAO'])} <span>({esc(pessoa['AREA_GRADUACAO'])}){(' · fonte: ' + esc(pessoa['GRADUACAO_FONTE']).lower()) if pessoa['GRADUACAO_FONTE'] not in (None, 'Planilha do programa') and pd.notna(pessoa['GRADUACAO_FONTE']) else ''}</span></p>
  <div class="ficha-rot">Atuação declarada no Currículo Lattes</div><p>{atuacao}</p>
  <div class="ficha-rot">Docente de pós-graduação (CAPES, {ano_doc})</div><p>{docencia}</p>
  <div class="ficha-rot">Trajetória no programa</div><p>{esc(pessoa['TRAJETORIA'])}</p>
</div></div>""")
