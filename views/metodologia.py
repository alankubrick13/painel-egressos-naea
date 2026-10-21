"""Metodologia e qualidade dos dados: de onde vêm os números e quanto confiar neles."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import charts, data
from core import components as ui
from core.theme import APAGADO, VERDE_NAEA, num, pct

tit, pes, meta, val = data.titulacoes(), data.pessoas(), data.meta(), data.validacao_capes()

comp = meta.get("complemento_capes", {})
inc = [str(a) for a in meta.get("anos_incompletos_na_planilha", [])]
anos_inc = ", ".join(inc[:-1]) + " e " + inc[-1] if len(inc) > 1 else "".join(inc)
n_plan = int((tit["FONTE_REGISTRO"] == "Planilha do programa").sum())
av = meta.get("anos_validados_capes", [])
anos_val = f"{av[0]} a {av[-1]}" if av else "–"
rec = sorted({str(a) for a in meta.get("anos_catalogo_capes", []) + meta.get("anos_site_programa", [])})
anos_rec = ", ".join(rec[:-1]) + " e " + rec[-1] if len(rec) > 1 else "".join(rec)
n_site = meta.get("titulacoes_por_fonte", {}).get("Site do programa", 0)
txt_catalogo = (f"""<p><b>Defesas recentes.</b> Os dados abertos da CAPES saem com cerca de um ano de atraso e ainda
não trazem {anos_rec}. Essas defesas vieram da lista de teses e dissertações publicada no site do PPGDSTU
({num(n_site)} trabalhos) e do Catálogo de Teses e Dissertações da CAPES, que, com a página do trabalho na
Plataforma Sucupira, informa a data de defesa e a linha de pesquisa. Quando a linha não vem da Sucupira, vale a
linha atual do(a) orientador(a) segundo o site do programa. A conferência com a CAPES será refeita quando os dados
abertos de {anos_rec} forem publicados.</p>""" if rec else "")

ui.secao("Como os números foram construídos")
st.html(f"""<div class="prosa">
<p><b>Base de titulações.</b> O ponto de partida é o quadro geral de egressos mantido pela coordenação do
PPGDSTU: uma linha por dissertação ou tese, com orientador(a), linha de pesquisa, curso de graduação e um
resumo do Currículo Lattes ({num(n_plan)} titulações após a limpeza). A ela foram somadas
<b>{num(comp.get('titulacoes', 0))} titulações</b> que a CAPES{' ou o site do programa' if n_site else ''}
registra{'m' if n_site else ''} como do programa e que não estavam na planilha. O painel reúne <b>{num(meta['titulacoes'])} titulações</b> de <b>{num(meta['pessoas'])} pessoas</b>,
defendidas entre {meta['primeiro_ano']} e {meta['ultimo_ano']}.</p>
<p><b>Destino profissional.</b> A ocupação declarada no Lattes foi complementada por cruzamentos nominais
com fontes oficiais, em rodadas sucessivas: folha federal (SIAPE, Portal da Transparência, competência
{meta['competencia_folha']}), folha do Governo do Pará, Tribunal de Justiça, Ministério Público e Tribunal
de Contas do Pará, Prefeitura de Belém, e os registros de docentes e discentes da CAPES. Nomes
homônimos foram descartados ou marcados para conferência.</p>
<p><b>Conferência externa.</b> As datas de defesa foram comparadas com os titulados do programa registrados
pela CAPES (Coleta Sucupira, {anos_val}) e com o Repositório Institucional da UFPA. A conferência corrigiu o
ano de {len(meta.get('correcoes_de_ano', []))} trabalhos e mostrou que a planilha estava incompleta,
sobretudo em {anos_inc}. As titulações que faltavam foram incorporadas (lista abaixo).</p>{txt_catalogo}
</div>""")

# ---------------------------------------------------------------- planilha x CAPES
ui.secao("Conferência com a CAPES")
v = val.groupby("ANO")[["PLANILHA", "CAPES", "SO_NA_CAPES", "SO_NA_PLANILHA"]].sum()
pareadas = (v["PLANILHA"] - v["SO_NA_PLANILHA"]).sum()
concord = pareadas / max(v["PLANILHA"].sum(), 1)
fig = go.Figure()
fig.add_bar(x=v.index.astype(str), y=v["PLANILHA"], name="Planilha original do programa",
            marker=dict(color=VERDE_NAEA, line=charts.GAP),
            hovertemplate="<b>%{y}</b> na planilha<extra></extra>")
fig.add_bar(x=v.index.astype(str), y=v["CAPES"], name="CAPES (Coleta Sucupira)",
            marker=dict(color=APAGADO, line=charts.GAP),
            hovertemplate="<b>%{y}</b> na CAPES<extra></extra>")
fig.update_layout(barmode="group", height=300, bargap=0.35, bargroupgap=0.08, hovermode="x unified",
                  legend=dict(y=1.04), margin=dict(l=4, r=8, t=30, b=4), xaxis=dict(type="category"))
tabela = v.reset_index().rename(columns={
    "ANO": "Ano", "PLANILHA": "Planilha", "CAPES": "CAPES", "SO_NA_CAPES": "Só na CAPES (incorporadas)",
    "SO_NA_PLANILHA": "Só na planilha"})
ui.grafico(fig, f"Nos {len(v)} anos conferidos, {pct(concord, 0)} das titulações da planilha estão na CAPES; "
                f"faltavam registros sobretudo em {anos_inc}",
           "Titulações por ano, antes do complemento: planilha original do programa e titulados do PPGDSTU na CAPES",
           "Fonte: CAPES – Dados Abertos, discentes da pós-graduação (programa 15001016002P5). Anos anteriores a "
           "2004 não existem nos dados abertos da CAPES. A comparação considera nome, título do trabalho e "
           "variações de grafia.", tabela, chave="capes")

corr = pd.DataFrame(meta.get("correcoes_de_ano", []))
if len(corr):
    with st.container(border=True, key="card-correcoes"):
        st.html('<div class="card-titulo">Anos de defesa corrigidos</div>'
                f'<div class="card-sub">{len(corr)} datas corrigidas. Quatro teses estavam lançadas duas vezes '
                '(2015 e 2016) e foram defendidas em 2016, segundo o Repositório Institucional da UFPA e a '
                'CAPES; as demais divergiam das duas fontes.</div>')
        st.dataframe(corr.drop(columns=["EGRESSO"], errors="ignore").rename(columns={
                         "TRABALHO": "Trabalho", "NIVEL": "Nível", "ANO_PLANILHA": "Ano na planilha",
                         "ANO_CORRIGIDO": "Ano adotado", "FONTE": "Fonte"}),
                     hide_index=True, use_container_width=True)

inc_df = data.capes_incorporadas()
if len(inc_df):
    with st.container(border=True, key="card-incorporadas"):
        st.html('<div class="card-titulo">Titulações incorporadas a partir da CAPES'
                f'{" e do site do programa" if n_site else ""}</div>'
                f'<div class="card-sub">{num(len(inc_df))} trabalhos que não estavam na planilha do programa. '
                f'{num(comp.get("pessoas_existentes", 0))} são de pessoas que já estavam na base (por exemplo, o '
                f'doutorado de quem tinha só o mestrado registrado); {num(comp.get("pessoas_novas", 0))} pessoas '
                f'entraram na base, das quais {num(comp.get("localizados", 0))} foram localizadas em fontes '
                'oficiais. A lista com os nomes, para atualizar a planilha, está na base consolidada da '
                'coordenação.</div>')
        st.dataframe(inc_df.drop(columns=["NOME"], errors="ignore").assign(LINHA_ORIGEM=inc_df["LINHA_ORIGEM"].replace(
                         {"Inferida pelo orientador": "Atribuída pelo orientador",
                          "Linha do orientador (site do programa)": "Linha do(a) orientador(a) no site"}),
                                   FONTE=inc_df.get("FONTE", pd.Series(index=inc_df.index, dtype=str)).replace(
                         {"CAPES (Coleta Sucupira)": "CAPES"})).rename(columns={
                         "NOME": "Nome", "NIVEL": "Nível", "ANO": "Ano", "TITULO": "Título", "ORIENTADOR": "Orientador(a)",
                         "LINHA": "Linha", "LINHA_ORIGEM": "Origem da linha", "PESSOA": "Pessoa", "FONTE": "Fonte"}),
                     hide_index=True, use_container_width=True, height=340)
        st.html('<div class="card-fonte">Fonte: CAPES – Dados Abertos, discentes da pós-graduação (situação '
                f'“titulado”, {anos_val})'
                + (f'; defesas de {anos_rec}: site do PPGDSTU, Catálogo de Teses e Dissertações e Plataforma '
                   'Sucupira' if rec else '')
                + '. Os dados abertos não informam linha de pesquisa; nenhuma dessas fontes informa a '
                'graduação.</div>')

# ---------------------------------------------------------------- localização
ui.secao("Localização profissional")
c1, c2 = st.columns(2, gap="medium")
with c1:
    tr = pes["TIPO_REGISTRO"].value_counts()
    ordem = ["Folha federal – ativo", "Folha federal – aposentado", "Folha estadual (PA)",
             "Outras folhas (TJ, MP, TCE, Prefeitura)", "Folha pública (confirmado pela coordenação)",
             "Docente de pós-graduação (CAPES)", "Discente de pós-graduação (CAPES)", "Não localizado"]
    tr = tr.reindex([o for o in ordem if o in tr.index])
    fig = charts.barras_h(tr.index, tr.values, total=tr.sum(), largura_rotulo=28, destaque=None)
    fig.data[0].marker.color = [APAGADO if i == "Não localizado" else VERDE_NAEA for i in tr.index]
    loc = pes["LOCALIZADO"].eq("Sim").mean()
    ui.grafico(fig, f"{pct(loc, 0)} dos egressos foram localizados em ao menos uma fonte oficial",
               "Pessoas por fonte em que foram localizadas (a primeira que confirmou o vínculo)",
               "Fontes: Portal da Transparência (SIAPE), folhas públicas do Pará, TJPA, MPPA, TCE-PA, "
               "Prefeitura de Belém e CAPES.",
               pd.DataFrame({"Fonte": tr.index, "Pessoas": tr.values}), chave="fontes")
with c2:
    pg = pes["PRECISAO_GEO"].value_counts().reindex(
        ["Município declarado (Lattes)", "Município da unidade (SIAPE)", "Sede da instituição",
         "Somente UF (SIAPE)", "Sem localização"]).dropna().astype(int)
    fig = charts.barras_h(pg.index, pg.values, total=pg.sum(), largura_rotulo=28)
    fig.data[0].marker.color = [APAGADO if i == "Sem localização" else VERDE_NAEA for i in pg.index]
    ui.grafico(fig, f"O local de atuação é conhecido para {pct(pes['UF_ATUACAO'].notna().mean(), 0)} das pessoas",
               "Pessoas pela precisão do local de atuação usado nos mapas",
               "Ordem de preferência: município declarado no Lattes; município da unidade (campus, agência) ou UF de exercício "
               "no SIAPE; sede da instituição.",
               pd.DataFrame({"Precisão": pg.index, "Pessoas": pg.values}), chave="geo")

# ---------------------------------------------------------------- completude
ui.secao("Completude dos campos")
campos = {
    "Linha de pesquisa": tit["LINHA"].ne("Não informada").mean(),
    "Curso de graduação": tit["GRADUACAO"].notna().mean(),
    "Ocupação (Lattes)": pes["OCUPACAO_LATTES"].notna().mean(),
    "Instituição de atuação": pes["INSTITUICAO_ATUACAO"].notna().mean(),
    "Local de atuação (UF)": pes["UF_ATUACAO"].notna().mean(),
    "Vínculo em fonte oficial": pes["LOCALIZADO"].eq("Sim").mean(),
    "Ano de ingresso no serviço público": pes["MOMENTO_INGRESSO"].notna().mean(),
}
s = pd.Series(campos).sort_values(ascending=False)
fig = charts.barras_h(s.index, s.values * 100, largura_rotulo=34,
                      formato_valor=lambda x: f"{num(x, 0)}%")
fig.update_layout(xaxis=dict(range=[0, 125]))
form = min(campos["Linha de pesquisa"], campos["Curso de graduação"])
ui.grafico(fig, ("Os dados de formação estão quase completos; os de destino profissional têm lacunas" if form >= 0.9
                 else "Completude dos principais campos"),
           "Percentual de registros com cada informação preenchida",
           "Linha e graduação: base de titulações. Demais campos: base de pessoas.",
           pd.DataFrame({"Campo": s.index, "% preenchido": (s.values * 100).round(1)}), chave="completude")

# ---------------------------------------------------------------- decisões
ui.secao("Decisões e limitações")
st.html(f"""<div class="prosa"><ul>
<li><b>Linhas de pesquisa.</b> “Desenvolvimento Regional e Agrário” é o nome antigo de “Desenvolvimento
Econômico, Regional e Agrário”; as duas aparecem somadas. O rótulo original continua na base.</li>
<li><b>Titulações fora da planilha.</b> Os dados abertos da CAPES e o site do programa não trazem linha de
pesquisa. Nesses {num(comp.get('titulacoes', 0))} trabalhos, a linha vem da Plataforma Sucupira
({num(comp.get('linha_sucupira', 0))}), é a do(a) orientador(a) segundo o site do programa, para as defesas
recentes ({num(comp.get('linha_site', 0))}), ou é a predominante do orientador quando ele tem ao menos três
orientações na planilha e 80% delas numa mesma linha ({num(comp.get('linha_inferida', 0))}); nos demais, fica
“não informada”. A graduação das pessoas novas veio do Currículo Lattes, consultado no Escavador
({num(comp.get('graduacao_escavador', 0))}) ou na Plataforma Lattes ({num(comp.get('graduacao_lattes', 0))}),
aceito só quando o currículo é comprovadamente da pessoa (lista o título obtido no PPGDSTU ou o mesmo tema e
vínculo); a das demais ({num(pes['GRADUACAO_FONTE'].eq('Informado pela coordenação').sum())}) foi informada pela
coordenação. A ocupação declarada no Lattes foi compilada só para {num(comp.get('atuacao_lattes', 0))} dessas
pessoas, que não estavam em nenhuma fonte oficial; as demais ficam fora das medidas que dependem dela.</li>
<li><b>Docência na pós-graduação.</b> Os docentes de programas de pós-graduação vêm dos dados abertos da CAPES
({meta.get('docencia_ppg', {}).get('ano')}). Quem se titulou no PPGDSTU a partir de 2004 é ligado pelo código da
pessoa na CAPES, o mesmo nos registros de discente e de docente
({num(meta.get('docencia_ppg', {}).get('por_metodo', {}).get('ID da pessoa na CAPES', 0))} pessoas). Os demais
são ligados pelo nome, e só quando o registro confirma: o maior título do docente é o obtido no PPGDSTU (mesmo
nível, UFPA, ano igual ou vizinho), ou o nome é exato e único entre os docentes do país e o título é posterior ou
o programa é da instituição onde a pessoa já atua. Homônimos e grafias apenas parecidas ficam de fora.</li>
<li><b>Orientadores.</b> Grafias diferentes do mesmo nome foram unificadas
({meta.get('orientadores_unificados', 0)} variantes a menos). Em um caso de coorientação, conta a orientadora principal.</li>
<li><b>Pessoas.</b> Quem fez mestrado e doutorado no programa conta uma vez nas análises de destino, pela
titulação mais recente. Nomes grafados com e sem acento foram reconhecidos como a mesma pessoa.</li>
<li><b>Homônimos.</b> Na busca das pessoas novas em fontes oficiais, um nome com mais de um servidor foi
descartado, assim como a grafia apenas parecida associada a cargo não acadêmico e um vínculo que o Lattes
mostrou pertencer a outra pessoa com o mesmo nome.</li>
<li><b>Viés de localização.</b> Quem trabalha em universidade ou órgão público é mais fácil de localizar
do que quem atua na iniciativa privada, em organizações da sociedade civil ou no exterior. Os percentuais de
destino refletem esse viés.</li>
<li><b>Remuneração.</b> Valor bruto mensal, antes dos descontos: “remuneração básica bruta” do SIAPE
(federais ativos e aposentados, junho de 2026; com mais de um vínculo, o maior) e salário bruto da folha do
Executivo do Pará (julho de 2026). Fontes com menos de 10 pessoas (TJPA, dezembro de 2025, mês que inclui o
13º salário; Prefeitura de Belém) não são publicadas. As competências diferem em até um mês.</li>
<li><b>Privacidade.</b> O painel mostra informações acadêmicas públicas (título, ano, orientação). Dados de
folha de pagamento aparecem apenas de forma agregada; a tabela de remuneração não tem nome nem
identificador, e o CPF não faz parte dos dados publicados.</li>
</ul></div>""")
