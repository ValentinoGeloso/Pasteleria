import unittest

import pandas as pd

from dashboard_charts import aggregate_evolution


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.sales = pd.DataFrame([
            {"fecha": "2026-10-25", "monto_total": 100, "costo_total": 40, "ganancia_limpia": 60},
            {"fecha": "2026-10-26", "monto_total": 200, "costo_total": 90, "ganancia_limpia": 110},
            {"fecha": "2026-11-01", "monto_total": 300, "costo_total": 120, "ganancia_limpia": 180},
            {"fecha": "2026-11-02", "monto_total": 400, "costo_total": 160, "ganancia_limpia": 240},
        ])

    def test_monday_sunday_boundary_and_cross_month_week(self):
        result = aggregate_evolution(self.sales, "Semanal")
        self.assertEqual(result["Periodo"].dt.strftime("%Y-%m-%d").tolist(), ["2026-10-19", "2026-10-26", "2026-11-02"])
        self.assertEqual(result["Facturación"].tolist(), [100, 500, 400])
        self.assertEqual(result["Margen"].tolist(), [60, 290, 240])
        self.assertEqual(result["Etiqueta"].iloc[1], "26/10/2026 al 01/11/2026")

    def test_all_cadences_preserve_selected_totals(self):
        for cadence in ("Diaria", "Semanal", "Mensual"):
            with self.subTest(cadence=cadence):
                result = aggregate_evolution(self.sales, cadence)
                self.assertEqual(result["Facturación"].sum(), self.sales["monto_total"].sum())
                self.assertEqual(result["Costo"].sum(), self.sales["costo_total"].sum())
                self.assertEqual(result["Margen"].sum(), self.sales["ganancia_limpia"].sum())

    def test_partial_week_does_not_add_unselected_sales(self):
        result = aggregate_evolution(self.sales.iloc[[1]], "Semanal")
        self.assertEqual(result["Facturación"].tolist(), [200])

    def test_empty_and_invalid_cadence(self):
        self.assertTrue(aggregate_evolution(self.sales.iloc[0:0], "Semanal").empty)
        with self.assertRaises(ValueError):
            aggregate_evolution(self.sales, "Anual")


if __name__ == "__main__":
    unittest.main()
