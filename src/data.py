"""Leitura, formatação e validações usadas pelo dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"


def load_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    datasets = {
        "competicoes": pd.read_csv(data_dir / "competicoes_2025.csv", parse_dates=["primeiro_jogo", "ultimo_jogo"]),
        "jogos": pd.read_csv(data_dir / "jogos_2025.csv", parse_dates=["data"]),
        "jogadores": pd.read_csv(data_dir / "jogadores_2025.csv"),
        "transferencias": pd.read_csv(data_dir / "transferencias_2025.csv", parse_dates=["data"]),
        "trofeus": pd.read_csv(data_dir / "trofeus_internos_2025.csv"),
        "fontes": pd.read_csv(data_dir / "fontes.csv"),
    }
    datasets["jogos"]["mes"] = datasets["jogos"]["data"].dt.to_period("M").astype(str)
    return datasets


def brl_millions(value: float) -> str:
    return f"R$ {value:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


def integer(value: float | int) -> str:
    return f"{int(value):,}".replace(",", ".")


def pct(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def data_quality_checks(data: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    competitions = data["competicoes"]
    matches = data["jogos"]
    players = data["jogadores"]
    transfers = data["transferencias"]

    incoming = transfers.loc[transfers["direcao"].eq("Entrada"), "valor_brl_milhoes"].sum()
    outgoing = transfers.loc[transfers["direcao"].eq("Saída"), "valor_brl_milhoes"].sum()
    checks = [
        ("7 competições oficiais", len(competitions) == 7, len(competitions)),
        ("78 jogos oficiais", len(matches) == 78, len(matches)),
        ("Partidas reconciliadas por competição", int(competitions["jogos"].sum()) == len(matches), int(competitions["jogos"].sum())),
        ("Campanha 49V–18E–11D", matches["resultado"].value_counts().to_dict() == {"Vitória": 49, "Empate": 18, "Derrota": 11}, matches["resultado"].value_counts().to_dict()),
        ("143 gols marcados", int(matches["gols_flamengo"].sum()) == 143, int(matches["gols_flamengo"].sum())),
        ("51 gols sofridos", int(matches["gols_adversario"].sum()) == 51, int(matches["gols_adversario"].sum())),
        ("Todos os jogos têm estádio", matches["estadio"].notna().all() and ~matches["estadio"].eq("Não informado").any(), int(matches["estadio"].notna().sum())),
        ("Compras divulgadas reconciliadas", abs(incoming - 308.7) < 0.01, round(incoming, 1)),
        ("Vendas divulgadas reconciliadas", abs(outgoing - 523.5) < 0.01, round(outgoing, 1)),
        ("Gols individuais + gol contra", int(players["gols_total"].sum()) + 1 == 143, int(players["gols_total"].sum())),
    ]
    return [{"checagem": name, "ok": ok, "valor_observado": observed} for name, ok, observed in checks]
