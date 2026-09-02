"""Dashboard interativo: Flamengo — Temporada 2025."""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts import (
    apps_vs_contributions,
    competition_games,
    monthly_results,
    player_contributions,
    transfer_values,
    venues,
)
from src.data import brl_millions, data_quality_checks, integer, load_data, pct


ROOT = Path(__file__).resolve().parent
LOGO_PATH = ROOT / "assets" / "flamengo_logo.svg"
LOGO_BASE64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")


st.set_page_config(
    page_title="Flamengo 2025 | Análise de Dados",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --red: #C8102E; --black: #141414; --gold: #D6A84B; }
    .stApp { background: #FAFAF8; }
    h1, h2, h3 { color: var(--black); letter-spacing: -0.02em; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E5E5E2;
        border-top: 4px solid var(--red);
        padding: 1rem;
        border-radius: 0.65rem;
    }
    div[data-testid="stMetricLabel"] { color: #666; }
    .hero {
        background: linear-gradient(112deg, #121212 0%, #241015 55%, #8F001E 100%);
        color: white;
        padding: 1.6rem 1.8rem;
        border-radius: 0.9rem;
        margin-bottom: 1rem;
    }
    .hero-inner { display: flex; align-items: center; gap: 1.35rem; }
    .hero-logo {
        width: 82px; height: 102px; object-fit: contain; flex: 0 0 auto;
        filter: drop-shadow(0 8px 12px rgba(0, 0, 0, 0.28));
    }
    .hero-copy { min-width: 0; }
    .hero h1 { color: white; margin: 0; }
    .hero p { color: #ECECEC; margin: 0.35rem 0 0; }
    .badge-title {
        display: inline-block; background: #C8102E; color: white; font-weight: 700;
        padding: 0.3rem 0.65rem; border-radius: 999px; margin: 0.2rem 0.25rem 0.2rem 0;
    }
    .badge-path {
        display: inline-block; background: #E7E7E4; color: #222; font-weight: 650;
        padding: 0.3rem 0.65rem; border-radius: 999px; margin: 0.2rem 0.25rem 0.2rem 0;
    }
    .small-note { color: #666; font-size: 0.88rem; }
    @media (max-width: 640px) {
        .hero { padding: 1.2rem; }
        .hero-inner { gap: 0.9rem; }
        .hero-logo { width: 60px; height: 74px; }
        .hero h1 { font-size: 1.65rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data() -> dict[str, pd.DataFrame]:
    return load_data()


data = get_data()
competitions = data["competicoes"]
matches = data["jogos"]
players = data["jogadores"]
transfers = data["transferencias"]

st.markdown(
    f"""
    <div class="hero notranslate" translate="no">
      <div class="hero-inner">
        <img class="hero-logo" src="data:image/svg+xml;base64,{LOGO_BASE64}" alt="Escudo do Flamengo">
        <div class="hero-copy">
          <h1>Flamengo — Temporada 2025</h1>
          <p>Desempenho esportivo, elenco profissional, produção ofensiva, partidas e mercado de transferências.</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Sobre o projeto")
    st.write("Projeto de portfólio em Python, Pandas, Plotly e Streamlit.")
    st.caption("Período: 12/01/2025 a 17/12/2025 • somente jogos oficiais")
    st.divider()
    st.subheader("Definições")
    st.write("**Maracanã:** partidas disputadas no estádio, independentemente do mando oficial.")
    st.write("**Outros estádios:** partidas fora do Maracanã, inclusive campos neutros e jogos como mandante em outras cidades.")
    st.write("**Elenco final:** jogadores listados no elenco profissional ao fim da temporada de 2025.")
    st.divider()
    st.caption("Atualização da base consolidada: 17/12/2025")

tab_overview, tab_matches, tab_players, tab_transfers, tab_method = st.tabs(
    ["Visão geral", "Partidas", "Jogadores", "Mercado", "Fontes e método"]
)

with tab_overview:
    total_titles = int(competitions["campeao"].sum())
    maracana_games = int(matches["no_maracana"].sum())
    win_rate = matches["resultado"].eq("Vitória").mean() * 100
    cols = st.columns(6)
    cols[0].metric("Jogos oficiais", integer(len(matches)))
    cols[1].metric("Títulos principais", integer(total_titles), "7 competições")
    cols[2].metric("Vitórias", integer(matches["resultado"].eq("Vitória").sum()), pct(win_rate))
    cols[3].metric("Gols marcados", integer(matches["gols_flamengo"].sum()))
    cols[4].metric("Jogos no Maracanã", integer(maracana_games))
    cols[5].metric("Fora do Maracanã", integer(len(matches) - maracana_games))

    st.subheader("Competições disputadas")
    champion_badges = "".join(
        f'<span class="badge-title">🏆 {row.competicao}</span>'
        for row in competitions.itertuples()
        if row.campeao
    )
    other_badges = "".join(
        f'<span class="badge-path">{row.competicao}: {row.resultado}</span>'
        for row in competitions.itertuples()
        if not row.campeao
    )
    st.markdown(champion_badges + "<br>" + other_badges, unsafe_allow_html=True)
    st.caption(
        "Além dos quatro títulos principais, o Flamengo conquistou a Taça Guanabara, "
        "o Derby das Américas e a Copa Challenger — troféus internos de competições já contabilizadas."
    )

    left, right = st.columns([1.4, 1])
    with left:
        st.plotly_chart(competition_games(competitions), width="stretch")
    with right:
        st.plotly_chart(venues(matches), width="stretch")

    display_competitions = competitions[
        ["competicao", "resultado", "jogos", "vitorias", "empates", "derrotas", "gols_pro", "gols_contra", "aproveitamento_pct"]
    ].rename(
        columns={
            "competicao": "Competição",
            "resultado": "Desfecho",
            "jogos": "J",
            "vitorias": "V",
            "empates": "E",
            "derrotas": "D",
            "gols_pro": "GP",
            "gols_contra": "GC",
            "aproveitamento_pct": "Aproveitamento (%)",
        }
    )
    st.dataframe(display_competitions, width="stretch", hide_index=True)

with tab_matches:
    st.subheader("Análise das 78 partidas oficiais")
    filter_cols = st.columns([2, 1, 1])
    selected_competitions = filter_cols[0].multiselect(
        "Competições",
        options=sorted(matches["competicao"].unique()),
        default=sorted(matches["competicao"].unique()),
    )
    selected_venues = filter_cols[1].multiselect(
        "Local",
        options=["Maracanã", "Outros estádios"],
        default=["Maracanã", "Outros estádios"],
    )
    selected_results = filter_cols[2].multiselect(
        "Resultado",
        options=["Vitória", "Empate", "Derrota"],
        default=["Vitória", "Empate", "Derrota"],
    )
    filtered_matches = matches[
        matches["competicao"].isin(selected_competitions)
        & matches["grupo_local"].isin(selected_venues)
        & matches["resultado"].isin(selected_results)
    ].copy()

    if filtered_matches.empty:
        st.warning("Nenhuma partida corresponde aos filtros escolhidos.")
    else:
        mcols = st.columns(5)
        mcols[0].metric("Partidas filtradas", integer(len(filtered_matches)))
        mcols[1].metric("Vitórias", integer(filtered_matches["resultado"].eq("Vitória").sum()))
        mcols[2].metric("Empates", integer(filtered_matches["resultado"].eq("Empate").sum()))
        mcols[3].metric("Derrotas", integer(filtered_matches["resultado"].eq("Derrota").sum()))
        mcols[4].metric("Saldo de gols", integer(filtered_matches["gols_flamengo"].sum() - filtered_matches["gols_adversario"].sum()))
        st.plotly_chart(monthly_results(filtered_matches), width="stretch")

        detail = filtered_matches[
            ["data", "competicao", "fase_rodada", "mandante", "gols_mandante", "gols_visitante", "visitante", "resultado", "condicao", "estadio", "cidade"]
        ].copy()
        detail["placar"] = detail["gols_mandante"].astype(str) + " x " + detail["gols_visitante"].astype(str)
        detail["data"] = detail["data"].dt.strftime("%d/%m/%Y")
        detail = detail[["data", "competicao", "fase_rodada", "mandante", "placar", "visitante", "resultado", "condicao", "estadio", "cidade"]]
        detail.columns = ["Data", "Competição", "Fase/Rodada", "Mandante", "Placar", "Visitante", "Resultado", "Condição", "Estádio", "Cidade"]
        st.dataframe(detail, width="stretch", hide_index=True, height=440)

with tab_players:
    st.subheader("Elenco e desempenho individual")
    pcol1, pcol2, pcol3 = st.columns([1.4, 1, 1])
    roster_only = pcol1.toggle("Exibir apenas o elenco profissional ao fim de 2025", value=True)
    selected_positions = pcol2.multiselect(
        "Setor",
        options=["Goleiro", "Defesa", "Meio-campo", "Ataque"],
        default=["Goleiro", "Defesa", "Meio-campo", "Ataque"],
    )
    top_n = pcol3.slider("Jogadores no ranking", min_value=5, max_value=25, value=15, step=5)
    filtered_players = players[players["grupo_posicao"].isin(selected_positions)].copy()
    if roster_only:
        filtered_players = filtered_players[filtered_players["elenco_profissional_final"]].copy()

    if filtered_players.empty:
        st.warning("Nenhum jogador corresponde aos filtros escolhidos.")
    else:
        leader_goals = players.loc[players["gols_total"].idxmax()]
        leader_assists = players.loc[players["assistencias_total"].idxmax()]
        leader_apps = players.loc[players["jogos_total"].idxmax()]
        pcards = st.columns(4)
        pcards[0].metric("Jogadores exibidos", integer(len(filtered_players)))
        pcards[1].metric("Mais jogos", leader_apps["jogador"], integer(leader_apps["jogos_total"]))
        pcards[2].metric("Artilheiro", leader_goals["jogador"], f"{integer(leader_goals['gols_total'])} gols")
        pcards[3].metric("Mais assistências", leader_assists["jogador"], integer(leader_assists["assistencias_total"]))

        chart_left, chart_right = st.columns(2)
        with chart_left:
            st.plotly_chart(player_contributions(filtered_players, min(top_n, len(filtered_players))), width="stretch")
        with chart_right:
            st.plotly_chart(apps_vs_contributions(filtered_players), width="stretch")

        player_table = filtered_players[
            ["numero", "jogador", "posicao", "jogos_total", "titular_total", "reserva_total", "gols_total", "assistencias_total", "participacoes_gol", "status_2025"]
        ].copy()
        player_table.columns = ["Nº", "Jogador", "Posição", "Jogos", "Titular", "Entrou", "Gols", "Assistências", "G+A", "Status em 2025"]
        player_table = player_table.sort_values(["Jogos", "G+A"], ascending=False)
        st.dataframe(player_table, width="stretch", hide_index=True, height=520)
        st.caption(
            "As aparições incluem entradas como titular e como reserva em todas as sete competições. "
            "Jogadores da base que atuaram no profissional aparecem quando o filtro de elenco final é desativado."
        )

with tab_transfers:
    st.subheader("Compras, vendas e movimentações")
    incoming_value = transfers.loc[transfers["direcao"].eq("Entrada"), "valor_brl_milhoes"].sum()
    outgoing_value = transfers.loc[transfers["direcao"].eq("Saída"), "valor_brl_milhoes"].sum()
    net_value = outgoing_value - incoming_value
    tcols = st.columns(4)
    tcols[0].metric("Compras divulgadas", brl_millions(incoming_value), "4 aquisições pagas")
    tcols[1].metric("Vendas divulgadas", brl_millions(outgoing_value), "7 negociações com valor")
    tcols[2].metric("Saldo de transferências", brl_millions(net_value), "vendas − compras")
    tcols[3].metric("Movimentações registradas", integer(len(transfers)), "inclui custo zero e não divulgado")
    st.plotly_chart(transfer_values(transfers), width="stretch")

    direction_label = st.radio(
        "Movimento",
        options=["Todos", "Compras", "Vendas"],
        horizontal=True,
        key="filtro_movimento",
    )
    direction_map = {"Compras": "Entrada", "Vendas": "Saída"}
    direction = direction_map.get(direction_label)
    transfer_view = transfers if direction is None else transfers[transfers["direcao"].eq(direction)]
    transfer_table = transfer_view[
        ["direcao", "jogador", "clube_origem_destino", "tipo_taxa", "valor_brl_milhoes", "valor_eur_milhoes", "data", "categoria"]
    ].copy()
    transfer_table["data"] = transfer_table["data"].dt.strftime("%d/%m/%Y")
    transfer_table.columns = ["Direção", "Jogador", "Clube de origem/destino", "Tipo", "R$ milhões", "€ milhões", "Data", "Categoria"]
    st.dataframe(transfer_table, width="stretch", hide_index=True, height=500)
    st.info(
        "Os totais financeiros somam apenas valores publicamente divulgados. Transferências gratuitas, "
        "retornos de empréstimo, liberações e valores não divulgados permanecem na tabela, mas não entram no saldo."
    )

with tab_method:
    st.subheader("Metodologia e qualidade dos dados")
    st.write(
        "A unidade de análise de partidas é um jogo oficial. A unidade de análise de jogadores é um atleta "
        "listado na tabela de aparições da temporada. As bases são geradas por `scripts/collect_data.py` e "
        "consumidas pelo aplicativo sem cálculos manuais ocultos."
    )

    checks = pd.DataFrame(data_quality_checks(data))
    checks["status"] = checks["ok"].map({True: "✅ OK", False: "⚠️ Revisar"})
    checks["valor_observado"] = checks["valor_observado"].map(str)
    st.dataframe(checks[["status", "checagem", "valor_observado"]], width="stretch", hide_index=True)

    st.warning(
        "Caveat de assistências: as linhas individuais da fonte somam 99 assistências, enquanto o rodapé da mesma "
        "tabela informa 98. O projeto preserva os valores individuais e sinaliza a divergência, em vez de alterar "
        "um jogador sem evidência. Assistências também podem variar entre provedores conforme a regra de atribuição."
    )
    st.caption("Os 143 gols do time correspondem a 142 gols atribuídos a jogadores e um gol contra do adversário.")

    st.subheader("Troféus dentro de competições")
    st.dataframe(data["trofeus"], width="stretch", hide_index=True)

    st.subheader("Catálogo de fontes")
    for source in data["fontes"].itertuples():
        st.markdown(f"- **{source.tema}:** [{source.fonte}]({source.url})")

    st.subheader("Como reproduzir")
    st.code(
        "python -m venv .venv\n"
        "# Windows: .venv\\Scripts\\activate\n"
        "# macOS/Linux: source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python scripts/collect_data.py\n"
        "streamlit run app.py",
        language="bash",
    )

st.caption("Projeto educacional de análise de dados. Não afiliado ao Clube de Regatas do Flamengo.")
