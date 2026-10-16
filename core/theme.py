"""Identidade visual do painel: paleta validada, modelo do Plotly e formatação pt-BR.

A paleta categórica das linhas de pesquisa foi validada (daltonismo e contraste)
contra o fundo branco dos cartões, em pares adjacentes e em todos os pares.
"""
import plotly.graph_objects as go
import plotly.io as pio

# ---------------------------------------------------------------- cores de marca
VERDE_NAEA = "#00742A"        # verde do logo; série única e destaques
LARANJA_NAEA = "#D9630C"      # laranja dos lápis do logo
LARANJA_TEXTO = "#9C4609"     # laranja escurecido para texto (6,4:1)

# ---------------------------------------------------------------- tinta e superfícies
SUPERFICIE = "#FFFFFF"        # cartões e área dos gráficos
PAPEL = "#F6F5F1"             # fundo da página
TINTA = "#1B1D1A"
TINTA_2 = "#55574F"
TINTA_3 = "#85857C"           # rótulos de eixo
GRADE = "#ECEAE3"
BASE = "#C9C6BD"              # linha de base / eixo
APAGADO = "#CFCCC3"           # de-ênfase (o resto, quando um item é o destaque)
NAO_INFORMADO = "#A9A69D"

# ---------------------------------------------------------------- linhas de pesquisa
# Ordem fixa (é ela que garante a separação para daltonismo): SUEP, DERA, GRN, EIPPP.
LINHAS = {
    "SUEP": ("Sociedade, Urbanização e Estudos Populacionais", "#1F6FBF"),
    "DERA": ("Desenvolvimento Econômico, Regional e Agrário", "#D9630C"),
    "GRN": ("Gestão de Recursos Naturais", "#13906B"),
    "EIPPP": ("Estado, Instituições, Planejamento e Políticas Públicas", "#7A3E8F"),
    "N/I": ("Não informada", NAO_INFORMADO),
}
ORDEM_LINHAS = ["SUEP", "DERA", "GRN", "EIPPP", "N/I"]
COR_LINHA = {s: c for s, (_, c) in LINHAS.items()}
NOME_LINHA = {s: n for s, (n, _) in LINHAS.items()}
COR_LINHA_NOME = {n: c for _, (n, c) in LINHAS.items()}

# ---------------------------------------------------------------- nível (ordinal: um só matiz)
COR_NIVEL = {"Mestrado": "#74C07E", "Doutorado": "#15662A"}
ORDEM_NIVEL = ["Mestrado", "Doutorado"]

# ---------------------------------------------------------------- escala sequencial (verde NAEA)
VERDES = ["#E0F5E1", "#CAECCD", "#AEE0B3", "#91D099", "#74C07E", "#5BAE68", "#409C52",
          "#2B8A41", "#1E7634", "#15662A", "#125623", "#0F471D", "#0C3816"]
def escala(cores):
    """Lista de cores -> escala contínua do Plotly (posições de 0 a 1)."""
    return [[i / (len(cores) - 1), c] for i, c in enumerate(cores)]


ESCALA_VERDE = escala(VERDES)
ESCALA_VERDE_MAPA = escala(VERDES[2:])     # sem os dois passos mais claros (somem no fundo)

# ---------------------------------------------------------------- divergente (abaixo / acima do esperado)
# laranja NAEA <-> cinza neutro <-> verde NAEA (quente x frio; ponto médio sem matiz)
ESCALA_DIVERGENTE = [[0, "#B4500A"], [0.25, "#E9A46F"], [0.5, "#F0EFEC"], [0.75, "#7DBE8A"], [1, "#0F5A26"]]

FONTE = "IBM Plex Sans, system-ui, -apple-system, Segoe UI, sans-serif"

# ---------------------------------------------------------------- modelo Plotly
_modelo = go.layout.Template()
_modelo.layout = go.Layout(
    font=dict(family=FONTE, size=13, color=TINTA_2),
    paper_bgcolor=SUPERFICIE,
    plot_bgcolor=SUPERFICIE,
    separators=",.",
    colorway=[COR_LINHA[s] for s in ORDEM_LINHAS[:4]],
    margin=dict(l=8, r=8, t=8, b=8),
    hoverlabel=dict(bgcolor=SUPERFICIE, bordercolor=GRADE, font=dict(family=FONTE, size=13, color=TINTA)),
    hovermode="closest",
    legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                font=dict(size=12, color=TINTA_2), title_text="", itemclick=False,
                itemdoubleclick=False, bgcolor=SUPERFICIE),
    xaxis=dict(showgrid=False, zeroline=False, showline=True, linecolor=BASE, linewidth=1,
               ticks="", tickfont=dict(size=12, color=TINTA_3), title=dict(font=dict(size=12, color=TINTA_3)),
               automargin=True, fixedrange=True),
    yaxis=dict(showgrid=True, gridcolor=GRADE, gridwidth=1, zeroline=False, showline=False,
               ticks="", tickfont=dict(size=12, color=TINTA_3), title=dict(font=dict(size=12, color=TINTA_3)),
               automargin=True, fixedrange=True),
    bargap=0.32,
    barcornerradius=4,
)
pio.templates["naea"] = _modelo
pio.templates.default = "naea"

CONFIG_PLOTLY = {"displayModeBar": False, "locale": "pt-BR", "responsive": True}


# ---------------------------------------------------------------- formatação pt-BR
def num(v, casas=0):
    """1234.5 -> '1.234,5'."""
    if v is None:
        return "–"
    s = f"{v:,.{casas}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(v, casas=1):
    """0.1234 -> '12,3%'."""
    if v is None:
        return "–"
    return f"{num(v * 100, casas)}%"


def reais(v):
    return f"R$ {num(v, 0)}"
