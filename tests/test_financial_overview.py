from datetime import date
from decimal import Decimal
import unittest

from financial_overview import cash_overview, reporting_sales, money_value


class CashOverviewTests(unittest.TestCase):
    def test_credit_is_revenue_once_and_receipt_is_only_cash(self):
        sales = [{"id": 1, "fecha": "2026-10-01", "monto_total": "100.10"}]
        summary = {"period_credit_sales": "80.20", "period_receipts": "30.05", "outstanding_as_of": "50.15"}
        result = cash_overview(sales, summary, date(2026,10,1), date(2026,10,31))
        self.assertEqual(result["total_sales"], Decimal("180.30"))
        self.assertEqual(result["collected"], Decimal("130.15"))
        self.assertEqual(result["collected_plus_outstanding"], Decimal("180.30"))

    def test_old_debt_receipts_do_not_become_new_sales(self):
        summary = {"period_credit_sales": 0, "period_receipts": "40", "outstanding_as_of": "60"}
        result = cash_overview([], summary, date(2026,10,1), date(2026,10,31))
        self.assertEqual(result["total_sales"], 0)
        self.assertEqual(result["collected"], 40)
        self.assertEqual(result["collected_plus_outstanding"], 100)

    def test_paid_sales_respect_period(self):
        sales = [{"id":1,"fecha":"2026-09-30","monto_total":999}, {"id":2,"fecha":"2026-10-01","monto_total":"0.10"}, {"id":3,"fecha":"2026-10-31","monto_total":"0.20"}]
        result = cash_overview(sales, {"period_credit_sales":0,"period_receipts":0,"outstanding_as_of":0}, date(2026,10,1), date(2026,10,31))
        self.assertEqual(result["collected"], Decimal("0.30"))

    def test_reporting_has_credit_charges_but_no_payment_rows(self):
        data = {"cargos":[{"id":1,"fecha":"2026-10-01","producto":"Prueba","presentacion":"Entero","cantidad":2,"monto_total":"42.25","costo_total":"20.15"}],"pagos":[{"id":1,"monto":12}]}
        result = reporting_sales([], data)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["ganancia_limpia"],Decimal("22.10"))
        self.assertEqual(result[0]["referencia"],"cuenta:1")

    def test_invalid_money_is_not_silently_zero(self):
        for value in (None, "nan", "Infinity", "incorrecto"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                money_value(value)


if __name__ == "__main__":
    unittest.main()
