"""Separate sales, cash receipts and receivables without double counting."""
from datetime import date
from decimal import Decimal, InvalidOperation


ZERO = Decimal("0.00")


def money_value(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Importe inválido para el resumen financiero") from error
    if not amount.is_finite():
        raise ValueError("Importe no finito para el resumen financiero")
    return amount


def reporting_sales(paid_sales, account_data):
    """One reporting row per sale/credit charge; payments are never sales rows."""
    result = []
    for sale in paid_sales:
        row = dict(sale)
        row["tipo_registro"] = "Venta cobrada"
        row["referencia"] = f"venta:{sale['id']}"
        result.append(row)
    for charge in account_data["cargos"]:
        total, cost = money_value(charge["monto_total"]), money_value(charge["costo_total"])
        result.append({
            "id": charge["id"], "fecha": charge["fecha"],
            "producto": charge["producto"], "tipo_venta": charge["presentacion"],
            "cantidad": charge["cantidad"], "monto_total": total,
            "costo_total": cost, "ganancia_limpia": total - cost,
            "tipo_registro": "Venta a cuenta", "referencia": f"cuenta:{charge['id']}",
        })
    return result


def cash_overview(paid_sales, account_summary, start, end):
    """Current legacy sales are paid, as explicitly confirmed by the owner."""
    paid = ZERO
    for sale in paid_sales:
        day = date.fromisoformat(str(sale["fecha"])[:10])
        if start <= day <= end:
            paid += money_value(sale["monto_total"])
    credit = money_value(account_summary["period_credit_sales"])
    receipts = money_value(account_summary["period_receipts"])
    outstanding = money_value(account_summary["outstanding_as_of"])
    return {
        "paid_sales": paid,
        "credit_sales": credit,
        "total_sales": paid + credit,
        "collected": paid + receipts,
        "outstanding": outstanding,
        "collected_plus_outstanding": paid + receipts + outstanding,
    }
