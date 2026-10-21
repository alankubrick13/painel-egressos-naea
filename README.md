# Painel de Egressos do PPGDSTU · NAEA/UFPA

Painel público com os números dos egressos do Programa de Pós-Graduação em Desenvolvimento
Sustentável do Trópico Úmido (NAEA/UFPA): 920 titulações de mestrado e doutorado (1981–2025),
828 pessoas.

Páginas: Panorama, Formação, Graduação, Orientação, Destino profissional, Território,
Correlações, Consulta e Metodologia.

## Rodar localmente

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

## Dados

As tabelas em `data/` são geradas pelo ETL do projeto (fora deste repositório), a partir da
planilha do programa, dos dados abertos e do Catálogo de Teses e Dissertações da CAPES, da lista
de teses e dissertações do site do programa (2025), do Currículo Lattes (via Escavador) e de
folhas de pagamento públicas. A remuneração é publicada só de forma agregada, em grupos de
pelo menos 10 pessoas. Detalhes na página Metodologia.
