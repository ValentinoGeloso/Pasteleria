"""Pruebas de pantallas con identidad simulada; no prueban OAuth real."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest


APP = str(Path(__file__).resolve().parents[1] / "app.py")


class UITests(unittest.TestCase):
    def test_login_keeps_google_and_demo(self):
        with patch.object(st, "user", SimpleNamespace(is_logged_in=False)), patch("supabase.create_client") as client:
            at = AppTest.from_file(APP, default_timeout=20).run()
            self.assertFalse(at.exception)
            self.assertEqual([b.label for b in at.button], ["Iniciar sesión con Google", "Explorar demostración"])
            client.assert_not_called()

    def test_unauthorized_user_cannot_initialize_database(self):
        with patch.object(st, "user", SimpleNamespace(is_logged_in=True, email="unauthorized@example.invalid")), patch("supabase.create_client") as client:
            at = AppTest.from_file(APP, default_timeout=20).run()
            self.assertFalse(at.exception)
            self.assertTrue(any("no tiene autorización" in e.value for e in at.error))
            self.assertEqual(len(at.sidebar.radio), 0)
            client.assert_not_called()

    def test_demo_pages_never_initialize_database(self):
        with patch.object(st, "user", SimpleNamespace(is_logged_in=False)), patch("supabase.create_client") as client:
            at = AppTest.from_file(APP, default_timeout=20).run()
            at.button[1].click().run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.sidebar.radio[0].options), 3)
            for page in ("🏷️ Productos y Recetas", "🛒 Insumos y Costos", "⚙️ Calculadora de Costos"):
                at.sidebar.radio[0].set_value(page).run()
                self.assertFalse(at.exception)
                self.assertEqual(len(at.error), 0)
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
