"""Pure accounting and service boundary tests; no network or real customer data."""
import copy
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import customer_accounts as accounts


def ledger_fixture():
    return {
        "clientes": [{"id": 1, "nombre": "Persona de prueba A"}, {"id": 2, "nombre": "Persona de prueba B"}],
        "cargos": [
            {"id": 1, "cliente_id": 1, "fecha": "2026-01-10", "producto": "Producto A", "presentacion": "Unidad", "cantidad": 1, "precio_unitario": "100.00", "monto_total": "100.00", "costo_total": "30.00"},
            {"id": 2, "cliente_id": 1, "fecha": "2026-02-12", "producto": "Producto B", "presentacion": "Unidad", "cantidad": 2, "precio_unitario": "100.00", "monto_total": "200.00", "costo_total": "80.00"},
            {"id": 3, "cliente_id": 2, "fecha": "2026-02-15", "producto": "Producto C", "presentacion": "Unidad", "cantidad": 1, "precio_unitario": "50.00", "monto_total": "50.00", "costo_total": "20.00"},
        ],
        "pagos": [
            {"id": 1, "cliente_id": 1, "fecha": "2026-02-10", "monto": "40.00", "nota": "Parcial"},
            {"id": 2, "cliente_id": 1, "fecha": "2026-03-05", "monto": "60.00", "nota": "Completa producto A"},
            {"id": 3, "cliente_id": 1, "fecha": "2026-02-22", "monto": "75.00", "nota": "Parcial producto B"},
        ],
        "aplicaciones": [
            {"id": 1, "cliente_id": 1, "pago_id": 1, "cargo_id": 1, "monto": "40.00"},
            {"id": 2, "cliente_id": 1, "pago_id": 2, "cargo_id": 1, "monto": "60.00"},
            {"id": 3, "cliente_id": 1, "pago_id": 3, "cargo_id": 2, "monto": "75.00"},
        ],
    }


class AccountingTests(unittest.TestCase):
    def test_credit_sales_receipts_and_global_balance_are_separate(self):
        summary = accounts.summarize_accounts(ledger_fixture(), date(2026, 2, 1), date(2026, 2, 28))
        self.assertEqual(summary["period_credit_sales"], Decimal("250.00"))
        self.assertEqual(summary["period_credit_cost"], Decimal("100.00"))
        self.assertEqual(summary["period_receipts"], Decimal("115.00"))
        # Includes January's remaining debt, not merely unpaid February charges.
        self.assertEqual(summary["outstanding_as_of"], Decimal("235.00"))
        self.assertEqual(summary["outstanding_now"], Decimal("175.00"))
        self.assertEqual(summary["by_customer"][1]["outstanding"], Decimal("185.00"))
        self.assertEqual(summary["by_customer"][2]["outstanding"], Decimal("50.00"))

    def test_selected_product_payment_changes_only_its_balance(self):
        summary = accounts.summarize_accounts(ledger_fixture(), hasta="2026-02-28")
        self.assertEqual(summary["per_charge"][1]["paid"], Decimal("40.00"))
        self.assertEqual(summary["per_charge"][2]["paid"], Decimal("75.00"))
        self.assertEqual(summary["per_charge"][3]["paid"], Decimal("0.00"))
        self.assertEqual(summary["per_charge"][2]["outstanding"], Decimal("125.00"))

    def test_future_charge_and_payment_do_not_change_past_balance(self):
        data = ledger_fixture()
        data["cargos"].append({"id": 4, "cliente_id": 2, "fecha": "2026-04-01", "producto": "Producto futuro", "presentacion": "Unidad", "cantidad": 1, "precio_unitario": "120.00", "monto_total": "120.00", "costo_total": "20.00"})
        summary = accounts.summarize_accounts(data, "2026-02-01", "2026-02-28")
        self.assertEqual(summary["outstanding_as_of"], Decimal("235.00"))
        self.assertEqual(summary["outstanding_now"], Decimal("295.00"))
        self.assertNotIn(4, summary["per_charge"])

    def test_empty_account_and_standalone_person_have_zero_balance(self):
        data = {"clientes": [{"id": 10, "nombre": "Sin productos"}], "cargos": [], "pagos": [], "aplicaciones": []}
        summary = accounts.summarize_accounts(data)
        for key in ("period_credit_sales", "period_credit_cost", "period_receipts", "outstanding_as_of"):
            self.assertEqual(summary[key], Decimal("0.00"))
        self.assertEqual(summary["by_customer"][10]["outstanding"], Decimal("0.00"))

    def test_decimal_precision_and_half_up_rounding(self):
        self.assertEqual(accounts.decimal_amount("12.345"), Decimal("12.35"))
        self.assertEqual(accounts.decimal_amount(0.1) + accounts.decimal_amount(0.2), Decimal("0.30"))
        for value in (None, "not money", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(accounts.AccountsValidationError):
                accounts.decimal_amount(value)

    def test_incomplete_or_cross_customer_allocation_is_rejected(self):
        incomplete = ledger_fixture()
        incomplete["aplicaciones"].pop()
        cross_customer = ledger_fixture()
        cross_customer["aplicaciones"][0]["cargo_id"] = 3
        for data in (incomplete, cross_customer):
            with self.assertRaises(accounts.AccountsValidationError):
                accounts.summarize_accounts(data)

    def test_duplicate_allocations_and_overpayment_are_rejected(self):
        duplicate = ledger_fixture()
        duplicate["aplicaciones"].append({**duplicate["aplicaciones"][0], "id": 4})
        excess = ledger_fixture()
        excess["pagos"][0]["monto"] = "101.00"
        excess["aplicaciones"][0]["monto"] = "101.00"
        for data in (duplicate, excess):
            with self.assertRaises(accounts.AccountsValidationError):
                accounts.summarize_accounts(data)

    def test_backdated_payment_before_delivery_is_rejected(self):
        data = ledger_fixture()
        data["pagos"][2]["fecha"] = "2026-02-01"
        with self.assertRaises(accounts.AccountsValidationError):
            accounts.summarize_accounts(data)

    def test_inverted_period_is_rejected_and_source_is_not_mutated(self):
        data = ledger_fixture()
        before = copy.deepcopy(data)
        accounts.summarize_accounts(data, "2026-02-01", "2026-02-28")
        self.assertEqual(data, before)
        with self.assertRaises(accounts.AccountsValidationError):
            accounts.summarize_accounts(data, "2026-03-01", "2026-02-01")

    def test_loader_retries_inconsistent_snapshot_and_never_falls_back_to_zero(self):
        data = ledger_fixture()
        incomplete = copy.deepcopy(data)
        incomplete["aplicaciones"] = []
        batches = [incomplete[k] for k in accounts.TABLES] + [data[k] for k in accounts.TABLES]
        with patch.object(accounts, "fetch_all_rows", side_effect=batches) as reader:
            self.assertEqual(accounts.load_accounts(object()), data)
            self.assertEqual(reader.call_count, 8)
        with patch.object(accounts, "fetch_all_rows", side_effect=ConnectionError("sensitive sentinel")):
            with self.assertRaises(accounts.AccountsUnavailableError) as caught:
                accounts.load_accounts(object())
            self.assertNotIn("sensitive sentinel", str(caught.exception))


class Rejected(ValueError):
    code = "22023"


class FakeQuery:
    def __init__(self, client, name):
        self.client, self.name = client, name
        self.filters = []
        self.payload = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, value):
        return self

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        rows = self.client.data[self.name]
        if self.payload is not None:
            record = {"id": len(rows) + 1, **self.payload}
            rows.append(record)
            if self.client.lose_insert_response:
                self.client.lose_insert_response = False
                raise ConnectionError("response lost after commit")
            return SimpleNamespace(data=[record])
        return SimpleNamespace(data=[r for r in rows if all(r.get(k) == v for k, v in self.filters)])


class FakeClient:
    def __init__(self):
        self.data = {"cuentas_clientes": []}
        self.calls = []
        self.lose_insert_response = False
        self.rpc_result = {"id": 77}

    def table(self, table):
        return FakeQuery(self, table)

    def rpc(self, name, params):
        self.calls.append((name, params))
        def execute():
            if name == "renombrar_cliente_cuenta":
                record = next(r for r in self.data["cuentas_clientes"] if r["id"] == params["p_cliente_id"])
                if record["nombre"] == params["p_nombre"]:
                    return SimpleNamespace(data=[copy.deepcopy(record)])
                if record["nombre"] != params["p_nombre_anterior"]:
                    raise Rejected("Concurrent name change")
                record["nombre"] = params["p_nombre"]
                return SimpleNamespace(data=copy.deepcopy(record))
            return SimpleNamespace(data=self.rpc_result)
        return SimpleNamespace(execute=execute)


class ServiceTests(unittest.TestCase):
    def test_standalone_customer_retry_recovers_lost_response_without_duplicate(self):
        client = FakeClient()
        client.lose_insert_response = True
        first = accounts.create_customer(client, "  Persona nueva  ", "test-request")
        second = accounts.create_customer(client, "Persona nueva", "test-request")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(client.data["cuentas_clientes"]), 1)
        self.assertEqual(first["nombre"], "Persona nueva")

    def test_same_customer_request_cannot_be_reused_for_another_name(self):
        client = FakeClient()
        accounts.create_customer(client, "Una persona", "test-request")
        with self.assertRaises(accounts.AccountsValidationError):
            accounts.create_customer(client, "Otra persona", "test-request")
        self.assertEqual(len(client.data["cuentas_clientes"]), 1)

    def test_rename_is_trimmed_idempotent_and_changes_only_name(self):
        client = FakeClient()
        client.data["cuentas_clientes"] = [{"id": 3, "nombre": "Nombre anterior", "request_id": "original", "created_at": "2026-01-01"}]
        before = copy.deepcopy(client.data["cuentas_clientes"][0])
        first = accounts.rename_customer(client, 3, "  Nombre corregido  ", "Nombre anterior")
        second = accounts.rename_customer(client, 3, "Nombre corregido", "Nombre anterior")
        self.assertEqual(first, second)
        self.assertEqual(first, {**before, "nombre": "Nombre corregido"})
        self.assertEqual(client.calls[0], ("renombrar_cliente_cuenta", {"p_cliente_id": 3, "p_nombre": "Nombre corregido", "p_nombre_anterior": "Nombre anterior"}))

    def test_rename_rejects_conflicting_previous_name(self):
        client = FakeClient()
        client.data["cuentas_clientes"] = [{"id": 3, "nombre": "Editado por otra persona"}]
        with self.assertRaises(Rejected):
            accounts.rename_customer(client, 3, "Mi edición", "Nombre viejo")
        self.assertEqual(client.data["cuentas_clientes"][0]["nombre"], "Editado por otra persona")

    def test_name_validation_does_not_send_invalid_requests(self):
        client = FakeClient()
        for name in ("   ", "x" * 161):
            with self.subTest(name_length=len(name)), self.assertRaises(accounts.AccountsValidationError):
                accounts.rename_customer(client, 3, name, "Anterior")
            with self.assertRaises(accounts.AccountsValidationError):
                accounts.create_customer(client, name, "test-request")
        self.assertEqual(client.calls, [])
        self.assertEqual(client.data["cuentas_clientes"], [])

    def test_charge_rpc_preserves_exact_money_and_never_touches_ventas(self):
        client = FakeClient()
        accounts.create_charge(client, cliente_id=3, fecha=date(2026, 10, 29), producto="Producto de prueba", presentacion="Unidad", cantidad=2, precio_unitario="12.345", costo_total="2.005", request_id="test-request")
        name, payload = client.calls[0]
        self.assertEqual(name, "crear_cargo_cuenta")
        self.assertEqual(payload["p_precio_unitario"], "12.35")
        self.assertEqual(payload["p_costo_total"], "2.01")
        self.assertEqual(payload["p_cantidad"], 2)
        self.assertEqual(payload["p_fecha"], "2026-10-29")
        self.assertEqual(set(client.data), {"cuentas_clientes"})

    def test_selected_payment_rpc_canonicalizes_ids_and_money(self):
        client = FakeClient()
        accounts.register_payment(client, cliente_id=3, fecha="2026-10-29", monto="0.30", nota="  Parcial  ", request_id="test-request", cargo_ids=[5, 2, 5])
        name, payload = client.calls[0]
        self.assertEqual(name, "registrar_pago_cuenta")
        self.assertEqual(payload["p_monto"], "0.30")
        self.assertEqual(payload["p_cargo_ids"], [2, 5])
        self.assertEqual(payload["p_nota"], "Parcial")
        self.assertEqual(len(client.calls), 1)

    def test_invalid_payment_or_quantity_is_rejected_before_rpc(self):
        client = FakeClient()
        for amount, selection in ((0, None), (-1, None), (10, [])):
            with self.assertRaises(accounts.AccountsValidationError):
                accounts.register_payment(client, cliente_id=3, fecha="2026-10-29", monto=amount, nota="", request_id="test", cargo_ids=selection)
        for quantity in (0, -1, 1.5, True):
            with self.assertRaises(accounts.AccountsValidationError):
                accounts.create_charge(client, cliente_id=3, fecha="2026-10-29", producto="Producto", presentacion="Unidad", cantidad=quantity, precio_unitario=10, costo_total=1, request_id="test")
        self.assertEqual(client.calls, [])

    def test_uncertain_server_response_is_not_reported_as_validation_failure(self):
        client = FakeClient()
        client.rpc_result = []
        with self.assertRaises(accounts.AccountsUnconfirmedError):
            accounts.register_payment(client, cliente_id=1, fecha="2026-10-29", monto=10, nota="", request_id="test")

    def test_request_token_stable_for_retry_and_payment_completion_gate(self):
        state = {}
        with patch.object(accounts.st, "session_state", state):
            first = accounts._request_token("payment", {"monto": "20.00", "cliente": 1})
            self.assertEqual(first, accounts._request_token("payment", {"cliente": 1, "monto": "20.00"}))
            self.assertNotEqual(first, accounts._request_token("payment", {"cliente": 1, "monto": "30.00"}))
            accounts._complete("payment", 1)
            self.assertTrue(state["_cuentas_payment_complete"])
            accounts._complete("person", 4)
            self.assertEqual(state["_cuentas_person_complete"], 4)


if __name__ == "__main__":
    unittest.main()
