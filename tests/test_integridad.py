"""Regresiones sin red ni secretos: ejecutan bloques reales de app.py con dobles."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "app.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))


class Stopped(BaseException):
    """Como st.stop, interrumpe incluso dentro de except Exception."""


class UI:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)

    def stop(self):
        raise Stopped()


class ReadOnlyDB:
    def __init__(self, rows=None, fail=False):
        self.rows = rows
        self.fail = fail
        self.reads = []

    def table(self, name):
        self.reads.append(name)
        return self

    def select(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def execute(self):
        if self.fail:
            raise RuntimeError("CONFIDENTIAL_SENTINEL")
        return SimpleNamespace(data=self.rows)

    # No insert/update/delete methods: any unexpected write fails the test.


def run_node(node, env):
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), env)


def load_function(name, db):
    ui = UI()
    env = {"st": ui, "supabase": db, "numero": lambda value, default: float(value or default), "fetch_all_rows": lambda client, table, *args: client.table(table).execute().data}
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)
    run_node(node, env)
    return env[name], ui


class CatalogTests(unittest.TestCase):
    def test_empty_catalog_stops_without_seeding(self):
        for name in ("obtener_insumos", "obtener_recetas"):
            with self.subTest(name=name):
                function, ui = load_function(name, ReadOnlyDB([]))
                with self.assertRaises(Stopped):
                    function()
                self.assertTrue(ui.errors)

    def test_failed_catalog_stops_without_disclosing_exception(self):
        for name in ("obtener_insumos", "obtener_recetas"):
            with self.subTest(name=name):
                function, ui = load_function(name, ReadOnlyDB(fail=True))
                with self.assertRaises(Stopped):
                    function()
                self.assertNotIn("CONFIDENTIAL_SENTINEL", " ".join(ui.errors))

    def test_existing_supplies_preserve_values(self):
        function, _ = load_function("obtener_insumos", ReadOnlyDB([{"nombre": "Prueba", "precio": 125.5}]))
        self.assertEqual(function(), {"Prueba": 125.5})

    def test_existing_recipes_preserve_ingredients_and_prices(self):
        recipe = {"nombre": "Prueba", "rinde": 8, "tipo": "porciones", "precios": {"Entero": 100}, "ingredientes": {"Naranja (kg)": 0.13}}
        function, _ = load_function("obtener_recetas", ReadOnlyDB([recipe]))
        self.assertEqual(function(), {"Prueba": {k: v for k, v in recipe.items() if k != "nombre"}})

    def test_private_normalization_does_not_read_or_write(self):
        node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "normalizar_naranjas_por_unidad")
        env = {"modo_invitado": False}
        run_node(node, env)
        # No database or session is supplied: even accessing either would fail.
        env[node.name]()


class ReportTests(unittest.TestCase):
    def test_query_failures_stop_dashboard_and_import(self):
        targets = {"ventas_data", "gastos_data", "mermas_data", "existentes"}
        checked = set()
        for node in ast.walk(TREE):
            if not isinstance(node, ast.Try) or not node.body:
                continue
            first = node.body[0]
            if not isinstance(first, ast.Assign):
                continue
            names = {t.id for t in first.targets if isinstance(t, ast.Name)} & targets
            if not names:
                continue
            with self.subTest(target=names):
                ui = UI()
                with self.assertRaises(Stopped):
                    run_node(node, {"st": ui, "supabase": ReadOnlyDB(fail=True), "fetch_all_rows": lambda client, table, *args: client.table(table).execute().data})
                self.assertTrue(ui.errors)
                self.assertNotIn("CONFIDENTIAL_SENTINEL", " ".join(ui.errors))
            checked |= names
        self.assertEqual(checked, targets)

    def test_empty_report_tables_remain_valid(self):
        for name in ("ventas_data", "gastos_data", "mermas_data"):
            node = next(n for n in ast.walk(TREE) if isinstance(n, ast.Try) and n.body and isinstance(n.body[0], ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.body[0].targets))
            env = {"st": UI(), "supabase": ReadOnlyDB([]), "fetch_all_rows": lambda client, table, *args: client.table(table).execute().data}
            run_node(node, env)
            self.assertEqual(env[name], [])
            self.assertEqual(env["st"].errors, [])


if __name__ == "__main__":
    unittest.main()
