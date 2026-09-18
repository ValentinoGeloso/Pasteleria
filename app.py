import streamlit as st
import pandas as pd
import unicodedata
import plotly.express as px
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from supabase import create_client

# ============================================================
# DULCE MAR - SISTEMA INTEGRAL
# Versión mejorada:
# - Conserva las tablas existentes: insumos, productos y ventas.
# - Agrega gastos_operativos y mermas.
# - Las ventas históricas guardan su costo al momento de vender.
# - Packaging sigue siendo un costo directo de la receta.
# - "Ganancia limpia" de la base existente se interpreta como
#   margen bruto/directo para no romper datos históricos.
# ============================================================

st.set_page_config(
    page_title="Dulce Mar - Sistema Integral",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DATOS ORIGINALES - NO MODIFICAR
# ============================================================

INSUMOS_DEFAULT = {
    "Harina Leudante (kg)": 1700.0, "Manteca (kg)": 19500.0, "Azúcar (kg)": 1400.0,
    "Dulce de Leche (kg)": 7000.0, "Huevo (unidad)": 150.0, "Aceite (litro)": 4000.0,
    "Leche (litro)": 2290.0, "Toddy cacao polvo (kg)": 12600.0, "Azucar impalpable (kg)": 4000.0,
    "Maicena (kg)": 4100.0, "Crema de Leche (litro)": 3800.0, "Caja (unidad)": 2000.0,
    "Frutos rojos (kg)": 16000.0, "Bandeja torta (unidad)": 800.0, "Naranja (kg)": 2000.0,
    "Limon (kg)": 1500.0, "Queso crema (kg)": 12000.0, "Esencia de vainilla (litro)": 22600.0,
    "Coco rallado (kg)": 43400.0, "Bolsa (unidad)": 32.0, "Bandeja (unidad)": 40.0, 
    "Vaso Chico (unidad)": 72.0, "Vaso Grande (unidad)": 100.0, "Cafe molido (kg)": 18550.0,
    "Preparado para Chipa (kg)": 14975.0, "Banana (kg)": 3500.0, "Galletitas vainilla (kg)": 12000.0
}

RECETAS_DEFAULT = {
    "Alfajores de maicena": {
        "rinde": 30, "tipo": "unidades",
        "precios": {"1 Unidad": 1250.0, "Media Docena (6u)": 7500.0, "Docena (12u)": 15000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.200, "Manteca (kg)": 0.100, "Azúcar impalpable (kg)": 0.100, "Maicena (kg)": 0.300, "Dulce de Leche (kg)": 0.250, "Huevo (unidad)": 2, "Esencia de vainilla (litro)": 0.005, "Coco rallado (kg)": 0.010, "Bolsa (unidad)": 30}
    },
    "Budin de chocolate/marmolado": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1000.0, "Entero": 12000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.300, "Toddy cacao polvo (kg)": 0.050, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.100, "Huevo (unidad)": 2, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de vainilla": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1000.0, "Entero": 12000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.300, "Esencia de vainilla (litro)": 0.005, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.100, "Huevo (unidad)": 2, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de limón": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1000.0, "Entero": 12000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.260, "Limon (kg)": 0.150, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.120, "Huevo (unidad)": 3, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de Naranja": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1000.0, "Entero": 12000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.260, "Naranja (kg)": 0.130, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.120, "Huevo (unidad)": 3, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de banana": {
        "rinde": 9, "tipo": "porciones",
        "precios": {"Porción": 1000.0, "Entero": 9000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.150, "Banana (kg)": 0.200, "Azúcar (kg)": 0.180, "Aceite (litro)": 0.060, "Huevo (unidad)": 2, "Esencia de vainilla (litro)": 0.005, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Lemonies": {
        "rinde": 4, "tipo": "porciones",
        "precios": {"Porción": 4000.0, "Entero": 15000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.140, "Limon (kg)": 0.150, "Azúcar (kg)": 0.155, "Manteca (kg)": 0.100, "Huevo (unidad)": 3, "Azucar impalpable (kg)": 0.100, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Chessecake": {
        "rinde": 1, "tipo": "entero",
        "precios": {"Entero": 45000.0},
        "ingredientes": {"Frutos rojos (kg)": 0.500, "Manteca (kg)": 0.080, "Azúcar (kg)": 0.200, "Queso crema (kg)": 0.340, "Galletitas vainilla (kg)": 0.300, "Naranja (kg)": 0.130, "Crema de Leche (litro)": 0.110, "Huevo (unidad)": 3, "Bandeja (unidad)": 1, "Caja (unidad)": 1}
    },
    "Chipa": {
        "rinde": 30, "tipo": "unidades",
        "precios": {"Media Docena (6u)": 5000.0, "Docena (12u)": 10000.0},
        "ingredientes": {"Huevo (unidad)": 3, "Preparado para Chipa (kg)": 0.400}
    },
    "Cafe chico": {
        "rinde": 1, "tipo": "entero",
        "precios": {"Entero": 2000.0},
        "ingredientes": {"Cafe molido (kg)": 0.006,"Leche (litro)": 0.090, "Azúcar (kg)": 0.050, "Vaso Chico (unidad)": 1}
    },
    "Cafe grande": {
        "rinde": 1, "tipo": "entero",
        "precios": {"Entero": 3000.0},
        "ingredientes": {"Cafe molido (kg)": 0.008,"Leche (litro)": 0.120, "Azúcar (kg)": 0.050, "Vaso Grande (unidad)": 1}
    }
}

# ============================================================
# CONFIGURACIÓN
# ============================================================

try:
    TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")
except Exception:
    TZ_AR = None

def hoy_argentina():
    if TZ_AR:
        return datetime.now(TZ_AR).date()
    return datetime.now().date()

# ============================================================
# SUPABASE
# ============================================================

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
    conexion_ok = True
except Exception:
    supabase = None
    conexion_ok = False

if not conexion_ok:
    st.error(
        "No se pudo conectar con Supabase. "
        "Revisá SUPABASE_URL y SUPABASE_KEY en los Secrets de Streamlit."
    )
    st.stop()

# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>
    h1, h2, h3 {
        color: #72b3c2 !important;
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 42px;
    }

    .card-resumen {
        background: linear-gradient(135deg, #1e2d38, #18242d);
        border-radius: 14px;
        padding: 18px;
        border: 1px solid #3a5366;
        margin: 5px 0 15px 0;
    }

    .card-title {
        font-size: 13px;
        color: #93c5fd;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .4px;
        margin-bottom: 5px;
    }

    .card-value {
        font-size: 25px;
        font-weight: 750;
    }

    .venta-item {
        background-color: #1a232a;
        padding: 13px 16px;
        border-radius: 9px;
        border-left: 4px solid #72b3c2;
        margin-bottom: 9px;
        color: #e0f2fe;
    }

    .small-muted {
        color: #94a3b8;
        font-size: 13px;
    }

    .positive {
        color: #4ade80;
    }

    .negative {
        color: #f87171;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS GENERALES
# ============================================================

def dinero(valor):
    try:
        return f"${float(valor):,.2f}"
    except Exception:
        return "$0.00"

def numero(valor, default=0.0):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default

def limpiar_texto(valor):
    return str(valor).strip()

def clave_insumo(valor):
    """Normaliza nombres para comparar insumos sin depender de tildes,
    mayúsculas/minúsculas o espacios sobrantes.

    Ejemplo: "Azúcar impalpable (kg)" y "Azucar impalpable (kg)"
    se consideran el mismo insumo a efectos del cálculo.
    """
    texto = limpiar_texto(valor).lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())

def buscar_insumo(nombre_receta):
    """Devuelve (nombre_real, precio) buscando de forma robusta.

    Primero intenta coincidencia exacta y luego coincidencia normalizada
    para tolerar diferencias como Azúcar/Azucar.
    """
    if nombre_receta in st.session_state.INSUMOS:
        return nombre_receta, numero(st.session_state.INSUMOS[nombre_receta], 0.0)

    clave = clave_insumo(nombre_receta)
    for nombre_real, precio in st.session_state.INSUMOS.items():
        if clave_insumo(nombre_real) == clave:
            return nombre_real, numero(precio, 0.0)

    return None, None

def refrescar_datos():
    st.session_state.pop("INSUMOS", None)
    st.session_state.pop("RECETAS", None)
    st.rerun()

def safe_float_series(df, columna):
    if columna not in df.columns:
        df[columna] = 0.0
    df[columna] = pd.to_numeric(df[columna], errors="coerce").fillna(0.0)
    return df

# ============================================================
# CARGA DE DATOS
# ============================================================

def obtener_insumos():
    try:
        res = supabase.table("insumos").select("*").execute()

        if not res.data:
            datos = [
                {"nombre": nombre, "precio": float(precio)}
                for nombre, precio in INSUMOS_DEFAULT.items()
            ]
            supabase.table("insumos").insert(datos).execute()
            return dict(INSUMOS_DEFAULT)

        resultado = {}
        for item in res.data:
            nombre = item.get("nombre")
            if nombre:
                resultado[nombre] = numero(item.get("precio"), 0.0)
        return resultado

    except Exception as e:
        st.error(f"Error al cargar insumos: {e}")
        return dict(INSUMOS_DEFAULT)


def obtener_recetas():
    try:
        res = supabase.table("productos").select("*").execute()

        if not res.data:
            datos = []
            for nombre, receta in RECETAS_DEFAULT.items():
                datos.append({
                    "nombre": nombre,
                    "rinde": int(receta["rinde"]),
                    "tipo": receta["tipo"],
                    "precios": receta["precios"],
                    "ingredientes": receta["ingredientes"],
                })
            supabase.table("productos").insert(datos).execute()
            return dict(RECETAS_DEFAULT)

        resultado = {}
        for item in res.data:
            nombre = item.get("nombre")
            if not nombre:
                continue

            precios = item.get("precios") or {}
            ingredientes = item.get("ingredientes") or {}

            resultado[nombre] = {
                "rinde": int(item.get("rinde") or 0),
                "tipo": item.get("tipo") or "unidades",
                "precios": precios,
                "ingredientes": ingredientes,
            }

        return resultado

    except Exception as e:
        st.error(f"Error al cargar productos: {e}")
        return dict(RECETAS_DEFAULT)


if "INSUMOS" not in st.session_state:
    st.session_state.INSUMOS = obtener_insumos()

if "RECETAS" not in st.session_state:
    st.session_state.RECETAS = obtener_recetas()

# ============================================================
# CÁLCULOS DE COSTOS
# ============================================================

def calcular_costo_receta(nombre_receta):
    if nombre_receta not in st.session_state.RECETAS:
        return 0.0, 0.0, ["Producto inexistente"]

    receta = st.session_state.RECETAS[nombre_receta]
    rinde = numero(receta.get("rinde"), 0)

    if rinde <= 0:
        return 0.0, 0.0, ["El rendimiento de la receta debe ser mayor a 0"]

    costo_lote = 0.0
    faltantes = []

    for ing, cant in (receta.get("ingredientes") or {}).items():
        cantidad = numero(cant, 0.0)

        nombre_real, precio = buscar_insumo(ing)

        if nombre_real is None:
            faltantes.append(ing)
            continue

        costo_lote += cantidad * precio

    costo_unitario = costo_lote / rinde
    return costo_lote, costo_unitario, faltantes


def multiplicador_presentacion(presentacion, receta):
    """
    Devuelve cuántas unidades/porciones del rendimiento representa
    una presentación.

    Ejemplos:
    - 1 Unidad / Porción -> 1
    - Media Docena -> 6
    - Docena -> 12
    - Entero -> rendimiento completo
    """
    texto = str(presentacion).lower()

    if "docena (12u)" in texto:
        return 12

    if "media docena (6u)" in texto:
        return 6

    if "porción" in texto or "porcion" in texto or "1 unidad" in texto:
        return 1

    return int(numero(receta.get("rinde"), 1))


def calcular_costo_presentacion(nombre_receta, presentacion, cantidad=1):
    receta = st.session_state.RECETAS[nombre_receta]
    costo_lote, costo_unitario, faltantes = calcular_costo_receta(nombre_receta)

    if faltantes:
        return 0.0, faltantes

    multiplicador = multiplicador_presentacion(presentacion, receta)
    costo = costo_unitario * multiplicador * cantidad
    return costo, []


def calcular_margen(precio, costo):
    precio = numero(precio)
    costo = numero(costo)
    margen_pesos = precio - costo
    margen_pct = (margen_pesos / precio * 100) if precio > 0 else 0.0
    return margen_pesos, margen_pct

# ============================================================
# MODAL
# ============================================================

@st.dialog("✅ Producto guardado")
def modal_producto_guardado(nombre):
    st.success(f"**{nombre}** fue guardado correctamente.")
    st.write("Ya está disponible para ventas y cálculos.")
    if st.button("Entendido", use_container_width=True):
        st.rerun()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧁 Dulce Mar")
st.sidebar.caption("Sistema de gestión")

if st.sidebar.button("🔄 Recargar datos", use_container_width=True):
    refrescar_datos()

opcion_menu = st.sidebar.radio(
    "Navegación:",
    [
        "📊 Cargar Venta Diaria",
        "📈 Dashboard",
        "🏷️ Productos y Recetas",
        "🛒 Insumos y Costos",
        "🧾 Gastos Operativos",
        "🗑️ Mermas",
        "⚙️ Calculadora de Costos",
    ],
)

# ============================================================
# 1. CARGAR VENTA
# ============================================================

if opcion_menu == "📊 Cargar Venta Diaria":

    st.header("🛒 Registrar nueva venta")
    st.caption(
        "El costo se guarda en el momento de la venta. "
        "Si mañana cambia el precio de un insumo, las ventas anteriores no cambian."
    )

    if not st.session_state.RECETAS:
        st.warning("No hay productos cargados.")
        st.stop()

    productos = list(st.session_state.RECETAS.keys())

    col1, col2 = st.columns(2)

    with col1:
        fecha_venta = st.date_input("Fecha", value=hoy_argentina())
        prod_sel = st.selectbox("Producto", productos)
        datos_prod = st.session_state.RECETAS[prod_sel]

    with col2:
        presentaciones = list((datos_prod.get("precios") or {}).keys())

        if not presentaciones:
            st.error("Este producto no tiene presentaciones/precios.")
            st.stop()

        tipo_presentacion = st.selectbox("Presentación", presentaciones)
        cantidad = st.number_input(
            "Cantidad vendida",
            min_value=1,
            value=1,
            step=1,
        )

    # ---------------- PROMO CAFÉ + BUDÍN ----------------
    cant_budin_promo = 0
    budin_sel_promo = None
    precio_extra_budin = 0.0

    if "Cafe" in prod_sel:
        st.markdown("---")
        agregar_promo = st.checkbox(
            "☕ Agregar porción de Budín promocional a $750"
        )

        if agregar_promo:
            budines_disponibles = [
                p for p in productos
                if "Budin" in p or "Budín" in p
            ]

            if budines_disponibles:
                colb1, colb2 = st.columns(2)

                with colb1:
                    budin_sel_promo = st.selectbox(
                        "Gusto del budín",
                        budines_disponibles,
                    )

                with colb2:
                    cant_budin_promo = st.number_input(
                        "Porciones de budín",
                        min_value=1,
                        value=1,
                        step=1,
                    )

                precio_extra_budin = cant_budin_promo * 750.0

    precio_base = numero(
        datos_prod["precios"].get(tipo_presentacion), 0.0
    ) * cantidad

    precio_total_sugerido = precio_base + precio_extra_budin

    precio_cobrado = st.number_input(
        "Precio total cobrado ($)",
        min_value=0.0,
        value=float(precio_total_sugerido),
        step=100.0,
    )

    # ---------------- COSTO ----------------
    costo_total_venta, faltantes = calcular_costo_presentacion(
        prod_sel,
        tipo_presentacion,
        cantidad,
    )

    if faltantes:
        st.error(
            "No se puede calcular el costo correctamente porque faltan "
            f"estos insumos: {', '.join(faltantes)}"
        )
        costo_total_venta = 0.0

    if cant_budin_promo > 0 and budin_sel_promo:
        _, costo_u_budin, faltantes_budin = calcular_costo_receta(
            budin_sel_promo
        )

        if faltantes_budin:
            st.error(
                "La promo tiene insumos faltantes: "
                + ", ".join(faltantes_budin)
            )
        else:
            costo_total_venta += costo_u_budin * cant_budin_promo

    margen_bruto = precio_cobrado - costo_total_venta
    margen_pct = (
        margen_bruto / precio_cobrado * 100
        if precio_cobrado > 0
        else 0
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("💵 Venta", dinero(precio_cobrado))
    m2.metric("📦 Costo directo", dinero(costo_total_venta))
    m3.metric("📈 Margen bruto", dinero(margen_bruto))

    st.caption(
        f"Margen sobre venta: **{margen_pct:.1f}%**. "
        "Esto todavía no descuenta gas, electricidad u otros gastos generales."
    )

    if st.button(
        "💾 Guardar venta en la nube",
        type="primary",
        use_container_width=True,
    ):
        try:
            if faltantes:
                st.error("Corregí los insumos faltantes antes de guardar.")
                st.stop()

            presentacion_final = tipo_presentacion

            if cant_budin_promo > 0 and budin_sel_promo:
                gusto_corto = (
                    budin_sel_promo
                    .replace("Budin de ", "")
                    .replace("Budín de ", "")
                    .replace("Budin ", "")
                    .replace("Budín ", "")
                )
                presentacion_final += (
                    f" + {cant_budin_promo}x Budín "
                    f"{gusto_corto} (Promo $750)"
                )

            # Se mantiene "ganancia_limpia" por compatibilidad con la
            # tabla existente. Desde esta versión representa margen bruto.
            registro = {
                "fecha": str(fecha_venta),
                "producto": prod_sel,
                "cantidad": int(cantidad),
                "tipo_venta": presentacion_final,
                "monto_total": float(precio_cobrado),
                "costo_total": float(costo_total_venta),
                "ganancia_limpia": float(margen_bruto),
            }

            supabase.table("ventas").insert(registro).execute()

            st.success(
                f"Venta guardada. Margen bruto: {dinero(margen_bruto)}"
            )
            st.rerun()

        except Exception as err:
            st.error(f"No se pudo guardar la venta: {err}")

    # ---------------- HISTORIAL ----------------
    st.markdown("---")
    st.subheader("📋 Historial de ventas")

    try:
        respuesta = (
            supabase.table("ventas")
            .select("*")
            .order("fecha", desc=True)
            .execute()
        )
        datos_ventas = respuesta.data or []
    except Exception as err:
        st.error(f"No se pudo cargar el historial: {err}")
        datos_ventas = []

    if not datos_ventas:
        st.info("Todavía no hay ventas registradas.")
    else:
        df_ventas = pd.DataFrame(datos_ventas)
        df_ventas["fecha"] = pd.to_datetime(
            df_ventas["fecha"], errors="coerce"
        )

        for _, row in df_ventas.iterrows():
            fecha_txt = (
                row["fecha"].strftime("%d/%m/%Y")
                if pd.notna(row["fecha"])
                else "-"
            )

            with st.container():
                col_info, col_btn = st.columns([5, 1])

                with col_info:
                    st.markdown(
                        f"""
                        <div class="venta-item">
                            📅 <b>{fecha_txt}</b> |
                            <b>{row.get('producto', '-')}</b>
                            ({row.get('tipo_venta', '-')}) x
                            {row.get('cantidad', 0)}
                            <br>
                            💵 Venta:
                            <b>{dinero(row.get('monto_total', 0))}</b>
                            &nbsp;|&nbsp;
                            📦 Costo:
                            <b>{dinero(row.get('costo_total', 0))}</b>
                            &nbsp;|&nbsp;
                            📈 Margen:
                            <b>{dinero(row.get('ganancia_limpia', 0))}</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_btn:
                    if st.button(
                        "🗑️ Borrar",
                        key=f"del_venta_{row.get('id')}",
                    ):
                        try:
                            supabase.table("ventas").delete().eq(
                                "id", row.get("id")
                            ).execute()
                            st.success("Venta eliminada.")
                            st.rerun()
                        except Exception as err:
                            st.error(f"No se pudo eliminar: {err}")

# ============================================================
# 2. DASHBOARD
# ============================================================

elif opcion_menu == "📈 Dashboard":

    st.header("📈 Dashboard del negocio")
    st.caption(
        "El resultado operativo usa solamente los gastos y mermas "
        "que hayan sido registrados en el sistema."
    )

    try:
        ventas_data = (
            supabase.table("ventas")
            .select("*")
            .order("fecha")
            .execute()
            .data
            or []
        )
    except Exception as err:
        st.error(f"No se pudieron cargar las ventas: {err}")
        ventas_data = []

    if ventas_data:
        df = pd.DataFrame(ventas_data)

        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"])

        for col in ["cantidad", "monto_total", "costo_total", "ganancia_limpia"]:
            df = safe_float_series(df, col)

        # Unidades equivalentes para que 1 docena no cuente igual que 1 unidad.
        def unidades_equivalentes(row):
            pres = str(row.get("tipo_venta", "")).lower()
            cant = numero(row.get("cantidad"), 0)

            if "docena (12u)" in pres:
                return cant * 12
            if "media docena (6u)" in pres:
                return cant * 6
            return cant

        df["unidades_equivalentes"] = df.apply(
            unidades_equivalentes, axis=1
        )

        min_fecha = df["fecha"].min().date()
        max_fecha = df["fecha"].max().date()

        colf1, colf2 = st.columns(2)
        with colf1:
            desde = st.date_input(
                "Desde",
                value=min_fecha,
                min_value=min_fecha,
                max_value=max_fecha,
            )
        with colf2:
            hasta = st.date_input(
                "Hasta",
                value=max_fecha,
                min_value=min_fecha,
                max_value=max_fecha,
            )

        if desde > hasta:
            st.error("La fecha inicial no puede ser posterior a la final.")
            st.stop()

        df_periodo = df[
            (df["fecha"].dt.date >= desde)
            & (df["fecha"].dt.date <= hasta)
        ].copy()

        # Gastos operativos
        try:
            gastos_data = (
                supabase.table("gastos_operativos")
                .select("*")
                .execute()
                .data
                or []
            )
        except Exception:
            gastos_data = []

        if gastos_data:
            dg = pd.DataFrame(gastos_data)
            dg["fecha"] = pd.to_datetime(dg["fecha"], errors="coerce")
            dg = dg.dropna(subset=["fecha"])
            dg = safe_float_series(dg, "monto")

            dg_periodo = dg[
                (dg["fecha"].dt.date >= desde)
                & (dg["fecha"].dt.date <= hasta)
            ].copy()

            gastos_periodo = dg_periodo["monto"].sum()
        else:
            dg_periodo = pd.DataFrame()
            gastos_periodo = 0.0

        # Mermas
        try:
            mermas_data = (
                supabase.table("mermas")
                .select("*")
                .execute()
                .data
                or []
            )
        except Exception:
            mermas_data = []

        if mermas_data:
            dm = pd.DataFrame(mermas_data)
            dm["fecha"] = pd.to_datetime(dm["fecha"], errors="coerce")
            dm = dm.dropna(subset=["fecha"])
            dm = safe_float_series(dm, "costo_total")

            dm_periodo = dm[
                (dm["fecha"].dt.date >= desde)
                & (dm["fecha"].dt.date <= hasta)
            ].copy()

            mermas_periodo = dm_periodo["costo_total"].sum()
        else:
            dm_periodo = pd.DataFrame()
            mermas_periodo = 0.0

        facturacion = df_periodo["monto_total"].sum()
        costo_directo = df_periodo["costo_total"].sum()
        margen_bruto_total = df_periodo["ganancia_limpia"].sum()

        resultado_operativo = (
            margen_bruto_total
            - gastos_periodo
            - mermas_periodo
        )

        margen_bruto_pct = (
            margen_bruto_total / facturacion * 100
            if facturacion > 0
            else 0
        )

        resultado_pct = (
            resultado_operativo / facturacion * 100
            if facturacion > 0
            else 0
        )

        promedio_ticket = (
            facturacion / len(df_periodo)
            if len(df_periodo) > 0
            else 0
        )

        # ---------------- KPIs ----------------
        k1, k2, k3 = st.columns(3)
        k1.metric("💵 Facturación", dinero(facturacion))
        k2.metric("📦 Costo directo", dinero(costo_directo))
        k3.metric("📈 Margen bruto", dinero(margen_bruto_total))

        k4, k5, k6 = st.columns(3)
        k4.metric("🧾 Gastos operativos", dinero(gastos_periodo))
        k5.metric("🗑️ Mermas", dinero(mermas_periodo))
        k6.metric("🏦 Resultado operativo", dinero(resultado_operativo))

        st.info(
            f"Margen bruto: **{margen_bruto_pct:.1f}%** | "
            f"Resultado operativo sobre ventas: **{resultado_pct:.1f}%** | "
            f"Promedio por venta: **{dinero(promedio_ticket)}** | "
            f"Ventas: **{len(df_periodo)}** | "
            f"Unidades equivalentes: **{df_periodo['unidades_equivalentes'].sum():.0f}**"
        )

        # ---------------- TENDENCIA DIARIA ----------------
        st.markdown("---")
        st.subheader("📅 Evolución diaria")

        diario = (
            df_periodo.assign(Día=df_periodo["fecha"].dt.date)
            .groupby("Día")
            .agg(
                Facturación=("monto_total", "sum"),
                Costo=("costo_total", "sum"),
                Margen=("ganancia_limpia", "sum"),
            )
            .reset_index()
        )

        if not diario.empty:
            fig = px.bar(
                diario,
                x="Día",
                y=["Facturación", "Margen"],
                barmode="group",
                title="Facturación y margen bruto por día",
            )
            st.plotly_chart(fig, use_container_width=True)

        # ---------------- MENSUAL ----------------
        st.subheader("🗓️ Evolución mensual")

        mensual = (
            df_periodo.assign(
                Mes=df_periodo["fecha"].dt.to_period("M").astype(str)
            )
            .groupby("Mes")
            .agg(
                Facturación=("monto_total", "sum"),
                Costo=("costo_total", "sum"),
                Margen=("ganancia_limpia", "sum"),
            )
            .reset_index()
        )

        if not mensual.empty:
            fig_m = px.bar(
                mensual,
                x="Mes",
                y=["Facturación", "Margen"],
                barmode="group",
                title="Facturación y margen bruto por mes",
            )
            st.plotly_chart(fig_m, use_container_width=True)

        # ---------------- PRODUCTOS ----------------
        st.markdown("---")
        st.subheader("🏆 Análisis por producto")

        por_producto = (
            df_periodo.groupby("producto")
            .agg(
                Ventas=("monto_total", "sum"),
                Costo=("costo_total", "sum"),
                Margen=("ganancia_limpia", "sum"),
                Operaciones=("producto", "count"),
                Unidades=("unidades_equivalentes", "sum"),
            )
            .reset_index()
        )

        por_producto["Margen %"] = (
            por_producto["Margen"]
            / por_producto["Ventas"]
            .replace(0, pd.NA)
            * 100
        ).fillna(0)

        por_producto = por_producto.sort_values(
            "Margen",
            ascending=False,
        )

        colp1, colp2 = st.columns(2)

        with colp1:
            figp = px.bar(
                por_producto.sort_values("Margen", ascending=True),
                x="Margen",
                y="producto",
                orientation="h",
                title="Margen bruto total por producto",
            )
            st.plotly_chart(figp, use_container_width=True)

        with colp2:
            figm = px.bar(
                por_producto.sort_values("Margen %", ascending=True),
                x="Margen %",
                y="producto",
                orientation="h",
                title="Margen porcentual por producto",
            )
            st.plotly_chart(figm, use_container_width=True)

        st.dataframe(
            por_producto.style.format({
                "Ventas": "${:,.2f}",
                "Costo": "${:,.2f}",
                "Margen": "${:,.2f}",
                "Margen %": "{:.1f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # ---------------- EXPORTAR ----------------
        st.markdown("---")
        st.subheader("📥 Exportar datos del período")

        csv = df_periodo.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "⬇️ Descargar ventas en CSV",
            data=csv,
            file_name=f"dulce_mar_ventas_{desde}_{hasta}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.info("Todavía no hay ventas registradas.")

# ============================================================
# 3. PRODUCTOS Y RECETAS
# ============================================================

elif opcion_menu == "🏷️ Productos y Recetas":

    st.header("🏷️ Productos y recetas")

    tab1, tab2, tab3, tab4 = st.tabs([
        "✏️ Precios",
        "➕ Crear producto",
        "🗑️ Eliminar producto",
        "📊 Rentabilidad",
    ])

    # ---------------- PRECIOS ----------------
    with tab1:

        if not st.session_state.RECETAS:
            st.info("No hay productos.")
        else:
            productos = list(st.session_state.RECETAS.keys())

            col1, col2 = st.columns([2, 1])

            with col1:
                prod_mod = st.selectbox(
                    "Producto",
                    productos,
                    key="prod_mod_precio",
                )

                pres_dict = st.session_state.RECETAS[
                    prod_mod
                ].get("precios", {})

                if not pres_dict:
                    st.warning("Este producto no tiene presentaciones.")
                else:
                    pres_mod = st.selectbox(
                        "Presentación",
                        list(pres_dict.keys()),
                        key="pres_mod_precio",
                    )

                    precio_actual = numero(
                        pres_dict[pres_mod]
                    )

                    nuevo_precio = st.number_input(
                        "Nuevo precio ($)",
                        min_value=0.0,
                        value=precio_actual,
                        step=100.0,
                    )

                    if st.button(
                        "💾 Guardar nuevo precio",
                        type="primary",
                    ):
                        try:
                            nuevos_precios = dict(pres_dict)
                            nuevos_precios[pres_mod] = float(
                                nuevo_precio
                            )

                            supabase.table("productos").update({
                                "precios": nuevos_precios
                            }).eq("nombre", prod_mod).execute()

                            st.session_state.RECETAS[
                                prod_mod
                            ]["precios"] = nuevos_precios

                            st.success("Precio actualizado.")
                            st.rerun()

                        except Exception as err:
                            st.error(
                                f"No se pudo actualizar: {err}"
                            )

            with col2:
                st.subheader("📋 Precios actuales")

                filas = []

                for nombre, data in st.session_state.RECETAS.items():
                    for pres, precio in (
                        data.get("precios", {}).items()
                    ):
                        costo, faltantes = calcular_costo_presentacion(
                            nombre, pres, 1
                        )
                        margen, margen_pct = calcular_margen(
                            precio,
                            costo,
                        )

                        filas.append({
                            "Producto": nombre,
                            "Presentación": pres,
                            "Precio": dinero(precio),
                            "Costo directo": dinero(costo),
                            "Margen": dinero(margen),
                            "Margen %": f"{margen_pct:.1f}%",
                        })

                st.dataframe(
                    pd.DataFrame(filas),
                    use_container_width=True,
                    height=500,
                    hide_index=True,
                )

    # ---------------- CREAR ----------------
    with tab2:

        st.subheader("➕ Agregar producto nuevo")

        col1, col2 = st.columns(2)

        with col1:
            nuevo_nombre_prod = st.text_input(
                "Nombre del producto",
                key="nuevo_producto_nombre",
            )

            rinde_prod = st.number_input(
                "Rendimiento de la receta",
                min_value=1,
                value=8,
                step=1,
            )

            tipo_rinde = st.selectbox(
                "Unidad del rendimiento",
                ["porciones", "unidades", "entero"],
            )

        with col2:
            st.markdown("**Precios de venta ($)**")

            p_entero = st.number_input(
                "Precio Entero / Tanda",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

            p_individual = st.number_input(
                "Precio Porción / Unidad",
                min_value=0.0,
                value=0.0,
                step=50.0,
            )

            p_media = st.number_input(
                "Precio Media Docena (6u)",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

            p_docena = st.number_input(
                "Precio Docena (12u)",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

        st.markdown("---")
        st.subheader("🥣 Ingredientes")

        insumos_disponibles = list(
            st.session_state.INSUMOS.keys()
        )

        ingredientes_seleccionados = st.multiselect(
            "Seleccioná los insumos",
            insumos_disponibles,
        )

        dict_ingredientes_nuevo = {}

        if ingredientes_seleccionados:
            cols = st.columns(2)

            for idx, ing in enumerate(
                ingredientes_seleccionados
            ):
                col = cols[idx % 2]

                if "(unidad)" in ing.lower():
                    cant = col.number_input(
                        f"Cantidad de {ing}",
                        min_value=1,
                        value=1,
                        step=1,
                        key=f"nuevo_ing_{idx}_{ing}",
                    )
                else:
                    cant = col.number_input(
                        f"Cantidad de {ing}",
                        min_value=0.001,
                        value=0.100,
                        step=0.010,
                        format="%.3f",
                        key=f"nuevo_ing_{idx}_{ing}",
                    )

                dict_ingredientes_nuevo[ing] = float(cant)

        if st.button(
            "✨ Guardar producto completo",
            type="primary",
            use_container_width=True,
        ):
            nombre_limpio = limpiar_texto(nuevo_nombre_prod)

            if not nombre_limpio:
                st.warning("Escribí un nombre.")
                st.stop()

            if nombre_limpio in st.session_state.RECETAS:
                st.warning(
                    "Ya existe un producto con ese nombre."
                )
                st.stop()

            if not dict_ingredientes_nuevo:
                st.warning(
                    "Elegí al menos un ingrediente."
                )
                st.stop()

            precios = {}

            if p_entero > 0:
                precios["Entero"] = float(p_entero)

            if p_individual > 0:
                etiqueta = (
                    "1 Unidad"
                    if tipo_rinde == "unidades"
                    else "Porción"
                )
                precios[etiqueta] = float(p_individual)

            if p_media > 0:
                precios["Media Docena (6u)"] = float(p_media)

            if p_docena > 0:
                precios["Docena (12u)"] = float(p_docena)

            if not precios:
                st.warning(
                    "Ingresá al menos un precio mayor a $0."
                )
                st.stop()

            registro = {
                "nombre": nombre_limpio,
                "rinde": int(rinde_prod),
                "tipo": tipo_rinde,
                "precios": precios,
                "ingredientes": dict_ingredientes_nuevo,
            }

            try:
                supabase.table("productos").insert(
                    registro
                ).execute()

                st.session_state.RECETAS[
                    nombre_limpio
                ] = {
                    "rinde": int(rinde_prod),
                    "tipo": tipo_rinde,
                    "precios": precios,
                    "ingredientes": dict_ingredientes_nuevo,
                }

                modal_producto_guardado(nombre_limpio)

            except Exception as err:
                st.error(
                    f"No se pudo guardar el producto: {err}"
                )

    # ---------------- ELIMINAR ----------------
    with tab3:

        if not st.session_state.RECETAS:
            st.info("No hay productos.")
        else:
            prod_eliminar = st.selectbox(
                "Producto a eliminar",
                list(st.session_state.RECETAS.keys()),
                key="producto_eliminar",
            )

            st.warning(
                "Eliminar el producto NO elimina las ventas históricas. "
                "Las ventas guardadas conservan sus datos."
            )

            confirmar = st.checkbox(
                "Confirmo que quiero eliminar este producto."
            )

            if st.button(
                "🗑️ Eliminar producto",
                disabled=not confirmar,
            ):
                try:
                    supabase.table("productos").delete().eq(
                        "nombre",
                        prod_eliminar,
                    ).execute()

                    del st.session_state.RECETAS[
                        prod_eliminar
                    ]

                    st.success("Producto eliminado.")
                    st.rerun()

                except Exception as err:
                    st.error(
                        f"No se pudo eliminar: {err}"
                    )

    # ---------------- RENTABILIDAD ----------------
    with tab4:

        if not st.session_state.RECETAS:
            st.info("No hay productos.")
        else:
            filas = []

            for nombre, receta in st.session_state.RECETAS.items():
                for pres, precio in (
                    receta.get("precios", {}).items()
                ):
                    costo, faltantes = (
                        calcular_costo_presentacion(
                            nombre,
                            pres,
                            1,
                        )
                    )

                    margen, margen_pct = calcular_margen(
                        precio,
                        costo,
                    )

                    filas.append({
                        "Producto": nombre,
                        "Presentación": pres,
                        "Precio venta": precio,
                        "Costo directo": costo,
                        "Margen bruto": margen,
                        "Margen %": margen_pct,
                        "Insumos faltantes": (
                            ", ".join(faltantes)
                            if faltantes else ""
                        ),
                    })

            df_r = pd.DataFrame(filas)

            st.dataframe(
                df_r.style.format({
                    "Precio venta": "${:,.2f}",
                    "Costo directo": "${:,.2f}",
                    "Margen bruto": "${:,.2f}",
                    "Margen %": "{:.1f}%",
                }),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Margen % = (precio - costo directo) / precio. "
                "No es lo mismo que markup."
            )

# ============================================================
# 4. INSUMOS
# ============================================================

elif opcion_menu == "🛒 Insumos y Costos":

    st.header("🛒 Insumos y materias primas")
    st.caption(
        "Packaging como bolsas, cajas, vasos y bandejas puede "
        "seguir dentro de esta tabla y dentro del costo directo."
    )

    tab1, tab2 = st.tabs([
        "✏️ Editar",
        "➕ Agregar",
    ])

    with tab1:

        if not st.session_state.INSUMOS:
            st.info("No hay insumos.")
        else:

            insumos = list(
                st.session_state.INSUMOS.keys()
            )

            insumo_editar = st.selectbox(
                "Insumo",
                insumos,
                key="insumo_editar",
            )

            precio_actual = numero(
                st.session_state.INSUMOS[
                    insumo_editar
                ]
            )

            nuevo_precio = st.number_input(
                "Nuevo costo ($)",
                min_value=0.0,
                value=precio_actual,
                step=50.0,
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "🔄 Actualizar costo",
                    type="primary",
                ):
                    try:
                        supabase.table("insumos").update({
                            "precio": float(nuevo_precio)
                        }).eq(
                            "nombre",
                            insumo_editar,
                        ).execute()

                        st.session_state.INSUMOS[
                            insumo_editar
                        ] = float(nuevo_precio)

                        st.success(
                            "Costo actualizado."
                        )
                        st.rerun()

                    except Exception as err:
                        st.error(
                            f"No se pudo actualizar: {err}"
                        )

            with col2:
                confirmar_eliminar = st.checkbox(
                    "Confirmar eliminación"
                )

                if st.button(
                    "🗑️ Eliminar insumo",
                    disabled=not confirmar_eliminar,
                ):
                    # Evitamos borrar accidentalmente un insumo que
                    # alguna receta todavía necesita.
                    recetas_que_lo_usan = []

                    for nombre, receta in (
                        st.session_state.RECETAS.items()
                    ):
                        if insumo_editar in (
                            receta.get("ingredientes", {})
                        ):
                            recetas_que_lo_usan.append(nombre)

                    if recetas_que_lo_usan:
                        st.error(
                            "No se puede eliminar porque lo usan "
                            "estas recetas: "
                            + ", ".join(recetas_que_lo_usan)
                        )
                    else:
                        try:
                            supabase.table(
                                "insumos"
                            ).delete().eq(
                                "nombre",
                                insumo_editar,
                            ).execute()

                            del st.session_state.INSUMOS[
                                insumo_editar
                            ]

                            st.success(
                                "Insumo eliminado."
                            )
                            st.rerun()

                        except Exception as err:
                            st.error(
                                f"No se pudo eliminar: {err}"
                            )

        st.markdown("---")
        st.subheader("📋 Lista actual")

        filas = [
            {
                "Insumo": nombre,
                "Costo": precio,
            }
            for nombre, precio
            in st.session_state.INSUMOS.items()
        ]

        df_ins = pd.DataFrame(filas)

        if not df_ins.empty:
            df_ins = df_ins.sort_values("Insumo")

        st.dataframe(
            df_ins.style.format({
                "Costo": "${:,.2f}",
            }),
            use_container_width=True,
            height=500,
            hide_index=True,
        )

    with tab2:

        nuevo_nombre = st.text_input(
            "Nombre del nuevo insumo"
        )

        nuevo_precio = st.number_input(
            "Costo ($)",
            min_value=0.0,
            value=0.0,
            step=50.0,
        )

        if st.button(
            "➕ Crear insumo",
            type="primary",
        ):
            nombre = limpiar_texto(nuevo_nombre)

            if not nombre:
                st.warning("Escribí un nombre.")
                st.stop()

            if nombre in st.session_state.INSUMOS:
                st.warning("Ese insumo ya existe.")
                st.stop()

            try:
                supabase.table("insumos").insert({
                    "nombre": nombre,
                    "precio": float(nuevo_precio),
                }).execute()

                st.session_state.INSUMOS[
                    nombre
                ] = float(nuevo_precio)

                st.success("Insumo creado.")
                st.rerun()

            except Exception as err:
                st.error(
                    f"No se pudo crear: {err}"
                )

# ============================================================
# 5. GASTOS OPERATIVOS
# ============================================================

elif opcion_menu == "🧾 Gastos Operativos":

    st.header("🧾 Gastos operativos")
    st.caption(
        "Acá van costos generales como gas, electricidad, internet, "
        "alquiler, impuestos u otros. No se meten dentro de la receta "
        "porque no es razonable asignarlos arbitrariamente a cada producto."
    )

    tab1, tab2 = st.tabs([
        "➕ Registrar gasto",
        "📋 Historial",
    ])

    with tab1:

        fecha_gasto = st.date_input(
            "Fecha del gasto",
            value=hoy_argentina(),
        )

        categoria = st.selectbox(
            "Categoría",
            [
                "Gas",
                "Electricidad",
                "Agua",
                "Internet",
                "Alquiler",
                "Impuestos",
                "Comisiones",
                "Delivery",
                "Mantenimiento",
                "Otros",
            ],
        )

        descripcion = st.text_input(
            "Descripción",
            placeholder="Ej: factura de gas septiembre",
        )

        monto = st.number_input(
            "Monto ($)",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )

        if st.button(
            "💾 Registrar gasto",
            type="primary",
            use_container_width=True,
        ):

            if monto <= 0:
                st.warning(
                    "El gasto debe ser mayor a $0."
                )
                st.stop()

            try:
                supabase.table(
                    "gastos_operativos"
                ).insert({
                    "fecha": str(fecha_gasto),
                    "categoria": categoria,
                    "descripcion": descripcion.strip(),
                    "monto": float(monto),
                }).execute()

                st.success(
                    f"Gasto registrado: {dinero(monto)}"
                )
                st.rerun()

            except Exception as err:
                st.error(
                    "No se pudo registrar el gasto. "
                    "¿Ejecutaste la tabla gastos_operativos en Supabase?\n\n"
                    f"Detalle: {err}"
                )

    with tab2:

        try:
            gastos = (
                supabase.table(
                    "gastos_operativos"
                )
                .select("*")
                .order("fecha", desc=True)
                .execute()
                .data
                or []
            )
        except Exception as err:
            gastos = []
            st.warning(
                "No se pudo leer gastos_operativos. "
                "Ejecutá el SQL de instalación primero."
            )

        if not gastos:
            st.info("No hay gastos registrados.")
        else:
            dg = pd.DataFrame(gastos)
            dg["fecha"] = pd.to_datetime(
                dg["fecha"],
                errors="coerce",
            )
            dg = safe_float_series(dg, "monto")

            st.dataframe(
                dg[[
                    "id",
                    "fecha",
                    "categoria",
                    "descripcion",
                    "monto",
                ]].style.format({
                    "monto": "${:,.2f}",
                }),
                use_container_width=True,
                hide_index=True,
            )

            total = dg["monto"].sum()
            st.metric(
                "Total de gastos registrados",
                dinero(total),
            )

            st.markdown("---")
            st.subheader("Eliminar gasto")

            ids = dg["id"].tolist()

            if ids:
                gasto_id = st.selectbox(
                    "ID del gasto",
                    ids,
                )

                if st.button(
                    "🗑️ Eliminar gasto seleccionado"
                ):
                    try:
                        supabase.table(
                            "gastos_operativos"
                        ).delete().eq(
                            "id",
                            gasto_id,
                        ).execute()

                        st.success(
                            "Gasto eliminado."
                        )
                        st.rerun()

                    except Exception as err:
                        st.error(
                            f"No se pudo eliminar: {err}"
                        )

# ============================================================
# 6. MERMAS
# ============================================================

elif opcion_menu == "🗑️ Mermas":

    st.header("🗑️ Registro de mermas")
    st.caption(
        "No inventamos una merma porcentual si normalmente es $0. "
        "Se registra únicamente lo que realmente se perdió/desperdició."
    )

    tab1, tab2 = st.tabs([
        "➕ Registrar merma",
        "📋 Historial",
    ])

    with tab1:

        if not st.session_state.INSUMOS:
            st.warning(
                "No hay insumos cargados."
            )
        else:

            fecha_merma = st.date_input(
                "Fecha",
                value=hoy_argentina(),
            )

            insumo_merma = st.selectbox(
                "Insumo desperdiciado",
                list(st.session_state.INSUMOS.keys()),
            )

            cantidad_merma = st.number_input(
                "Cantidad perdida",
                min_value=0.001,
                value=0.100,
                step=0.010,
                format="%.3f",
            )

            motivo = st.text_input(
                "Motivo",
                placeholder="Ej: se cayó, se quemó, venció...",
            )

            precio_actual = numero(
                st.session_state.INSUMOS[
                    insumo_merma
                ]
            )

            costo_merma = (
                cantidad_merma * precio_actual
            )

            st.metric(
                "Costo estimado de la merma",
                dinero(costo_merma),
            )

            if st.button(
                "💾 Registrar merma",
                type="primary",
                use_container_width=True,
            ):

                if cantidad_merma <= 0:
                    st.warning(
                        "La cantidad debe ser mayor a 0."
                    )
                    st.stop()

                try:
                    supabase.table(
                        "mermas"
                    ).insert({
                        "fecha": str(fecha_merma),
                        "insumo": insumo_merma,
                        "cantidad": float(cantidad_merma),
                        "costo_unitario": float(precio_actual),
                        "costo_total": float(costo_merma),
                        "motivo": motivo.strip(),
                    }).execute()

                    st.success(
                        f"Merma registrada: {dinero(costo_merma)}"
                    )
                    st.rerun()

                except Exception as err:
                    st.error(
                        "No se pudo registrar la merma. "
                        "¿Ejecutaste la tabla mermas en Supabase?\n\n"
                        f"Detalle: {err}"
                    )

    with tab2:

        try:
            mermas = (
                supabase.table(
                    "mermas"
                )
                .select("*")
                .order("fecha", desc=True)
                .execute()
                .data
                or []
            )
        except Exception:
            mermas = []

        if not mermas:
            st.info("No hay mermas registradas.")
        else:
            dm = pd.DataFrame(mermas)
            dm["fecha"] = pd.to_datetime(
                dm["fecha"],
                errors="coerce",
            )
            dm = safe_float_series(
                dm,
                "cantidad",
            )
            dm = safe_float_series(
                dm,
                "costo_unitario",
            )
            dm = safe_float_series(
                dm,
                "costo_total",
            )

            st.dataframe(
                dm[[
                    "id",
                    "fecha",
                    "insumo",
                    "cantidad",
                    "costo_unitario",
                    "costo_total",
                    "motivo",
                ]].style.format({
                    "cantidad": "{:.3f}",
                    "costo_unitario": "${:,.2f}",
                    "costo_total": "${:,.2f}",
                }),
                use_container_width=True,
                hide_index=True,
            )

            st.metric(
                "Costo total histórico de mermas",
                dinero(dm["costo_total"].sum()),
            )

            st.markdown("---")
            st.subheader("Eliminar merma")

            merma_id = st.selectbox(
                "ID de la merma",
                dm["id"].tolist(),
            )

            if st.button(
                "🗑️ Eliminar merma seleccionada"
            ):
                try:
                    supabase.table(
                        "mermas"
                    ).delete().eq(
                        "id",
                        merma_id,
                    ).execute()

                    st.success(
                        "Merma eliminada."
                    )
                    st.rerun()

                except Exception as err:
                    st.error(
                        f"No se pudo eliminar: {err}"
                    )

# ============================================================
# 7. CALCULADORA
# ============================================================

elif opcion_menu == "⚙️ Calculadora de Costos":

    st.header("⚙️ Calculadora de costos y márgenes")
    st.caption(
        "Packaging incluido como costo directo cuando forma parte de la receta."
    )

    if not st.session_state.RECETAS:
        st.info("No hay productos.")
        st.stop()

    receta_seleccionada = st.selectbox(
        "Producto",
        list(st.session_state.RECETAS.keys()),
    )

    receta = st.session_state.RECETAS[
        receta_seleccionada
    ]

    costo_lote, costo_unitario, faltantes = (
        calcular_costo_receta(
            receta_seleccionada
        )
    )

    if faltantes:
        st.error(
            "Faltan estos insumos: "
            + ", ".join(faltantes)
        )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Costo del lote",
        dinero(costo_lote),
    )

    c2.metric(
        "Rendimiento",
        f"{receta.get('rinde', 0)} {receta.get('tipo', '')}",
    )

    c3.metric(
        "Costo por unidad/porción",
        dinero(costo_unitario),
    )

    st.markdown("---")
    st.subheader("💵 Rentabilidad por presentación")

    filas = []

    for pres, precio in (
        receta.get("precios", {}).items()
    ):

        costo, faltantes_pres = (
            calcular_costo_presentacion(
                receta_seleccionada,
                pres,
                1,
            )
        )

        margen, margen_pct = calcular_margen(
            precio,
            costo,
        )

        filas.append({
            "Presentación": pres,
            "Precio venta": precio,
            "Costo directo": costo,
            "Margen bruto": margen,
            "Margen %": margen_pct,
        })

    df_margen = pd.DataFrame(filas)

    st.dataframe(
        df_margen.style.format({
            "Precio venta": "${:,.2f}",
            "Costo directo": "${:,.2f}",
            "Margen bruto": "${:,.2f}",
            "Margen %": "{:.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("🎯 Precio orientativo según margen objetivo")

    margen_objetivo = st.slider(
        "Margen bruto objetivo",
        min_value=10,
        max_value=90,
        value=60,
        step=5,
    )

    if margen_objetivo < 100:
        filas_sugerencia = []

        for pres, precio in (
            receta.get("precios", {}).items()
        ):
            costo, _ = calcular_costo_presentacion(
                receta_seleccionada,
                pres,
                1,
            )

            precio_sugerido = (
                costo / (1 - margen_objetivo / 100)
                if costo > 0
                else 0
            )

            filas_sugerencia.append({
                "Presentación": pres,
                "Costo": costo,
                "Precio actual": numero(precio),
                "Precio con margen objetivo": precio_sugerido,
            })

        st.dataframe(
            pd.DataFrame(
                filas_sugerencia
            ).style.format({
                "Costo": "${:,.2f}",
                "Precio actual": "${:,.2f}",
                "Precio con margen objetivo": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.subheader("🥣 Desglose de insumos")

    desglose = []

    for ing, cant in (
        receta.get("ingredientes", {}).items()
    ):

        precio_ing = (
            st.session_state.INSUMOS.get(
                ing,
                None,
            )
        )

        if precio_ing is None:
            costo_ing = 0
            precio_mostrar = "FALTANTE"
        else:
            precio_ing = numero(precio_ing)
            costo_ing = (
                numero(cant) * precio_ing
            )
            precio_mostrar = dinero(
                precio_ing
            )

        if "(unidad)" in ing.lower():
            cantidad_mostrar = f"{numero(cant):.0f}"
        else:
            cantidad_mostrar = f"{numero(cant):.3f}"

        desglose.append({
            "Insumo": ing,
            "Cantidad": cantidad_mostrar,
            "Precio actual": precio_mostrar,
            "Costo en receta": costo_ing,
        })

    df_desglose = pd.DataFrame(desglose)

    st.dataframe(
        df_desglose.style.format({
            "Costo en receta": "${:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# FIN
# ============================================================
