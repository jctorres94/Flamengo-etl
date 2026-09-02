from __future__ import annotations

import unittest

from src.data import data_quality_checks, load_data


class FlamengoDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()

    def test_competitions(self):
        competitions = self.data["competicoes"]
        self.assertEqual(len(competitions), 7)
        self.assertEqual(int(competitions["campeao"].sum()), 4)
        self.assertEqual(int(competitions["jogos"].sum()), 78)

    def test_match_reconciliation(self):
        matches = self.data["jogos"]
        self.assertEqual(len(matches), 78)
        self.assertEqual(matches["resultado"].value_counts().to_dict(), {"Vitória": 49, "Empate": 18, "Derrota": 11})
        self.assertEqual(int(matches["gols_flamengo"].sum()), 143)
        self.assertEqual(int(matches["gols_adversario"].sum()), 51)
        self.assertEqual(int(matches["no_maracana"].sum()), 37)
        self.assertEqual(int((~matches["no_maracana"]).sum()), 41)

    def test_players(self):
        players = self.data["jogadores"]
        self.assertEqual(int(players["elenco_profissional_final"].sum()), 31)
        self.assertEqual(int(players["gols_total"].sum()), 142)
        self.assertEqual(int(players["assistencias_total"].sum()), 99)
        top_scorer = players.loc[players["gols_total"].idxmax()]
        self.assertEqual(top_scorer["jogador"], "Giorgian de Arrascaeta")
        self.assertEqual(int(top_scorer["gols_total"]), 25)

    def test_transfers(self):
        transfers = self.data["transferencias"]
        incoming = transfers.loc[transfers["direcao"].eq("Entrada"), "valor_brl_milhoes"].sum()
        outgoing = transfers.loc[transfers["direcao"].eq("Saída"), "valor_brl_milhoes"].sum()
        self.assertAlmostEqual(incoming, 308.7, places=1)
        self.assertAlmostEqual(outgoing, 523.5, places=1)
        self.assertAlmostEqual(outgoing - incoming, 214.8, places=1)

    def test_quality_checks(self):
        checks = data_quality_checks(self.data)
        self.assertTrue(all(check["ok"] for check in checks), checks)


if __name__ == "__main__":
    unittest.main()
