"""Pure period grouping for the sales evolution charts."""
import pandas as pd


def aggregate_evolution(sales, cadence="Semanal"):
    """Group only the selected rows; weeks run Monday through Sunday.

    The caller filters the requested date range before grouping. A week at either
    edge can therefore contain only part of that week; no values are extrapolated.
    """
    if cadence not in {"Diaria", "Semanal", "Mensual"}:
        raise ValueError("Cadencia desconocida")
    dates = pd.to_datetime(sales["fecha"], errors="coerce")
    if cadence == "Semanal":
        periods = dates.dt.to_period("W-SUN").dt.start_time
    elif cadence == "Mensual":
        periods = dates.dt.to_period("M").dt.start_time
    else:
        periods = dates.dt.normalize()
    grouped = (
        sales.assign(Periodo=periods)
        .dropna(subset=["Periodo"])
        .groupby("Periodo", sort=True)
        .agg(
            Facturación=("monto_total", "sum"),
            Costo=("costo_total", "sum"),
            Margen=("ganancia_limpia", "sum"),
        )
        .reset_index()
    )
    if cadence == "Semanal":
        grouped["Etiqueta"] = grouped["Periodo"].dt.strftime("%d/%m/%Y") + " al " + (grouped["Periodo"] + pd.Timedelta(days=6)).dt.strftime("%d/%m/%Y")
    elif cadence == "Mensual":
        grouped["Etiqueta"] = grouped["Periodo"].dt.strftime("%m/%Y")
    else:
        grouped["Etiqueta"] = grouped["Periodo"].dt.strftime("%d/%m/%Y")
    return grouped
