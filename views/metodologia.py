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

ui.secao("Como os números foram construídos")
st.html(f"""<div class="prosa">
<p><b>Base de titulações.</b> O ponto de partida é o quadro geral de egressos mantido pela coordenação do
PPGDSTU: uma linha por dissertação ou tese, com orientador(a), linha de pesquisa, curso de graduação e um
resumo do Currículo Lattes ({num(n_plan)} titulações após a limpeza). A ela foram somadas
<b>{num(comp.get('titulacoes', 0))} titulações</b> que a CAPES registra como do programa e que não estavam na
planilha. O painel reúne <b>{num(meta['titulacoes'])} titulações</b> de <b>{num(meta['pessoas'])} pessoas</b>,
defendidas entre {meta['primeiro_ano']} e {meta['ultimo_ano']}.</p>
<p><b>Destino profissional.</b> A ocupação declarada no Lattes foi complementada por cruzamentos nominais
com fontes oficiais, em rodadas sucessivas: folha federal (SIAPE, Portal da Transparência, competência
{meta['competencia_folha']}), folha do Governo do Pará, Tribunal de Justiça, Ministério Público e Tribunal
de Contas do Pará, Prefeitura de Belém, e os registros de docentes e discentes da CAPES. Nomes
homônimos foram descartados ou marcados para conferência.</p>
<p><b>Conferência externa.</b> As datas de defesa foram comparadas com os titulados do programa registrados
pela CAPES (Coleta Sucupira, 2004 a 2024) e com o Repositório Institucional da UFPA. A conferência corrigiu o
ano de {len(meta.get('correcoes_de_ano', []))} trabalhos e mostrou que a planilha estava incompleta,
sobretudo em {anos_inc}. As titulações que faltavam foram incorporadas (lista abaixo).</p>
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
        st.dataframe(corr.rename(columns={"EGRESSO": "Egresso", "NIVEL": "Nível", "ANO_PLANILHA": "Ano na planilha",
                                          "ANO_CORRIGIDO": "Ano adotado", "FONTE": "Fonte"}),
                     hide_index=True, use_container_width=True)

inc_df = data.capes_incorporadas()
if len(inc_df):
    with st.container(border=True, key="card-incorporadas"):
        st.html('<div class="card-titulo">Titulações incorporadas a partir da CAPES</div>'
                f'<div class="card-sub">{num(len(inc_df))} trabalhos que não estavam na planilha do programa. '
                f'{num(comp.get("pessoas_existentes", 0))} são de pessoas que já estavam na base (por exemplo, o '
                f'doutorado de quem tinha só o mestrado registrado); {num(comp.get("pessoas_novas", 0))} pessoas '
                f'entraram na base, das quais {num(comp.get("localizados", 0))} foram localizadas em fontes '
                'oficiais. A coordenação pode usar esta lista para atualizar a planilha.</div>')
        st.dataframe(inc_df.assign(LINHA_ORIGEM=inc_df["LINHA_ORIGEM"].replace(
                         {"Inferida pelo orientador": "Atribuída pelo orientador"})).rename(columns={
                         "NOME": "Nome", "NIVEL": "Nível", "ANO": "Ano", "TITULO": "Título", "ORIENTADOR": "Orientador(a)",
                         "LINHA": "Linha", "LINHA_ORIGEM": "Origem da linha", "PESSOA": "Pessoa"}),
                     hide_index=True, use_container_width=True, height=340)
        st.html('<div class="card-fonte">Fonte: CAPES – Dados Abertos, discentes da pós-graduação (situação '
                '“titulado”). Os registros da CAPES não informam linha de pesquisa nem graduação.</div>')

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
<li><b>Titulações vindas da CAPES.</b> Os registros da CAPES não trazem linha de pesquisa. Nesses
{num(comp.get('titulacoes', 0))} trabalhos, a linha é a predominante do orientador quando ele tem ao menos três
orientações na planilha e 80% delas numa mesma linha ({num(comp.get('linha_inferida', 0))} casos); nos demais, fica
“não informada”. A graduação das pessoas novas foi buscada no Currículo Lattes reproduzido pelo Escavador
({num(comp.get('graduacao_escavador', 0))} encontradas), aceitando um perfil só quando ele lista o mestrado ou o
doutorado obtido no PPGDSTU; a das demais ({num(pes['GRADUACAO_FONTE'].eq('Informado pela coordenação').sum())}) foi
informada pela coordenação. A ocupação declarada no Lattes dessas pessoas, em geral, não foi compilada; elas ficam
fora das medidas que dependem dela.</li>
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
