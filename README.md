# Flamengo 2025 — Projeto de Análise de Dados em Python

Dashboard de portfólio sobre a temporada profissional do Flamengo em 2025. O projeto reúne resultados esportivos, partidas, elenco, aparições, gols, assistências e transferências em uma aplicação interativa construída com Python, Pandas, Plotly e Streamlit.

## Principais números

- 78 jogos oficiais: 49 vitórias, 18 empates e 11 derrotas
- 143 gols marcados e 51 sofridos
- 37 partidas no Maracanã e 41 em outros estádios
- 7 competições oficiais e 4 títulos principais
- R$ 308,7 milhões em compras com valor divulgado
- R$ 523,5 milhões em vendas com valor divulgado
- Saldo positivo divulgado de R$ 214,8 milhões
- Arrascaeta: 25 gols e 20 assistências na base consolidada

## Competições de 2025

| Competição | Desfecho |
|---|---|
| Campeonato Brasileiro Série A | Campeão |
| Campeonato Carioca | Campeão |
| CONMEBOL Libertadores | Campeão |
| Supercopa Rei | Campeão |
| Copa do Brasil | Oitavas de final |
| Copa do Mundo de Clubes da FIFA | Oitavas de final |
| Copa Intercontinental da FIFA | Vice-campeão |

O Flamengo também ganhou a Taça Guanabara, o Derby das Américas e a Copa Challenger. Esses são troféus obtidos dentro de competições já listadas e, por isso, não são somados novamente como competições independentes.

## O que o dashboard permite analisar

- Visão geral da campanha e do caminho em cada competição
- Jogos no Maracanã versus demais estádios
- Mandos oficiais: mandante, visitante e campo neutro
- Resultados por mês e filtros por competição, local e resultado
- Elenco profissional ao fim da temporada
- Aparições como titular e reserva por jogador
- Gols, assistências e participações em gols
- Compras, vendas, movimentações gratuitas e valores não divulgados
- Catálogo de fontes e verificações automáticas de qualidade

## Como executar

Requer Python 3.11 ou mais recente.

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No macOS ou Linux:

```bash
source .venv/bin/activate
```

Instale as dependências e execute:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá em `http://localhost:8501`.

## Atualização/reprodução da base

Os CSVs já estão incluídos no projeto. Para reconstruí-los a partir da página consolidada da temporada:

```bash
python scripts/collect_data.py
```

Também é possível usar um HTML previamente baixado:

```bash
python scripts/collect_data.py --html caminho/2025_CR_Flamengo_season.html
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes reconciliam quantidade de jogos, campanha, gols, estádios, competições, elenco, valores de transferências e a inicialização do aplicativo.

## Estrutura

```text
projeto_flamengo_2025/
├── app.py
├── assets/flamengo_logo.svg
├── data/processed/
│   ├── competicoes_2025.csv
│   ├── fontes.csv
│   ├── jogadores_2025.csv
│   ├── jogos_2025.csv
│   ├── transferencias_2025.csv
│   └── trofeus_internos_2025.csv
├── scripts/collect_data.py
├── src/
│   ├── charts.py
│   └── data.py
├── tests/
├── requirements.txt
└── README.md
```

## Fontes e critérios

A fonte consolidada é a página [2025 CR Flamengo season](https://en.wikipedia.org/wiki/2025_CR_Flamengo_season), cujas tabelas de aparições citam Soccerway e FBref. Os resultados de competições foram cruzados com publicações da CBF, Flamengo e FIFA, listadas em `data/processed/fontes.csv` e na aba **Fontes e método** do dashboard. O escudo exibido no cabeçalho vem do [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Flamengo_braz_logo.svg), com uso educacional e identificação da marca.

Critérios importantes:

- Período: 12 de janeiro a 17 de dezembro de 2025
- Apenas partidas oficiais; o amistoso de pré-temporada contra o São Paulo não entra nos 78 jogos
- “Maracanã” considera o estádio real, não o mando formal
- “Outros estádios” inclui jogos como visitante, campos neutros e partidas como mandante levadas a outra cidade
- Valores financeiros são os valores reportados em reais; negócios sem valor divulgado não entram no saldo
- O elenco profissional padrão é o listado ao fim da temporada; atletas da base e jogadores que saíram no ano continuam disponíveis na visão ampliada

### Divergência conhecida

As linhas individuais de assistências da fonte somam 99, mas o rodapé da mesma tabela informa 98. O projeto preserva os valores individuais e registra a divergência. Regras de atribuição de assistências também podem variar entre provedores.

## Tecnologias demonstradas

- Python e organização modular
- Pandas para limpeza, junção e agregação
- Web scraping reprodutível com `pandas.read_html` e `lxml`
- Plotly para visualizações interativas
- Streamlit para construção do produto analítico
- Testes e verificações de qualidade dos dados

Projeto educacional de portfólio. Não afiliado ao Clube de Regatas do Flamengo.
