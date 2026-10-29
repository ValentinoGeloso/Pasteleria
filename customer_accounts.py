"""Cuentas por cobrar: registros separados de las ventas cobradas existentes.

Los importes se calculan con Decimal. Los pagos se asignan transaccionalmente en
Postgres; esta capa no inserta pagos ni ventas por su cuenta y nunca toca ventas.
"""
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from uuid import uuid4

import pandas as pd
import streamlit as st

from data_access import fetch_all_rows
from dulce_mar_ui import render_page_header


CENT = Decimal("0.01")
ZERO = Decimal("0.00")
MAX_AMOUNT = Decimal("999999999999.99")
TABLES = {
    "clientes": "cuentas_clientes",
    "cargos": "cuentas_cargos",
    "pagos": "cuentas_pagos",
    "aplicaciones": "cuentas_aplicaciones",
}


class AccountsUnavailableError(RuntimeError):
    """No hay una lectura completa y consistente de las cuentas."""


class AccountsValidationError(ValueError):
    """Un dato no permite calcular o guardar la cuenta de forma segura."""


class AccountsUnconfirmedError(RuntimeError):
    """El servidor pudo guardar el movimiento, pero falta confirmar su respuesta."""


def decimal_amount(value):
    """Convertir un importe sin operaciones de punto flotante."""
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            raise InvalidOperation()
        return amount.quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise AccountsValidationError("Hay un importe inválido en las cuentas por cobrar.") from None


def _date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        raise AccountsValidationError("Hay una fecha inválida en las cuentas por cobrar.") from None


def _row_map(rows):
    result = {row["id"]: row for row in rows}
    if len(result) != len(rows):
        raise AccountsValidationError("La lectura contiene registros repetidos.")
    return result


def _validate_ledger(data):
    """Rechazar lecturas mezcladas o incompletas, en lugar de inventar saldos."""
    customers = _row_map(data["clientes"])
    charges = _row_map(data["cargos"])
    payments = _row_map(data["pagos"])
    _row_map(data["aplicaciones"])
    paid_by_charge = defaultdict(lambda: ZERO)
    allocated_by_payment = defaultdict(lambda: ZERO)
    pairs = set()
    for charge in charges.values():
        if charge["cliente_id"] not in customers:
            raise AccountsValidationError("Falta una cuenta vinculada a un producto.")
        quantity = charge["cantidad"]
        if isinstance(quantity, bool) or int(quantity) != quantity or int(quantity) <= 0:
            raise AccountsValidationError("Hay una cantidad inválida en los productos pendientes.")
        total = decimal_amount(charge["monto_total"])
        if total <= ZERO or total != decimal_amount(decimal_amount(charge["precio_unitario"]) * int(quantity)):
            raise AccountsValidationError("El importe de un producto pendiente no coincide con su cantidad y precio.")
        if decimal_amount(charge["costo_total"]) < ZERO:
            raise AccountsValidationError("Hay un costo inválido en los productos pendientes.")
        _date(charge["fecha"])
    for payment in payments.values():
        if payment["cliente_id"] not in customers or decimal_amount(payment["monto"]) <= ZERO:
            raise AccountsValidationError("Hay un pago inválido en las cuentas.")
        _date(payment["fecha"])
    for application in data["aplicaciones"]:
        charge = charges.get(application["cargo_id"])
        payment = payments.get(application["pago_id"])
        if charge is None or payment is None:
            raise AccountsValidationError("Falta un movimiento vinculado a un pago.")
        if charge["cliente_id"] != payment["cliente_id"] or application["cliente_id"] != charge["cliente_id"]:
            raise AccountsValidationError("Un pago está vinculado a una cuenta distinta.")
        if _date(payment["fecha"]) < _date(charge["fecha"]):
            raise AccountsValidationError("Un pago figura antes del producto al que corresponde.")
        amount = decimal_amount(application["monto"])
        pair = (payment["id"], charge["id"])
        if amount <= ZERO or pair in pairs:
            raise AccountsValidationError("La distribución de un pago no es válida.")
        pairs.add(pair)
        paid_by_charge[charge["id"]] += amount
        allocated_by_payment[payment["id"]] += amount
    for charge in charges.values():
        if paid_by_charge[charge["id"]] > decimal_amount(charge["monto_total"]):
            raise AccountsValidationError("Un producto tiene pagos superiores a su importe.")
    for payment in payments.values():
        if allocated_by_payment[payment["id"]] != decimal_amount(payment["monto"]):
            raise AccountsValidationError("La lectura de los pagos está incompleta.")


def load_accounts(client):
    """Leer las cuatro tablas completas; nunca convertir un fallo en saldo cero."""
    for attempt in range(2):
        try:
            data = {key: fetch_all_rows(client, table) for key, table in TABLES.items()}
            _validate_ledger(data)
            return data
        except Exception as error:
            if attempt:
                raise AccountsUnavailableError(
                    "No pudimos cargar las cuentas por cobrar completas. Volvé a intentar antes de registrar movimientos."
                ) from error
    raise AccountsUnavailableError("No pudimos cargar las cuentas por cobrar.")


def summarize_accounts(data, desde=None, hasta=None):
    """Devengado del período, cobros del período y deuda acumulada al cierre.

    ``outstanding_as_of`` incluye todos los cargos hasta ``hasta`` y resta solo
    aplicaciones de pagos con fecha hasta ese cierre. Los recibos nunca se suman
    como ventas. Sin fechas, el período y el saldo abarcan el registro completo.
    """
    _validate_ledger(data)
    start = _date(desde) if desde is not None else date.min
    end = _date(hasta) if hasta is not None else date.max
    if start > end:
        raise AccountsValidationError("La fecha inicial no puede ser posterior a la final.")
    payments = _row_map(data["pagos"])
    paid_as_of = defaultdict(lambda: ZERO)
    paid_now = defaultdict(lambda: ZERO)
    for application in data["aplicaciones"]:
        amount = decimal_amount(application["monto"])
        paid_now[application["cargo_id"]] += amount
        if _date(payments[application["pago_id"]]["fecha"]) <= end:
            paid_as_of[application["cargo_id"]] += amount
    by_customer = {
        customer["id"]: {"id": customer["id"], "nombre": customer["nombre"], "charged": ZERO, "paid": ZERO, "outstanding": ZERO}
        for customer in data["clientes"]
    }
    per_charge = {}
    period_sales = ZERO
    period_cost = ZERO
    outstanding = ZERO
    outstanding_now = ZERO
    for charge in data["cargos"]:
        amount = decimal_amount(charge["monto_total"])
        charge_date = _date(charge["fecha"])
        remaining_now = amount - paid_now[charge["id"]]
        outstanding_now += remaining_now
        if start <= charge_date <= end:
            period_sales += amount
            period_cost += decimal_amount(charge["costo_total"])
        if charge_date <= end:
            paid = paid_as_of[charge["id"]]
            remaining = amount - paid
            outstanding += remaining
            customer = by_customer[charge["cliente_id"]]
            customer["charged"] += amount
            customer["paid"] += paid
            customer["outstanding"] += remaining
            per_charge[charge["id"]] = {**charge, "total": amount, "paid": paid, "outstanding": remaining, "outstanding_now": remaining_now}
    receipts = sum((decimal_amount(p["monto"]) for p in data["pagos"] if start <= _date(p["fecha"]) <= end), ZERO)
    return {
        "period_credit_sales": period_sales,
        "period_credit_cost": period_cost,
        "period_receipts": receipts,
        "outstanding_as_of": outstanding,
        "outstanding_now": outstanding_now,
        "by_customer": by_customer,
        "per_charge": per_charge,
        # Aliases use the same cutoff and never a different accounting basis.
        "credit_sales": period_sales, "credit_cost": period_cost,
        "receipts": receipts, "outstanding": outstanding,
    }


def _first_row(response):
    rows = response.data
    if isinstance(rows, dict):
        return rows
    if isinstance(rows, list) and len(rows) == 1:
        return rows[0]
    raise AccountsUnconfirmedError("No se pudo confirmar el movimiento.")


def create_customer(client, nombre, request_id):
    name = str(nombre).strip()
    if not name or len(name) > 160:
        raise AccountsValidationError("Escribí un nombre de hasta 160 caracteres.")
    existing = client.table("cuentas_clientes").select("*").eq("request_id", str(request_id)).limit(1).execute().data or []
    if existing:
        if existing[0]["nombre"] != name:
            raise AccountsValidationError("El intento anterior tenía otro nombre. Revisá la cuenta antes de continuar.")
        return existing[0]
    try:
        return _first_row(client.table("cuentas_clientes").insert({"nombre": name, "request_id": str(request_id)}).execute())
    except Exception:
        # A request may commit and lose its response. Recover by its unique token.
        existing = client.table("cuentas_clientes").select("*").eq("request_id", str(request_id)).limit(1).execute().data or []
        if existing and existing[0]["nombre"] == name:
            return existing[0]
        raise


def create_charge(client, *, cliente_id, fecha, producto, presentacion, cantidad, precio_unitario, costo_total, request_id):
    if isinstance(cantidad, bool) or int(cantidad) != cantidad or int(cantidad) <= 0:
        raise AccountsValidationError("La cantidad debe ser un número entero mayor a cero.")
    price, cost = decimal_amount(precio_unitario), decimal_amount(costo_total)
    if price <= ZERO or cost < ZERO:
        raise AccountsValidationError("El precio debe ser mayor a cero y el costo no puede ser negativo.")
    if price * int(cantidad) > MAX_AMOUNT or cost > MAX_AMOUNT:
        raise AccountsValidationError("El importe del producto supera el máximo permitido. Revisá precio y cantidad.")
    return _first_row(client.rpc("crear_cargo_cuenta", {
        "p_cliente_id": int(cliente_id), "p_fecha": _date(fecha).isoformat(),
        "p_producto": str(producto), "p_presentacion": str(presentacion),
        "p_cantidad": int(cantidad), "p_precio_unitario": str(price),
        "p_costo_total": str(cost), "p_request_id": str(request_id),
    }).execute())


def register_payment(client, *, cliente_id, fecha, monto, nota, request_id, cargo_ids=None):
    amount = decimal_amount(monto)
    if amount <= ZERO:
        raise AccountsValidationError("El pago debe ser mayor a cero.")
    if amount > MAX_AMOUNT:
        raise AccountsValidationError("El pago supera el máximo permitido por movimiento. Registralo en partes.")
    if cargo_ids is not None and not cargo_ids:
        raise AccountsValidationError("Elegí al menos un producto para este pago.")
    return _first_row(client.rpc("registrar_pago_cuenta", {
        "p_cliente_id": int(cliente_id), "p_fecha": _date(fecha).isoformat(),
        "p_monto": str(amount), "p_nota": str(nota or "").strip(),
        "p_request_id": str(request_id),
        "p_cargo_ids": sorted(set(int(i) for i in cargo_ids)) if cargo_ids is not None else None,
    }).execute())


def rename_customer(client, cliente_id, nombre, nombre_anterior):
    """Cambiar solo el nombre y rechazar una edición concurrente no revisada."""
    name = str(nombre).strip()
    previous = str(nombre_anterior).strip()
    if not name or len(name) > 160:
        raise AccountsValidationError("Escribí un nombre de hasta 160 caracteres.")
    if not previous:
        raise AccountsValidationError("Recargá la cuenta antes de cambiar el nombre.")
    return _first_row(client.rpc("renombrar_cliente_cuenta", {
        "p_cliente_id": int(cliente_id), "p_nombre": name,
        "p_nombre_anterior": previous,
    }).execute())


def _request_token(scope, payload):
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    key = "_cuentas_request_" + scope
    state = st.session_state.get(key)
    if state is None or state["fingerprint"] != fingerprint:
        state = {"fingerprint": fingerprint, "id": str(uuid4())}
        st.session_state[key] = state
    return state["id"]


def _clear_request(scope):
    st.session_state.pop("_cuentas_request_" + scope, None)


def _customer_labels(customers):
    duplicates = Counter(str(c["nombre"]).strip().casefold() for c in customers)
    return {
        c["id"]: c["nombre"] + (f" · Cuenta {c['id']}" if duplicates[str(c["nombre"]).strip().casefold()] > 1 else "")
        for c in customers
    }


def _amount_column(label):
    return st.column_config.NumberColumn(label, format="$ %.2f")


def _definite_rejection(error):
    # These are explicit PostgreSQL rejection responses, not missing network replies.
    return str(getattr(error, "code", "")) in {"22023", "22003", "22P02", "23502", "23503", "23505", "23514", "42501", "P0001"}


def _complete(scope, customer_id):
    _clear_request(scope)
    st.session_state.pop("_cuentas_pending_" + scope, None)
    if scope == "charge":
        _clear_request("customer")
        st.session_state["_cuentas_last_customer"] = customer_id
        st.session_state["_cuentas_flash"] = "Producto agregado a la cuenta. Todavía no se cuenta como dinero cobrado."
    elif scope == "payment":
        st.session_state["_cuentas_payment_complete"] = True
        st.session_state["_cuentas_flash"] = "Pago registrado. El saldo se actualizó sin duplicar la venta."
    elif scope == "person":
        st.session_state["_cuentas_person_complete"] = customer_id
        st.session_state["_cuentas_flash"] = "Persona creada. Ya podés agregar productos a su cuenta."
    elif scope == "rename":
        st.session_state["_cuentas_flash"] = "Nombre actualizado. Los productos, pagos y saldos siguen en la misma cuenta."


def _resolve_pending(client, data):
    """After an uncertain response, only retry the identical request, never a new payment."""
    actions = (
        ("charge", "cargos", create_charge, "producto", "Confirmar el producto anterior"),
        ("payment", "pagos", register_payment, "pago", "Confirmar el pago anterior"),
        ("person", "clientes", create_customer, "registro de persona", "Confirmar la persona anterior"),
        ("rename", "clientes", rename_customer, "cambio de nombre", "Confirmar el cambio de nombre"),
    )
    for scope, table, method, label, button in actions:
        key = "_cuentas_pending_" + scope
        pending = st.session_state.get(key)
        if not pending:
            continue
        matched = next((row for row in data[table] if (
            row["id"] == pending["cliente_id"] and row["nombre"] == pending["nombre"]
            if scope == "rename" else str(row.get("request_id")) == pending["request_id"]
        )), None)
        if matched is not None:
            _complete(scope, matched["id"] if scope == "person" else pending["cliente_id"])
            st.rerun()
        st.warning(f"Falta confirmar el último {label}. No registres otro movimiento hasta resolver este intento.")
        if st.button(button, type="primary", key="cuentas_retry_" + scope):
            try:
                result = method(client, **pending)
                _complete(scope, result["id"] if scope == "person" else pending["cliente_id"])
                st.rerun()
            except Exception as error:
                if _definite_rejection(error):
                    st.session_state.pop(key, None)
                    _clear_request(scope)
                    st.session_state["_cuentas_error"] = "El movimiento fue rechazado. Revisá el saldo y los datos antes de volver a registrarlo."
                    st.rerun()
                st.error("Todavía no pudimos confirmar la respuesta. Volvé a intentar; se conserva el mismo movimiento para evitar duplicados.")
        return True
    return False


def render_accounts_page(client, recetas, calculate_cost, today, money_formatter):
    """Native Streamlit account management; all persistence goes through the service API."""
    render_page_header("Cuentas por cobrar", "Los productos entregados, lo que pagó cada persona y el saldo que falta cobrar.")
    flash = st.session_state.pop("_cuentas_flash", None)
    if flash:
        st.success(flash)
    previous_error = st.session_state.pop("_cuentas_error", None)
    if previous_error:
        st.error(previous_error)
    try:
        data = load_accounts(client)
        summary = summarize_accounts(data, hasta=today)
    except (AccountsUnavailableError, AccountsValidationError) as error:
        st.error(str(error))
        return
    customers = sorted(data["clientes"], key=lambda c: (str(c["nombre"]).casefold(), c["id"]))
    labels = _customer_labels(customers)
    customer_ids = [c["id"] for c in customers]
    current = summary["per_charge"]
    overdue_customers = sum(c["outstanding"] > ZERO for c in summary["by_customer"].values())
    top1, top2 = st.columns(2)
    top1.metric("Saldo pendiente de cobro", money_formatter(summary["outstanding_as_of"]))
    top2.metric("Cuentas con saldo", str(overdue_customers))
    if _resolve_pending(client, data):
        return
    last_customer = st.session_state.pop("_cuentas_last_customer", None)
    if last_customer is not None and last_customer in customer_ids:
        st.session_state["cuentas_customer_mode"] = "Elegir una cuenta"
        st.session_state["cuentas_charge_customer"] = last_customer
        st.session_state["cuentas_charge_quantity"] = 1
    balances_tab, charge_tab, payment_tab, people_tab = st.tabs(["Cuentas por cobrar", "Agregar productos", "Registrar pago", "Personas"])

    with balances_tab:
        if not customers:
            st.info("Todavía no hay cuentas. Agregá una persona y sus productos desde «Agregar productos».")
        else:
            totals = [{"Persona": labels[c["id"]], "Importe entregado": float(c["charged"]), "Pagado": float(c["paid"]), "Saldo pendiente": float(c["outstanding"])} for c in summary["by_customer"].values()]
            st.dataframe(pd.DataFrame(totals), hide_index=True, width="stretch", column_config={name: _amount_column(name) for name in ("Importe entregado", "Pagado", "Saldo pendiente")})
            detail_customer = st.selectbox("Ver la cuenta de", customer_ids, format_func=labels.get, key="cuentas_detail_customer")
            lines = [c for c in current.values() if c["cliente_id"] == detail_customer]
            has_products = bool(lines)
            if st.checkbox("Solo productos con saldo pendiente", value=True, key="cuentas_only_pending"):
                lines = [c for c in lines if c["outstanding"] > ZERO]
            if not lines:
                st.info("Esta cuenta está al día: no tiene productos pendientes de pago." if has_products else "Esta cuenta todavía no tiene productos.")
            else:
                st.subheader("Productos de la cuenta")
                line_rows = [{"Fecha": _date(c["fecha"]), "Producto": c["producto"], "Presentación": c["presentacion"], "Cantidad": c["cantidad"], "Importe": float(c["total"]), "Pagado": float(c["paid"]), "Pendiente": float(c["outstanding"])} for c in sorted(lines, key=lambda c: (_date(c["fecha"]), c["id"]))]
                st.dataframe(pd.DataFrame(line_rows), hide_index=True, width="stretch", column_config={"Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"), **{n: _amount_column(n) for n in ("Importe", "Pagado", "Pendiente")}})
            with st.expander("Ver pagos recibidos"):
                payments = [p for p in data["pagos"] if p["cliente_id"] == detail_customer]
                if payments:
                    rows = []
                    for payment in sorted(payments, key=lambda p: (_date(p["fecha"]), p["id"]), reverse=True):
                        applications = [a for a in data["aplicaciones"] if a["pago_id"] == payment["id"]]
                        product_text = "; ".join(f"{current[a['cargo_id']]['producto']} ({money_formatter(a['monto'])})" for a in applications if a["cargo_id"] in current)
                        rows.append({"Fecha": _date(payment["fecha"]), "Pago": float(decimal_amount(payment["monto"])), "Aplicado a": product_text, "Nota": payment.get("nota") or ""})
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={"Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"), "Pago": _amount_column("Pago")})
                else:
                    st.caption("Todavía no se registraron pagos para esta cuenta.")

    with charge_tab:
        st.subheader("Agregar productos a una cuenta")
        st.caption("Cargá aquí los productos pendientes de pago. No los registres también como una venta cobrada.")
        mode = st.radio("Persona", ["Elegir una cuenta", "Crear una cuenta"] if customers else ["Crear una cuenta"], horizontal=True, key="cuentas_customer_mode")
        chosen_customer = None
        new_name = ""
        if mode == "Elegir una cuenta":
            chosen_customer = st.selectbox("Cuenta", customer_ids, format_func=labels.get, key="cuentas_charge_customer")
        else:
            new_name = st.text_input("Nombre de la persona", max_chars=160, key="cuentas_new_customer_name")
            if customers:
                st.caption("Si ya tiene una cuenta, elegila para reunir sus productos y pagos en el mismo lugar.")
        if not recetas:
            st.info("Primero cargá un producto y su receta para poder agregarlo a una cuenta.")
        else:
            first, second = st.columns(2)
            with first:
                charge_date = st.date_input("Fecha de entrega", value=today, max_value=today, format="DD/MM/YYYY", key="cuentas_charge_date")
                product = st.selectbox("Producto entregado", sorted(recetas), key="cuentas_charge_product")
                presentations = list((recetas[product].get("precios") or {}).keys())
            with second:
                if not presentations:
                    st.warning("Este producto no tiene presentaciones ni precios cargados.")
                else:
                    presentation = st.selectbox("Presentación entregada", presentations, key="cuentas_charge_presentation")
                    quantity = st.number_input("Cantidad entregada", min_value=1, max_value=1000000, value=1, step=1, key="cuentas_charge_quantity")
            if presentations:
                suggested = decimal_amount(recetas[product]["precios"].get(presentation) or 0)
                unit_price = st.number_input("Precio por presentación ($)", min_value=0.0, max_value=999999999999.99, value=float(max(suggested, ZERO)), step=100.0, format="%.2f", key=f"cuentas_charge_price_{product}_{presentation}")
                cost, missing = calculate_cost(product, presentation, quantity)
                total = decimal_amount(unit_price) * int(quantity)
                st.metric("Se agrega a la cuenta", money_formatter(total))
                if missing:
                    st.error("Corregí los insumos faltantes antes de agregar este producto: " + ", ".join(str(m) for m in missing))
                payload = {"cliente_id": chosen_customer, "nombre": new_name.strip(), "fecha": charge_date, "producto": product, "presentacion": presentation, "cantidad": quantity, "precio_unitario": str(decimal_amount(unit_price)), "costo_total": str(decimal_amount(cost))}
                charge_request = _request_token("charge", payload)
                customer_request = _request_token("customer", {"nombre": new_name.strip()})
                if st.button("Agregar a la cuenta", type="primary", width="stretch", disabled=bool(missing), key="cuentas_save_charge"):
                    try:
                        if total <= ZERO:
                            raise AccountsValidationError("Ingresá un precio mayor a cero para el producto pendiente.")
                        customer_id = chosen_customer
                        if mode == "Crear una cuenta":
                            customer_id = create_customer(client, new_name, customer_request)["id"]
                        submitted_charge = dict(cliente_id=customer_id, fecha=charge_date.isoformat(), producto=product, presentacion=presentation, cantidad=quantity, precio_unitario=str(decimal_amount(unit_price)), costo_total=str(decimal_amount(cost)), request_id=charge_request)
                        create_charge(client, **submitted_charge)
                        _complete("charge", customer_id)
                        st.rerun()
                    except AccountsValidationError as error:
                        st.error(str(error))
                    except Exception as error:
                        if _definite_rejection(error) or "submitted_charge" not in locals():
                            st.error("No pudimos agregar el producto. Revisá la cuenta, el precio y los datos antes de volver a intentar.")
                        else:
                            st.session_state["_cuentas_pending_charge"] = submitted_charge
                            st.rerun()

    with payment_tab:
        st.subheader("Registrar un pago")
        owing_ids = [i for i in customer_ids if summary["by_customer"][i]["outstanding"] > ZERO]
        if st.session_state.get("_cuentas_payment_complete"):
            st.info("El último pago ya está registrado. Revisá el saldo en «Cuentas por cobrar».")
            if st.button("Registrar otro pago", key="cuentas_another_payment"):
                st.session_state.pop("_cuentas_payment_complete", None)
                st.session_state["cuentas_payment_note"] = ""
                st.rerun()
        elif not owing_ids:
            st.info("No hay saldos pendientes para cobrar.")
        else:
            payment_customer = st.selectbox("Persona que pagó", owing_ids, format_func=labels.get, key="cuentas_payment_customer")
            payment_date = st.date_input("Fecha del pago", value=today, max_value=today, format="DD/MM/YYYY", key="cuentas_payment_date")
            eligible = [c for c in current.values() if c["cliente_id"] == payment_customer and c["outstanding"] > ZERO and _date(c["fecha"]) <= payment_date]
            payment_mode = st.radio("Cómo querés aplicar el pago", ["Un importe a cuenta", "Productos concretos"], key="cuentas_payment_mode", horizontal=True)
            selected_ids = None
            if payment_mode == "Productos concretos":
                options = [c["id"] for c in sorted(eligible, key=lambda c: (_date(c["fecha"]), c["id"]))]
                option_labels = {c["id"]: f"{_date(c['fecha']):%d/%m/%Y} · {c['producto']} · {c['cantidad']} × {c['presentacion']} · {money_formatter(c['outstanding'])} pendiente · #{c['id']}" for c in eligible}
                selected_ids = st.multiselect("Qué productos pagó", options, format_func=option_labels.get, key=f"cuentas_selected_charges_{payment_customer}_{payment_date}")
                balance = sum((current[i]["outstanding"] for i in selected_ids), ZERO)
            else:
                balance = sum((c["outstanding"] for c in eligible), ZERO)
                st.caption("El pago se aplica primero a los productos más antiguos con saldo pendiente.")
            if balance <= ZERO:
                st.info("Elegí productos con saldo pendiente y una fecha de pago igual o posterior a su entrega.")
            else:
                st.caption(f"Saldo que podés cubrir con este pago: {money_formatter(balance)}")
                input_scope = hashlib.sha256(json.dumps([payment_customer, str(payment_date), selected_ids, str(balance)]).encode()).hexdigest()[:16]
                max_payment = min(balance, MAX_AMOUNT)
                paid_amount = st.number_input("Cuánto pagó ($)", min_value=0.0, max_value=float(max_payment), value=float(max_payment), step=100.0, format="%.2f", key="cuentas_payment_amount_" + input_scope)
                note = st.text_input("Nota del pago (opcional)", max_chars=500, key="cuentas_payment_note")
                request_payload = {"cliente_id": payment_customer, "fecha": payment_date, "monto": str(decimal_amount(paid_amount)), "nota": note, "cargo_ids": selected_ids}
                payment_request = _request_token("payment", request_payload)
                if st.button("Registrar pago recibido", type="primary", width="stretch", key="cuentas_save_payment"):
                    try:
                        if decimal_amount(paid_amount) > balance:
                            raise AccountsValidationError("El pago no puede superar el saldo seleccionado.")
                        submitted_payment = dict(cliente_id=payment_customer, fecha=payment_date.isoformat(), monto=str(decimal_amount(paid_amount)), nota=note, request_id=payment_request, cargo_ids=selected_ids)
                        register_payment(client, **submitted_payment)
                        _complete("payment", payment_customer)
                        st.rerun()
                    except AccountsValidationError as error:
                        st.error(str(error))
                    except Exception as error:
                        if _definite_rejection(error):
                            st.error("El saldo o los datos cambiaron. Revisá la cuenta antes de volver a registrar el pago.")
                        else:
                            st.session_state["_cuentas_pending_payment"] = submitted_payment
                            st.rerun()

    with people_tab:
        st.subheader("Agregar una persona")
        if st.session_state.get("_cuentas_person_complete"):
            st.info("La persona ya tiene su cuenta. Podés agregarle productos desde «Agregar productos».")
            if st.button("Agregar otra persona", key="cuentas_another_person"):
                st.session_state.pop("_cuentas_person_complete", None)
                st.session_state["cuentas_person_create_name"] = ""
                _clear_request("person")
                st.rerun()
        else:
            with st.form("cuentas_person_create_form"):
                person_name = st.text_input("Nombre de la nueva persona", max_chars=160, key="cuentas_person_create_name")
                person_request = _request_token("person", {"nombre": person_name.strip()})
                create_person = st.form_submit_button("Crear persona", type="primary", width="stretch")
            if create_person:
                submitted_person = {"nombre": person_name, "request_id": person_request}
                try:
                    person = create_customer(client, **submitted_person)
                    _complete("person", person["id"])
                    st.rerun()
                except AccountsValidationError as error:
                    st.error(str(error))
                except Exception as error:
                    if _definite_rejection(error):
                        st.error("No pudimos crear la persona. Revisá el nombre antes de volver a intentar.")
                    else:
                        st.session_state["_cuentas_pending_person"] = submitted_person
                        st.rerun()
        st.divider()
        st.subheader("Editar el nombre de una persona")
        if not customers:
            st.caption("Primero creá una persona para poder editar su nombre.")
        else:
            edit_id = st.selectbox("Persona a editar", customer_ids, format_func=labels.get, key="cuentas_person_edit_customer")
            previous_name = next(c["nombre"] for c in customers if c["id"] == edit_id)
            name_key = hashlib.sha256(str(previous_name).encode()).hexdigest()[:10]
            edited_name = st.text_input("Nuevo nombre", value=previous_name, max_chars=160, key=f"cuentas_person_rename_name_{edit_id}_{name_key}")
            st.caption("Los productos y pagos seguirán vinculados a la misma cuenta.")
            if st.button("Guardar nombre", type="primary", key="cuentas_person_save_name"):
                submitted_rename = {"cliente_id": edit_id, "nombre": edited_name, "nombre_anterior": previous_name}
                try:
                    rename_customer(client, **submitted_rename)
                    _complete("rename", edit_id)
                    st.rerun()
                except AccountsValidationError as error:
                    st.error(str(error))
                except Exception as error:
                    if _definite_rejection(error):
                        st.error("El nombre pudo cambiar mientras lo editabas. Recargá la cuenta y revisá el nombre actual antes de volver a guardar.")
                    else:
                        st.session_state["_cuentas_pending_rename"] = submitted_rename
                        st.rerun()
