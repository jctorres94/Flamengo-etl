"""Gráficos Plotly com identidade visual rubro-negra."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


RED = "#C8102E"
DARK_RED = "#7A0019"
BLACK = "#141414"
GOLD = "#D6A84B"
LIGHT = "#F5F5F3"
GREY = "#777777"
POSITION_COLORS = {
    "Goleiro": "#777777",
    "Defesa": "#141414",
    "Meio-campo": "#C8102E",
    "Ataque": "#D6A84B",
}


def polish(fig: go.Figure, title: str, subtitle: str = "") -> go.Figure:
    full_title = title if not subtitle else f"{title}<br><sup>{subtitle}</sup>"
    fig.update_layout(
        title=full_title,
        font=dict(family="Arial, sans-serif", color=BLACK),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=75, b=20),
        legend_title_text="",
        hoverlabel=dict(bgcolor="white", font_color=BLACK),
    )
    fig.update_xaxes(showgrid=False, linecolor="#D9D9D9")
    fig.update_yaxes(gridcolor="#ECECEC", zerolinecolor="#BDBDBD")
    return fig


def competition_games(competitions: pd.DataFrame) -> go.Figure:
    data = competitions.sort_values("jogos", ascending=True)
    colors = [RED if result == "Campeão" else "#B9B9B9" for result in data["resultado"]]
    fig = go.Figure(
        go.Bar(
            x=data["jogos"],
            y=data["competicao"],
            orientation="h",
            marker_color=colors,
            text=data["jogos"],
            textposition="outside",
            customdata=data[["resultado", "aproveitamento_pct"]],
            hovertemplate="%{y}<br>Jogos: %{x}<br>Resultado: %{customdata[0]}<br>Aproveitamento: %{customdata[1]:.1f}%<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, data["jogos"].max() * 1.15], title="Jogos")
    fig.update_yaxes(title="")
    return polish(fig, "Jogos por competição", "Vermelho identifica as competições conquistadas")


def venues(matches: pd.DataFrame) -> go.Figure:
    values = matches["grupo_local"].value_counts().reindex(["Maracanã", "Outros estádios"]).fillna(0)
    fig = go.Figure(
        go.Pie(
            labels=values.index,
            values=values.values,
            hole=0.62,
            marker=dict(colors=[RED, BLACK], line=dict(color="white", width=2)),
            textinfo="label+value",
            hovertemplate="%{label}: %{value} jogos (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=False)
    return polish(fig, "Onde o Flamengo jogou", "Maracanã versus todos os demais estádios")


def monthly_results(matches: pd.DataFrame) -> go.Figure:
    order = ["Vitória", "Empate", "Derrota"]
    grouped = matches.groupby(["mes", "resultado"]).size().reset_index(name="jogos")
    fig = px.bar(
        grouped,
        x="mes",
        y="jogos",
        color="resultado",
        category_orders={"resultado": order},
        color_discrete_map={"Vitória": RED, "Empate": "#A9A9A9", "Derrota": BLACK},
        barmode="stack",
        labels={"mes": "Mês", "jogos": "Jogos", "resultado": "Resultado"},
    )
    fig.update_traces(hovertemplate="Mês: %{x}<br>Jogos: %{y}<extra></extra>")
    return polish(fig, "Resultados por mês", "Quantidade de vitórias, empates e derrotas")


def player_contributions(players: pd.DataFrame, top_n: int = 15) -> go.Figure:
    data = players.nlargest(top_n, "participacoes_gol").sort_values("participacoes_gol")
    fig = go.Figure()
    fig.add_bar(
        name="Gols",
        x=data["gols_total"],
        y=data["jogador"],
        orientation="h",
        marker_color=RED,
        hovertemplate="%{y}<br>Gols: %{x}<extra></extra>",
    )
    fig.add_bar(
        name="Assistências",
        x=data["assistencias_total"],
        y=data["jogador"],
        orientation="h",
        marker_color=GOLD,
        hovertemplate="%{y}<br>Assistências: %{x}<extra></extra>",
    )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="Participações em gols")
    fig.update_yaxes(title="")
    return polish(fig, f"Top {top_n} em participações em gols", "Gols e assistências em todas as competições oficiais")


def apps_vs_contributions(players: pd.DataFrame) -> go.Figure:
    data = players[(players["jogos_total"] > 0) & (players["participacoes_gol"] > 0)].copy()
    fig = px.scatter(
        data,
        x="jogos_total",
        y="participacoes_gol",
        color="grupo_posicao",
        hover_name="jogador",
        hover_data={"gols_total": True, "assistencias_total": True, "grupo_posicao": False},
        color_discrete_map=POSITION_COLORS,
        labels={
            "jogos_total": "Jogos",
            "participacoes_gol": "Gols + assistências",
            "grupo_posicao": "Setor",
            "gols_total": "Gols",
            "assistencias_total": "Assistências",
        },
    )
    fig.update_traces(marker=dict(size=11, line=dict(width=1, color="white")))
    return polish(fig, "Jogos e produção ofensiva", "Cada ponto representa um jogador com ao menos uma participação em gol")


def transfer_values(transfers: pd.DataFrame) -> go.Figure:
    data = transfers[transfers["valor_brl_milhoes"].notna()].copy()
    data["valor_assinado"] = data["valor_brl_milhoes"].where(data["direcao"].eq("Entrada"), -data["valor_brl_milhoes"])
    data = data.sort_values("valor_assinado")
    colors = [RED if value > 0 else BLACK for value in data["valor_assinado"]]
    fig = go.Figure(
        go.Bar(
            x=data["valor_assinado"],
            y=data["jogador"],
            orientation="h",
            marker_color=colors,
            customdata=data[["direcao", "valor_brl_milhoes", "clube_origem_destino"]],
            hovertemplate="%{y}<br>%{customdata[0]}: R$ %{customdata[1]:.1f} mi<br>Clube: %{customdata[2]}<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_color="#777777", line_width=1)
    fig.update_xaxes(title="R$ milhões — entradas à direita; saídas à esquerda")
    fig.update_yaxes(title="")
    return polish(fig, "Valores divulgados por transferência", "Valores reportados em reais; negócios sem valor divulgado ficam fora do gráfico")
