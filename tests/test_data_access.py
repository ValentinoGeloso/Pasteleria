from types import SimpleNamespace
import unittest

from data_access import fetch_all_rows, IncompleteReadError


class FakeDB:
    def __init__(self, rows, cap=1000):
        self.rows = rows
        self.cap = cap
        self.exact_count = True
        self.fail_after_cursor = False
        self.ignore_cursor = False
        self.append_on_cursor = False
        self.delete_on_cursor = False

    def table(self, name):
        return Query(self)


class Query:
    def __init__(self, db):
        self.db = db
        self.upper = None
        self.cursor = None
        self.desc = False
        self.maximum = 1000
        self.head = False
        self.columns = "*"

    def select(self, columns, count=None, head=False):
        self.columns = columns
        self.head = head
        return self

    def lte(self, column, value):
        self.upper = value
        return self

    def gt(self, column, value):
        self.cursor = value
        return self

    def order(self, column, desc=False):
        self.desc = desc
        return self

    def limit(self, maximum):
        self.maximum = maximum
        return self

    def execute(self):
        if self.cursor is not None and self.db.fail_after_cursor:
            raise ConnectionError("synthetic network failure")
        if self.cursor is not None and self.db.append_on_cursor:
            self.db.rows.append({"id": 99999, "value": "new"})
            self.db.append_on_cursor = False
        if self.cursor is not None and self.db.delete_on_cursor:
            self.db.rows.pop()
            self.db.delete_on_cursor = False
        rows = sorted(self.db.rows, key=lambda r: r["id"], reverse=self.desc)
        if self.upper is not None:
            rows = [r for r in rows if r["id"] <= self.upper]
        if self.cursor is not None and not self.db.ignore_cursor:
            rows = [r for r in rows if r["id"] > self.cursor]
        count = len(rows) if self.db.exact_count else None
        rows = rows[:min(self.maximum, self.db.cap)]
        if self.columns != "*":
            fields = [c.strip() for c in self.columns.split(",")]
            rows = [{k: r[k] for k in fields} for r in rows]
        return SimpleNamespace(data=[] if self.head else rows, count=count)


class PaginationTests(unittest.TestCase):
    def test_over_api_limit_preserves_every_row(self):
        rows = [{"id": i * 3, "value": f"test-{i}"} for i in range(1, 1506)]
        self.assertEqual(fetch_all_rows(FakeDB(rows), "ventas"), rows)

    def test_server_cap_smaller_than_page_size(self):
        rows = [{"id": i, "value": "test"} for i in range(1, 103)]
        self.assertEqual(fetch_all_rows(FakeDB(rows, cap=7), "ventas", "value"), rows)

    def test_empty_table(self):
        self.assertEqual(fetch_all_rows(FakeDB([]), "ventas"), [])

    def test_no_count_does_not_return_unverified_rows(self):
        db = FakeDB([{"id": 1}])
        db.exact_count = False
        with self.assertRaises(IncompleteReadError):
            fetch_all_rows(db, "ventas")

    def test_second_page_failure_does_not_return_partial_result(self):
        db = FakeDB([{"id": 1}, {"id": 2}], cap=1)
        db.fail_after_cursor = True
        with self.assertRaises(ConnectionError):
            fetch_all_rows(db, "ventas")

    def test_non_advancing_page_is_rejected(self):
        db = FakeDB([{"id": 1}, {"id": 2}], cap=1)
        db.ignore_cursor = True
        with self.assertRaises(IncompleteReadError):
            fetch_all_rows(db, "ventas")

    def test_new_sales_after_upper_id_wait_for_next_read(self):
        rows = [{"id": 1}, {"id": 2}]
        db = FakeDB(list(rows), cap=1)
        db.append_on_cursor = True
        self.assertEqual(fetch_all_rows(db, "ventas"), rows)

    def test_concurrent_deletion_is_rejected(self):
        db = FakeDB([{"id": 1}, {"id": 2}], cap=1)
        db.delete_on_cursor = True
        with self.assertRaises(IncompleteReadError):
            fetch_all_rows(db, "ventas")


if __name__ == "__main__":
    unittest.main()
