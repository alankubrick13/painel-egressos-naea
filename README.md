# Painel de Egressos do PPGDSTU · NAEA/UFPA

Painel público com os números dos egressos do Programa de Pós-Graduação em Desenvolvimento
Sustentável do Trópico Úmido (NAEA/UFPA): 888 titulações de mestrado e doutorado (1981–2024),
799 pessoas.

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
planilha do programa, do Catálogo de Teses e Dissertações da CAPES, do Currículo Lattes e de
folhas de pagamento públicas. A remuneração é publicada só de forma agregada, em grupos de
pelo menos 10 pessoas. Detalhes na página Metodologia.
