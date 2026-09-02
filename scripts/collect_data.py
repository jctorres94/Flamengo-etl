"""Coleta e prepara os dados do Flamengo na temporada de 2025.

Fonte consolidada: página "2025 CR Flamengo season" da Wikipédia, cujas
tabelas de atletas citam Soccerway e FBref. Resultados e títulos são
cruzados no catálogo de fontes com CBF, Flamengo, FIFA e CONMEBOL.

Uso:
    python scripts/collect_data.py
    python scripts/collect_data.py --html /caminho/pagina.html
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from io import BytesIO, StringIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
from lxml import etree, html


SOURCE_URL = "https://en.wikipedia.org/wiki/2025_CR_Flamengo_season"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "processed"

COMPETITION_MAP = {
    "Série A": "Campeonato Brasileiro Série A",
    "Campeonato Brasileiro": "Campeonato Brasileiro Série A",
    "Copa do Brasil": "Copa do Brasil",
    "Campeonato Carioca": "Campeonato Carioca",
    "Copa Libertadores": "CONMEBOL Libertadores",
    "Libertadores": "CONMEBOL Libertadores",
    "Supercopa do Brasil": "Supercopa Rei",
    "FIFA Club World Cup": "Copa do Mundo de Clubes da FIFA",
    "FIFA Intercontinental Cup": "Copa Intercontinental da FIFA",
    "Carioca": "Campeonato Carioca",
    "Other[Note 1]": "Outras competições",
}

POSITION_MAP = {
    "GK": "Goleiro",
    "RB": "Lateral-direito",
    "CB": "Zagueiro",
    "LB": "Lateral-esquerdo",
    "DF": "Defensor",
    "DM": "Volante",
    "CM": "Meio-campista",
    "MF": "Meio-campista",
    "AM": "Meia ofensivo",
    "LW": "Ponta esquerda",
    "RW": "Ponta direita",
    "FW": "Atacante",
    "CF": "Centroavante",
}

POSITION_GROUP = {
    "GK": "Goleiro",
    "RB": "Defesa",
    "CB": "Defesa",
    "LB": "Defesa",
    "DF": "Defesa",
    "DM": "Meio-campo",
    "CM": "Meio-campo",
    "MF": "Meio-campo",
    "AM": "Meio-campo",
    "LW": "Ataque",
    "RW": "Ataque",
    "FW": "Ataque",
    "CF": "Ataque",
}


def slug(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    key = re.sub(r"[^a-z0-9]+", "", value.lower())
    aliases = {"saul": "saulniguez"}
    return aliases.get(key, key)


def clean_name(value: object) -> str:
    return re.sub(r"[†*]+$", "", str(value)).strip()


def number(value: object) -> int:
    text = str(value).strip()
    if text in {"—", "–", "nan", "None", ""}:
        return 0
    parsed = pd.to_numeric(text, errors="coerce")
    return 0 if pd.isna(parsed) else int(parsed)


def download_source() -> bytes:
    request = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 FlamengoDataPortfolio/1.0"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def get_tables(source_bytes: bytes) -> list[pd.DataFrame]:
    return pd.read_html(BytesIO(source_bytes))


def find_table(tables: list[pd.DataFrame], predicate) -> pd.DataFrame:
    for table in tables:
        if predicate(table):
            return table.copy()
    raise ValueError("Tabela esperada não encontrada na fonte.")


def flatten_first_level(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [str(col[0]) for col in out.columns]
    return out


def parse_competitions(tables: list[pd.DataFrame]) -> pd.DataFrame:
    raw = find_table(
        tables,
        lambda t: isinstance(t.columns, pd.MultiIndex)
        and "Competition" in t.columns.get_level_values(0)
        and "Pld" in t.columns.get_level_values(-1),
    )
    raw.columns = [
        "competicao",
        "primeiro_jogo",
        "ultimo_jogo",
        "fase_inicial",
        "resultado_fonte",
        "jogos",
        "vitorias",
        "empates",
        "derrotas",
        "gols_pro",
        "gols_contra",
        "saldo_gols",
        "aproveitamento_pct",
    ]
    raw = raw[raw["competicao"] != "Total"].copy()
    raw["competicao"] = raw["competicao"].map(lambda x: COMPETITION_MAP.get(str(x), str(x)))
    result_map = {
        "Winners": "Campeão",
        "Runners-up": "Vice-campeão",
        "Round of 16": "Oitavas de final",
    }
    raw["resultado"] = raw["resultado_fonte"].map(result_map).fillna(raw["resultado_fonte"])
    raw["campeao"] = raw["resultado"].eq("Campeão")
    raw["primeiro_jogo"] = pd.to_datetime(raw["primeiro_jogo"], format="mixed").dt.date
    raw["ultimo_jogo"] = pd.to_datetime(raw["ultimo_jogo"], format="mixed").dt.date
    numeric = [
        "jogos",
        "vitorias",
        "empates",
        "derrotas",
        "gols_pro",
        "gols_contra",
        "saldo_gols",
        "aproveitamento_pct",
    ]
    raw[numeric] = raw[numeric].apply(pd.to_numeric, errors="coerce")
    return raw.drop(columns="resultado_fonte")


def previous_heading(table_node, tag: str) -> str:
    nodes = table_node.xpath(f"preceding::{tag}[1]")
    return " ".join(nodes[-1].text_content().split()) if nodes else ""


def parse_matches(source_bytes: bytes) -> pd.DataFrame:
    document = html.fromstring(source_bytes)
    rows: list[dict[str, object]] = []

    for table in document.xpath("//table[contains(@class, 'vevent')]"):
        competition_source = previous_heading(table, "h3")
        if competition_source == "Pre-Season friendlies":
            continue

        frame = pd.read_html(StringIO(etree.tostring(table, encoding="unicode")))[0]
        first = [str(value).strip() for value in frame.iloc[0, :5].tolist()]
        if len(first) < 5:
            continue

        date_round, home_team, score_text, away_team, city = first
        date_match = re.search(r"(\d{1,2} [A-Za-z]+ 2025)", date_round)
        score_match = re.search(r"(\d+)\s*[–-]\s*(\d+)", score_text)
        if not date_match or not score_match:
            continue

        date_text = date_match.group(1)
        round_text = date_round.replace(date_text, "", 1).strip()
        details = " ".join(str(value) for value in frame.iloc[1:, -1].dropna().tolist())
        stadium_match = re.search(r"Stadium:\s*(.*?)(?:Attendance:|Referee:|$)", details)
        attendance_match = re.search(r"Attendance:\s*([\d,\.]+)", details)
        stadium = stadium_match.group(1).strip() if stadium_match else "Não informado"
        stadium = re.sub(r"\[\d+\]", "", stadium).strip()
        attendance = None
        if attendance_match:
            attendance = int(re.sub(r"\D", "", attendance_match.group(1)))

        goals_home, goals_away = map(int, score_match.groups())
        flamengo_home = slug(home_team) == "flamengo"
        goals_for = goals_home if flamengo_home else goals_away
        goals_against = goals_away if flamengo_home else goals_home
        result = "Vitória" if goals_for > goals_against else "Derrota" if goals_for < goals_against else "Empate"
        competition = COMPETITION_MAP.get(competition_source, competition_source)
        neutral = (
            competition in {
                "Supercopa Rei",
                "Copa do Mundo de Clubes da FIFA",
                "Copa Intercontinental da FIFA",
            }
            or (competition == "CONMEBOL Libertadores" and round_text.lower() == "final")
        )
        match_condition = "Neutro" if neutral else ("Mandante" if flamengo_home else "Visitante")
        at_maracana = "maracana" in slug(stadium)

        rows.append(
            {
                "data": pd.to_datetime(date_text, format="%d %B %Y").date(),
                "competicao": competition,
                "fase_rodada": round_text or "Não informada",
                "mandante": home_team,
                "visitante": away_team,
                "gols_mandante": goals_home,
                "gols_visitante": goals_away,
                "gols_flamengo": goals_for,
                "gols_adversario": goals_against,
                "resultado": result,
                "condicao": match_condition,
                "estadio": stadium,
                "cidade": city,
                "no_maracana": at_maracana,
                "grupo_local": "Maracanã" if at_maracana else "Outros estádios",
                "publico": attendance,
                "placar_fonte": score_text,
            }
        )

    matches = pd.DataFrame(rows).sort_values("data").reset_index(drop=True)
    matches.insert(0, "jogo_id", range(1, len(matches) + 1))
    return matches


def parse_roster(tables: list[pd.DataFrame]) -> pd.DataFrame:
    raw = find_table(
        tables,
        lambda t: isinstance(t.columns, pd.MultiIndex)
        and "Date of birth (age)" in t.columns.get_level_values(0)
        and "Contract end" in t.columns.get_level_values(0),
    )
    raw = flatten_first_level(raw)
    raw = raw[raw["Pos."].isin(POSITION_MAP)].copy()
    return pd.DataFrame(
        {
            "numero": pd.to_numeric(raw["No."], errors="coerce").astype("Int64"),
            "posicao_sigla": raw["Pos."],
            "jogador": raw["Name"].map(clean_name),
            "ano_chegada": pd.to_numeric(raw["Signed in"], errors="coerce").astype("Int64"),
            "fim_contrato": pd.to_numeric(raw["Contract end"], errors="coerce").astype("Int64"),
            "clube_anterior": raw["Signed from"],
            "taxa_transferencia_elenco": raw["Transfer fee"],
        }
    )


def parse_appearances(tables: list[pd.DataFrame]) -> pd.DataFrame:
    raw = find_table(
        tables,
        lambda t: isinstance(t.columns, pd.MultiIndex)
        and len(t.columns) == 16
        and "Apps" in t.columns.get_level_values(1),
    )
    raw = raw[raw.iloc[:, 1].isin(POSITION_MAP)].copy()
    columns = [
        "numero",
        "posicao_sigla",
        "jogador",
        "titular_brasileirao",
        "reserva_brasileirao",
        "titular_copa_brasil",
        "reserva_copa_brasil",
        "titular_libertadores",
        "reserva_libertadores",
        "titular_carioca",
        "reserva_carioca",
        "titular_outras",
        "reserva_outras",
        "titular_total",
        "reserva_total",
        "jogos_total",
    ]
    raw.columns = columns
    raw["jogador"] = raw["jogador"].map(clean_name)
    numeric_cols = [c for c in columns if c.startswith(("titular_", "reserva_")) or c == "jogos_total"]
    for col in numeric_cols:
        raw[col] = raw[col].map(number)

    for competition in ["brasileirao", "copa_brasil", "libertadores", "carioca", "outras"]:
        raw[f"jogos_{competition}"] = raw[f"titular_{competition}"] + raw[f"reserva_{competition}"]

    raw["numero"] = pd.to_numeric(raw["numero"], errors="coerce").astype("Int64")
    return raw


def find_player_table(tables: list[pd.DataFrame], footer_total: int) -> pd.DataFrame:
    for table in tables:
        if not {"Player", "Total", "Série A"}.issubset(set(map(str, table.columns))):
            continue
        footer = table[table["Player"].astype(str).eq("Total")]
        if not footer.empty and number(footer.iloc[0]["Total"]) == footer_total:
            return table.copy()
    raise ValueError(f"Tabela de jogadores com total {footer_total} não encontrada.")


def parse_player_metric(tables: list[pd.DataFrame], footer_total: int, prefix: str) -> pd.DataFrame:
    raw = find_player_table(tables, footer_total)
    raw = raw[~raw["Player"].isin(["Total", "Own Goal(s)"])].copy()
    raw["jogador"] = raw["Player"].map(clean_name)
    result = raw[["jogador"]].copy()
    mapping = {
        "Série A": "brasileirao",
        "Copa do Brasil": "copa_brasil",
        "Libertadores": "libertadores",
        "Carioca": "carioca",
        "Other[Note 1]": "outras",
        "Total": "total",
    }
    for source, suffix in mapping.items():
        result[f"{prefix}_{suffix}"] = raw[source].map(number)
    return result


def parse_players(tables: list[pd.DataFrame]) -> pd.DataFrame:
    roster = parse_roster(tables)
    appearances = parse_appearances(tables)
    goals = parse_player_metric(tables, footer_total=143, prefix="gols")
    assists = parse_player_metric(tables, footer_total=98, prefix="assistencias")

    for frame in (roster, appearances, goals, assists):
        frame["chave_jogador"] = frame["jogador"].map(slug)

    players = appearances.merge(goals.drop(columns="jogador"), on="chave_jogador", how="left")
    players = players.merge(assists.drop(columns="jogador"), on="chave_jogador", how="left")
    players = players.merge(
        roster.drop(columns=["jogador", "numero", "posicao_sigla"]),
        on="chave_jogador",
        how="outer",
        indicator="_roster",
    )

    metric_prefixes = ("gols_", "assistencias_", "jogos_", "titular_", "reserva_")
    metric_cols = [c for c in players.columns if c.startswith(metric_prefixes)]
    players[metric_cols] = players[metric_cols].fillna(0).astype(int)
    players["elenco_profissional_final"] = players["_roster"].eq("both") | players["_roster"].eq("right_only")
    players["posicao"] = players["posicao_sigla"].map(POSITION_MAP)
    players["grupo_posicao"] = players["posicao_sigla"].map(POSITION_GROUP)
    players["participacoes_gol"] = players["gols_total"] + players["assistencias_total"]
    players["status_2025"] = "Atuou em 2025; não estava no elenco final"
    players.loc[players["elenco_profissional_final"], "status_2025"] = "Elenco profissional ao fim de 2025"
    players.loc[(players["jogos_total"] == 0) & ~players["elenco_profissional_final"], "status_2025"] = "Base/inscrito sem atuação"
    players = players.drop(columns=["_roster", "chave_jogador"])
    return players.sort_values(["elenco_profissional_final", "jogos_total"], ascending=[False, False]).reset_index(drop=True)


def fee_kind(text: str) -> str:
    value = slug(text)
    if value.startswith("r") and ("m" in value or "e" in value):
        return "Valor divulgado"
    if "loanreturn" in value:
        return "Retorno de empréstimo"
    if value == "free":
        return "Sem custo"
    if "endofcontract" in value:
        return "Fim de contrato"
    if "undisclosed" in value:
        return "Valor não divulgado"
    if "released" in value:
        return "Liberado"
    return str(text)


def extract_fee(text: object, currency: str) -> float | None:
    value = str(text)
    pattern = r"R\$\s*([\d.]+)m" if currency == "BRL" else r"€\s*([\d.]+)m"
    match = re.search(pattern, value)
    return float(match.group(1)) if match else None


def parse_transfers(tables: list[pd.DataFrame]) -> pd.DataFrame:
    incoming = find_table(tables, lambda t: "Transferred from" in set(map(str, t.columns)))
    outgoing = find_table(tables, lambda t: "Transferred to" in set(map(str, t.columns)))

    def shape(frame: pd.DataFrame, direction: str) -> pd.DataFrame:
        frame = frame[frame["Player"] != "Total"].copy()
        club_col = "Transferred from" if direction == "Entrada" else "Transferred to"
        return pd.DataFrame(
            {
                "direcao": direction,
                "posicao_sigla": frame["Pos."],
                "jogador": frame["Player"].map(clean_name),
                "clube_origem_destino": frame[club_col],
                "taxa_fonte": frame["Fee"],
                "tipo_taxa": frame["Fee"].map(fee_kind),
                "valor_brl_milhoes": frame["Fee"].map(lambda x: extract_fee(x, "BRL")),
                "valor_eur_milhoes": frame["Fee"].map(lambda x: extract_fee(x, "EUR")),
                "data": pd.to_datetime(frame["Date"], format="mixed", errors="coerce").dt.date,
                "categoria": frame["Team"],
                "fonte": SOURCE_URL,
            }
        )

    return pd.concat([shape(incoming, "Entrada"), shape(outgoing, "Saída")], ignore_index=True)


def supporting_trophies() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trofeu": "Taça Guanabara",
                "competicao_principal": "Campeonato Carioca",
                "resultado": "Campeão",
                "observacao": "Troféu da primeira fase do Campeonato Carioca; não contado como competição separada.",
            },
            {
                "trofeu": "Derby das Américas",
                "competicao_principal": "Copa Intercontinental da FIFA",
                "resultado": "Campeão",
                "observacao": "Troféu do jogo da segunda fase contra o Cruz Azul.",
            },
            {
                "trofeu": "Copa Challenger",
                "competicao_principal": "Copa Intercontinental da FIFA",
                "resultado": "Campeão",
                "observacao": "Troféu do play-off contra o Pyramids; o Flamengo foi vice da competição principal.",
            },
        ]
    )


def source_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "tema": "Base consolidada da temporada, partidas, elenco, gols, assistências e transferências",
                "fonte": "2025 CR Flamengo season",
                "url": SOURCE_URL,
            },
            {
                "tema": "Campanha oficial do Campeonato Brasileiro",
                "fonte": "CBF — histórico e estatísticas do Flamengo no Brasileirão 2025",
                "url": "https://www.cbf.com.br/futebol-brasileiro/times/campeonato-brasileiro/serie-a/2025/20016/20031?tab=historico-de-partidas",
            },
            {
                "tema": "Título do Campeonato Brasileiro",
                "fonte": "CBF — Flamengo é campeão do Brasileirão 2025",
                "url": "https://www.cbf.com.br/futebol-brasileiro/noticias/campeonato-brasileiro/serie-a/flamengo-e-campeao-do-brasileirao-betano-2025",
            },
            {
                "tema": "Título da Supercopa Rei",
                "fonte": "CBF — Flamengo é tricampeão da Supercopa Rei",
                "url": "https://www.cbf.com.br/futebol-brasileiro/noticias/jogosdehoje-supercopa/a/flamengo-e-tricampeao-da-supercopa-rei",
            },
            {
                "tema": "Título do Campeonato Carioca",
                "fonte": "Flamengo — campeão carioca pela 39ª vez",
                "url": "https://www.flamengo.com.br/noticias/futebol/mengao-fica-no-0-a-0-com-o-fluminense-e-conquista-o-campeonato-carioca-pela-39--vez",
            },
            {
                "tema": "Taça Guanabara",
                "fonte": "Flamengo — 25º título da Taça Guanabara",
                "url": "https://www.flamengo.com.br/noticias/futebol/mengao-goleia-o-marica-e-conquista-o-25--titulo-da-taca-guanabara",
            },
            {
                "tema": "Título da CONMEBOL Libertadores",
                "fonte": "CBF — Flamengo conquista o tetra da Libertadores",
                "url": "https://www.cbf.com.br/futebol-brasileiro/noticias/campeonato-brasileiro/serie-b/flamengo-vence-palmeiras-e-ganha-o-tetra-da-libertadores",
            },
            {
                "tema": "Eliminação na Copa do Mundo de Clubes",
                "fonte": "FIFA — Flamengo 2 x 4 Bayern de Munique",
                "url": "https://www.fifa.com/pt/tournaments/mens/club-world-cup/usa-2025/articles/flamengo-bayern-munique-resumo-melhores-momentos-video-oitavas-final",
            },
            {
                "tema": "Vice-campeonato da Copa Intercontinental",
                "fonte": "FIFA — informações da Copa Intercontinental 2025",
                "url": "https://www.fifa.com/pt/tournaments/mens/intercontinentalcup/2025/articles/copa-intercontinental-2025-informacoes-data-local-clubes",
            },
            {
                "tema": "Escudo usado no cabeçalho",
                "fonte": "Wikimedia Commons — Clube de Regatas do Flamengo logo.svg",
                "url": "https://commons.wikimedia.org/wiki/File:Flamengo_braz_logo.svg",
            },
        ]
    )


def write_outputs(source_bytes: bytes, output: Path) -> dict[str, pd.DataFrame]:
    output.mkdir(parents=True, exist_ok=True)
    tables = get_tables(source_bytes)
    datasets = {
        "competicoes_2025.csv": parse_competitions(tables),
        "jogos_2025.csv": parse_matches(source_bytes),
        "jogadores_2025.csv": parse_players(tables),
        "transferencias_2025.csv": parse_transfers(tables),
        "trofeus_internos_2025.csv": supporting_trophies(),
        "fontes.csv": source_catalog(),
    }
    for filename, frame in datasets.items():
        frame.to_csv(output / filename, index=False, encoding="utf-8")
    return datasets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="HTML local opcional para execução reprodutível/offline.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source_bytes = args.html.read_bytes() if args.html else download_source()
    datasets = write_outputs(source_bytes, args.output)
    print("Dados preparados:")
    for name, frame in datasets.items():
        print(f"- {name}: {len(frame)} linhas")


if __name__ == "__main__":
    main()
