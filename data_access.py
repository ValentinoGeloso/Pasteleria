"""Lecturas completas por clave primaria, sin escribir en la base."""


class IncompleteReadError(RuntimeError):
    """La consulta no pudo demostrar que recuperó todas las filas esperadas."""


def fetch_all_rows(client, table, columns="*", page_size=500):
    """Lee por id hasta un límite superior fijo y comprueba el conteo exacto.

    Tolera límites de API menores que page_size. No es una transacción entre
    solicitudes: para cierres contables concurrentes se necesita un snapshot SQL.
    """
    if not isinstance(page_size, int) or not 1 <= page_size <= 1000:
        raise ValueError("page_size fuera de rango")
    if columns != "*" and "id" not in {c.strip() for c in columns.split(",")}:
        columns = "id, " + columns

    newest = client.table(table).select("id").order("id", desc=True).limit(1).execute().data
    if not newest:
        return []
    upper_id = newest[0]["id"]
    expected = client.table(table).select("id", count="exact", head=True).lte("id", upper_id).execute().count
    if expected is None:
        raise IncompleteReadError("No se obtuvo el conteo exacto")

    rows = []
    cursor = None
    while True:
        query = client.table(table).select(columns).lte("id", upper_id).order("id").limit(page_size)
        if cursor is not None:
            query = query.gt("id", cursor)
        batch = query.execute().data
        if batch is None:
            raise IncompleteReadError("Respuesta sin datos")
        if not batch:
            break
        for row in batch:
            row_id = row["id"]
            if row_id > upper_id or (cursor is not None and row_id <= cursor):
                raise IncompleteReadError("La paginación no avanzó por clave primaria")
            cursor = row_id
            rows.append(row)
        if len(rows) > expected:
            raise IncompleteReadError("El conjunto cambió durante la lectura")

    final_count = client.table(table).select("id", count="exact", head=True).lte("id", upper_id).execute().count
    if len(rows) != expected or final_count != expected:
        raise IncompleteReadError("Lectura incompleta o modificada durante la consulta")
    return rows
