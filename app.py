import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import re
import copy
from collections import Counter
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# DATOS FICTICIOS PARA MODO INVITADO
# ============================================================

DEMO_INSUMOS_DEFAULT = {
    "Harina Demo (kg)": 1500.0,
    "Azúcar Demo (kg)": 1000.0,
    "Manteca Demo (kg)": 5000.0,
    "Huevo Demo (unidad)": 250.0,
    "Chocolate Demo (kg)": 6000.0,
    "Naranja Demo (unidad)": 300.0,
}

DEMO_RECETAS_DEFAULT = {
    "Budín Demo": {
        "rinde": 10,
        "tipo": "porciones",
        "precios": {"Porción": 1500.0, "Entero": 11000.0},
        "ingredientes": {
            "Harina Demo (kg)": 0.250,
            "Azúcar Demo (kg)": 0.180,
            "Manteca Demo (kg)": 0.100,
            "Huevo Demo (unidad)": 2,
        },
    }
}

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================

st.set_page_config(
    page_title="Dulce Mar - Sistema Integral",
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ACCESO: MODO PRIVADO / MODO INVITADO
# ============================================================

USUARIOS_AUTORIZADOS = {
    "Valentinofabriciogelosorodio@gmail.com",
    "martinaprestileoortiz@gmail.com",
}

usuarios_autorizados_normalizados = {
    email.lower().strip()
    for email in USUARIOS_AUTORIZADOS
}

if "modo_invitado" not in st.session_state:
    st.session_state.modo_invitado = False


def limpiar_datos_sesion_app():
    """Limpia datos de aplicación al cambiar de modo."""
    for clave in [
        "INSUMOS",
        "RECETAS",
        "_demo_cargado",
        "pagina_historial_ventas",
    ]:
        st.session_state.pop(clave, None)


def entrar_modo_invitado():
    limpiar_datos_sesion_app()
    st.session_state.modo_invitado = True
    st.rerun()


def salir_modo_invitado():
    limpiar_datos_sesion_app()
    st.session_state.modo_invitado = False
    st.rerun()


# El modo invitado tiene prioridad: no requiere autenticación.
if not st.session_state.modo_invitado:
    if not st.user.is_logged_in:
        st.title("🧁 Dulce Mar")
        st.subheader("Sistema de gestión")
        st.write(
            "Iniciá sesión con una cuenta autorizada para acceder "
            "al sistema privado, o probá la demostración."
        )

        col_login, col_demo = st.columns(2)
        with col_login:
            if st.button("🔐 Iniciar sesión con Google", use_container_width=True):
                st.login()
        with col_demo:
            if st.button("👀 Ver demostración", use_container_width=True):
                entrar_modo_invitado()
        st.stop()

    email_usuario = (getattr(st.user, "email", "") or "").lower().strip()

    if email_usuario not in usuarios_autorizados_normalizados:
        st.error("⛔ Esta cuenta no tiene autorización para acceder a Dulce Mar.")
        st.write(f"Cuenta detectada: `{email_usuario}`")

        col_demo, col_logout = st.columns(2)
        with col_demo:
            if st.button("👀 Continuar como invitado", use_container_width=True):
                entrar_modo_invitado()
        with col_logout:
            if st.button("🚪 Cerrar sesión", use_container_width=True):
                st.logout()
        st.stop()

modo_invitado = st.session_state.modo_invitado


# ============================================================   
# DATOS ORIGINALES - NO MODIFICAR
# ============================================================

INSUMOS_DEFAULT = {
    "Harina Leudante (kg)": 1700.0, "Manteca (kg)": 19500.0, "Azúcar (kg)": 1400.0,
    "Dulce de Leche (kg)": 7000.0, "Huevo (unidad)": 150.0, "Aceite (litro)": 4000.0,
    "Leche (litro)": 2290.0, "Toddy cacao polvo (kg)": 12600.0, "Azucar impalpable (kg)": 4000.0,
    "Maicena (kg)": 4100.0, "Crema de Leche (litro)": 3800.0, "Caja (unidad)": 2000.0,
    "Frutos rojos (kg)": 16000.0, "Bandeja torta (unidad)": 800.0, "Naranja (kg)": 2000.0, "Naranja (unidad)": 300.0,
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
# SOLO SE INICIALIZA EN MODO PRIVADO
# ============================================================

supabase = None

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

if not modo_invitado:
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

def familia_producto(nombre):
    """Agrupa visualmente variantes sin cambiar el nombre real guardado."""
    texto = limpiar_texto(nombre)
    normal = clave_normalizada(texto)
    if normal.startswith("budin ") or normal.startswith("budin de "):
        return "Budín"
    if normal.startswith("brownie ") or normal.startswith("brownie de "):
        return "Brownie"
    if re.match(r"^cafe\s+(chico|grande)$", normal):
        return "Café"
    if re.match(r"^te\s+(chico|grande)$", normal):
        return "Té"
    return texto


def gusto_producto(nombre, familia=None):
    texto = limpiar_texto(nombre)
    familia = familia or familia_producto(texto)
    if familia in {"Budín", "Brownie"}:
        patrones = [r"^bud[ií]n\s+de\s+", r"^bud[ií]n\s+", r"^brownie\s+de\s+", r"^brownie\s+"]
        for patron in patrones:
            nuevo = re.sub(patron, "", texto, flags=re.IGNORECASE).strip()
            if nuevo != texto:
                return nuevo
    if familia in {"Café", "Té"}:
        normal = clave_normalizada(texto)
        if normal.endswith(" chico"):
            return "Chico"
        if normal.endswith(" grande"):
            return "Grande"
    return texto


def productos_agrupados(recetas=None):
    recetas = recetas if recetas is not None else st.session_state.RECETAS
    grupos = {}
    for nombre in recetas.keys():
        grupos.setdefault(familia_producto(nombre), []).append(nombre)
    return grupos


def selector_producto_agrupado(label="Producto", key_prefix="producto"):
    """Muestra familia y, cuando corresponde, gusto; devuelve la clave real de la receta."""
    grupos = productos_agrupados()
    familias = list(grupos.keys())
    if not familias:
        return None
    familia_sel = st.selectbox(label, familias, key=f"{key_prefix}_familia")
    variantes = grupos[familia_sel]
    if len(variantes) == 1 and familia_sel == variantes[0]:
        return variantes[0]
    mapa_gustos = {}
    for nombre in variantes:
        etiqueta = gusto_producto(nombre, familia_sel) or nombre
        if etiqueta in mapa_gustos:
            etiqueta = f"{etiqueta} ({nombre})"
        mapa_gustos[etiqueta] = nombre
    gusto_sel = st.selectbox("Gusto / variedad", list(mapa_gustos.keys()), key=f"{key_prefix}_gusto")
    return mapa_gustos[gusto_sel]


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


def clave_normalizada(valor):
    """Normaliza texto para comparar nombres sin depender de tildes/case/espacios."""
    texto = str(valor or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    return " ".join(texto.split())


def buscar_insumo(nombre):
    """Encuentra un insumo aunque haya diferencias de tildes o mayúsculas."""
    if nombre in st.session_state.INSUMOS:
        return nombre

    objetivo = clave_normalizada(nombre)
    for existente in st.session_state.INSUMOS:
        if clave_normalizada(existente) == objetivo:
            return existente

    return None


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
        return {}


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
        return {}


def guardar_receta_en_base(nombre_receta):
    """Guarda los ingredientes actuales de una receta en Supabase."""
    if modo_invitado:
        return

    supabase.table("productos").update({
        "ingredientes": st.session_state.RECETAS[nombre_receta].get("ingredientes", {}),
    }).eq("nombre", nombre_receta).execute()


def guardar_insumo_en_base(nombre, precio):
    """Guarda el precio de un insumo en Supabase. En demo solo modifica sesión."""
    precio = float(precio)

    if modo_invitado:
        st.session_state.INSUMOS[nombre] = precio
        return

    supabase.table("insumos").update({
        "precio": precio,
    }).eq("nombre", nombre).execute()
    st.session_state.INSUMOS[nombre] = precio


def crear_insumo_en_base(nombre, precio):
    """Crea un insumo nuevo en la base real o solamente en la demo."""
    nombre = limpiar_texto(nombre)
    precio = float(precio)

    if modo_invitado:
        st.session_state.INSUMOS[nombre] = precio
        return

    supabase.table("insumos").insert({
        "nombre": nombre,
        "precio": precio,
    }).execute()
    st.session_state.INSUMOS[nombre] = precio


def normalizar_naranjas_por_unidad():
    """Convierte Naranja (kg) a Naranja (unidad), usando 150 g por naranja."""
    nombre_kg = buscar_insumo("Naranja (kg)")
    nombre_unidad = buscar_insumo("Naranja (unidad)")

    if nombre_kg is None:
        return

    precio_kg = numero(st.session_state.INSUMOS.get(nombre_kg), 0.0)
    precio_unidad_calculado = precio_kg * 0.150

    # Creamos el insumo por unidad si todavía no existe. Su precio siempre
    # representa exactamente 150 g de naranja, por lo que se deriva del precio/kg.
    if nombre_unidad is None:
        nombre_unidad = "Naranja (unidad)"
        if modo_invitado:
            st.session_state.INSUMOS[nombre_unidad] = precio_unidad_calculado
        else:
            try:
                supabase.table("insumos").insert({
                    "nombre": nombre_unidad,
                    "precio": precio_unidad_calculado,
                }).execute()
                st.session_state.INSUMOS[nombre_unidad] = precio_unidad_calculado
            except Exception:
                # Si otro proceso la creó al mismo tiempo, volvemos a leerla.
                res = supabase.table("insumos").select("nombre, precio").eq("nombre", nombre_unidad).limit(1).execute()
                if res.data:
                    st.session_state.INSUMOS[nombre_unidad] = numero(res.data[0].get("precio"), precio_unidad_calculado)
                else:
                    return
    else:
        # Si cambió el precio por kg, actualizamos automáticamente el precio por unidad.
        if abs(numero(st.session_state.INSUMOS.get(nombre_unidad), -1) - precio_unidad_calculado) > 0.001:
            st.session_state.INSUMOS[nombre_unidad] = precio_unidad_calculado
            if not modo_invitado:
                try:
                    supabase.table("insumos").update({
                        "precio": precio_unidad_calculado,
                    }).eq("nombre", nombre_unidad).execute()
                except Exception:
                    pass

    # Las recetas que todavía usan kg pasan automáticamente a unidades.
    recetas_modificadas = []
    for nombre_receta, receta in st.session_state.RECETAS.items():
        ingredientes = dict(receta.get("ingredientes") or {})
        clave_kg = None
        clave_unidad = None

        for ing in ingredientes:
            if clave_normalizada(ing) == clave_normalizada("Naranja (kg)"):
                clave_kg = ing
            if clave_normalizada(ing) == clave_normalizada("Naranja (unidad)"):
                clave_unidad = ing

        if clave_kg is None:
            continue

        cantidad_kg = numero(ingredientes.get(clave_kg), 0.0)
        cantidad_unidades = cantidad_kg / 0.150

        if clave_unidad is not None:
            cantidad_unidades += numero(ingredientes.get(clave_unidad), 0.0)
            del ingredientes[clave_unidad]

        del ingredientes[clave_kg]
        ingredientes[nombre_unidad] = round(cantidad_unidades, 4)
        receta["ingredientes"] = ingredientes
        recetas_modificadas.append(nombre_receta)

    if not modo_invitado:
        for nombre_receta in recetas_modificadas:
            try:
                guardar_receta_en_base(nombre_receta)
            except Exception:
                # La receta ya quedó normalizada en memoria; si la escritura falla,
                # no detenemos toda la aplicación. Se mostrará el estado al recargar.
                pass


# ============================================================
# CARGA DE DATOS SEGÚN EL MODO
# ============================================================

if modo_invitado:
    # Demo: solamente memoria de la sesión actual.
    if (
        "INSUMOS" not in st.session_state
        or not st.session_state.get("_demo_cargado", False)
    ):
        st.session_state.INSUMOS = copy.deepcopy(DEMO_INSUMOS_DEFAULT)
        st.session_state.RECETAS = copy.deepcopy(DEMO_RECETAS_DEFAULT)
        st.session_state._demo_cargado = True
else:
    # Privado: datos reales desde Supabase.
    if "INSUMOS" not in st.session_state:
        st.session_state.INSUMOS = obtener_insumos()
    if "RECETAS" not in st.session_state:
        st.session_state.RECETAS = obtener_recetas()

# Las naranjas se manejan siempre por unidad: 1 naranja = 150 g.
normalizar_naranjas_por_unidad()

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
        nombre_real = buscar_insumo(ing)

        if nombre_real is None:
            faltantes.append(ing)
            continue

        costo_lote += cantidad * numero(
            st.session_state.INSUMOS[nombre_real],
            0.0,
        )

    costo_unitario = costo_lote / rinde
    return costo_lote, costo_unitario, faltantes

def presentacion_base(texto):
    """Quita información adicional de una venta, como una promo de budín."""
    return str(texto or "").split(" + ", 1)[0].strip()


def multiplicador_presentacion(presentacion, receta):
    """Devuelve cuántas unidades/porciones representa una presentación."""
    texto = presentacion_base(presentacion).lower()

    if "docena (12u)" in texto or texto == "docena":
        return 12

    if "media docena (6u)" in texto or "media docena" in texto:
        return 6

    if (
        "porción" in texto
        or "porcion" in texto
        or "1 unidad" in texto
        or texto in {"unidad", "1u"}
    ):
        return 1

    # "Entero" y cualquier presentación no tipificada representan
    # el rendimiento completo de la receta.
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
# IMPORTADOR DE VENTAS HISTÓRICAS
# ============================================================

ALIAS_COLUMNAS_VENTAS = {
    "fecha": ["fecha", "dia", "día", "date"],
    "producto": ["producto", "productos", "item", "articulo", "artículo", "detalle", "descripcion", "descripción", "venta"],
    "cantidad": ["cantidad", "cant", "cantidad vendida", "unidades", "uds", "qty"],
    "monto": ["monto", "monto total", "total", "importe", "precio", "precio total", "venta total", "facturacion", "facturación", "cobrado"],
    "presentacion": ["presentacion", "presentación", "formato", "unidad", "tamaño", "tamano"],
    "tipo": ["tipo", "movimiento", "clase"],
}


def detectar_columna(df, tipo):
    """Busca automáticamente una columna habitual del Excel.

    Además del nombre, contempla el formato histórico de Dulce Mar:
    Fecha | Tipo | Categoría | Detalle | Monto.
    """
    if df is None or df.empty:
        return None

    normalizadas = {
        col: clave_normalizada(col).replace("_", " ")
        for col in df.columns
    }

    aliases = ALIAS_COLUMNAS_VENTAS.get(tipo, [])

    # 1) Coincidencia exacta por nombre.
    for alias in aliases:
        alias_n = clave_normalizada(alias)
        for col, col_n in normalizadas.items():
            if col_n == alias_n:
                return col

    # 2) Coincidencia parcial.
    for alias in aliases:
        alias_n = clave_normalizada(alias)
        for col, col_n in normalizadas.items():
            if alias_n in col_n or col_n in alias_n:
                return col

    # 3) Respaldo específico para el Excel de Dulce Mar:
    #    Fecha | Tipo | Categoría | Detalle | Monto
    columnas = list(df.columns)
    if len(columnas) >= 5:
        posiciones = {
            "fecha": 0,
            "monto": 4,
            "producto": 3,
        }
        posicion = posiciones.get(tipo)
        if posicion is not None and posicion < len(columnas):
            return columnas[posicion]

    return None


def encontrar_producto_historico(texto):
    """Relaciona el texto del Excel con un producto existente.
    Si dice solamente Budín/Budin, conserva el gusto como desconocido.
    """
    texto_n = clave_normalizada(texto)
    if not texto_n:
        return None

    productos = list(st.session_state.RECETAS.keys())

    # Primero exactos y luego coincidencias por nombre completo.
    for producto in sorted(productos, key=len, reverse=True):
        if clave_normalizada(producto) == texto_n:
            return producto

    for producto in sorted(productos, key=len, reverse=True):
        producto_n = clave_normalizada(producto)
        if producto_n and producto_n in texto_n:
            return producto

    if "budin" in texto_n or "budines" in texto_n:
        return "__BUDIN_HISTORICO_SIN_GUSTO__"

    return None


def extraer_cantidad_desde_texto(texto):
    """Detecta cantidades simples en textos como '2 budines' o 'x3'."""
    texto = str(texto or "")
    patrones = [
        r"(?:^|\\s)x\\s*(\\d+(?:[.,]\\d+)?)",
        r"(?:^|\s)(\d+(?:[.,]\d+)?)\s*(?:x|unid|unidad|u|budin|budines|porcion|porciones|porc|porción)",
    ]

    import re

    for patron in patrones:
        encontrado = re.search(patron, texto, flags=re.IGNORECASE)
        if encontrado:
            try:
                return float(encontrado.group(1).replace(",", "."))
            except Exception:
                pass

    return None


def detectar_presentacion_historica(texto, producto, monto, cantidad):
    texto_n = clave_normalizada(texto)

    if "media docena" in texto_n:
        return "Media Docena (6u)"
    if "docena" in texto_n:
        return "Docena (12u)"
    if (
        "porcion" in texto_n
        or "porciones" in texto_n
        or "porc" in texto_n
        or "por." in str(texto).lower()
    ):
        return "Porción"
    if "entero" in texto_n or "grande" in texto_n:
        return "Entero"

    # Regla histórica de Dulce Mar: cuando se anotaba "chipa" sin
    # aclarar presentación, se refería a una bolsa de media docena.
    if producto == "Chipa":
        return "Media Docena (6u)"

    if producto == "__BUDIN_HISTORICO_SIN_GUSTO__":
        # Si no se especificó el gusto pero sí se escribió "porc"/"por.",
        # la venta es una porción. Para un "budín" sin presentación,
        # mantenemos la inferencia por precio como respaldo.
        unitario = numero(monto) / max(numero(cantidad, 1), 1)
        return "Porción" if unitario <= 2000 else "Entero"

    if producto in st.session_state.RECETAS:
        precios = st.session_state.RECETAS[producto].get("precios") or {}
        if precios:
            unitario = numero(monto) / max(numero(cantidad, 1), 1)
            for presentacion, precio in precios.items():
                if abs(numero(precio) - unitario) < 1:
                    return presentacion

            if len(precios) == 1:
                return next(iter(precios))

            # Para productos con porciones + entero, una venta cercana al
            # precio de porción suele ser una porción; si no, entero.
            for presentacion, precio in precios.items():
                if "porcion" in clave_normalizada(presentacion) and unitario <= numero(precio) * 1.15:
                    return presentacion

            return "Entero" if "Entero" in precios else next(iter(precios))

    return "Entero"


def costo_historico_generico_budin(presentacion):
    """Promedio de costo actual de los budines cuando el Excel no informa gusto.
    Se usa solo para poder reconstruir el margen histórico sin inventar un gusto.
    """
    costos = []
    for nombre, receta in st.session_state.RECETAS.items():
        if "budin" not in clave_normalizada(nombre):
            continue
        _, costo_u, faltantes = calcular_costo_receta(nombre)
        if faltantes:
            continue
        if "porcion" in clave_normalizada(presentacion):
            costos.append(costo_u)
        else:
            costos.append(costo_u * numero(receta.get("rinde"), 1))

    return sum(costos) / len(costos) if costos else 0.0


def costo_venta_historica(producto, presentacion, cantidad):
    if producto == "__BUDIN_HISTORICO_SIN_GUSTO__":
        return costo_historico_generico_budin(presentacion) * numero(cantidad, 1), True

    if producto not in st.session_state.RECETAS:
        return 0.0, False

    costo, faltantes = calcular_costo_presentacion(
        producto,
        presentacion,
        cantidad,
    )
    return costo, not bool(faltantes)


def _producto_historico_guardado(producto):
    return "Budines (gusto no registrado)" if producto == "__BUDIN_HISTORICO_SIN_GUSTO__" else producto


def _precio_historico_producto(producto, presentacion, cantidad=1):
    # Precio de venta histórico aproximado para repartir el monto de una fila
    # compuesta. Es independiente del costo de receta: acá queremos estimar
    # cuánto se cobró por cada componente, no cuánto costó producirlo.
    if producto == "__BUDIN_HISTORICO_SIN_GUSTO__":
        if "porcion" in clave_normalizada(presentacion):
            precio_unitario = 1000.0
        else:
            # En el historial se observan budines enteros a $12.000 y budín
            # chico a $10.000. Como no siempre se indicó el tamaño, usamos
            # $12.000 como referencia y dejamos que el monto real de la fila
            # corrija la diferencia.
            precio_unitario = 12000.0
        return precio_unitario * numero(cantidad, 1)
    if producto not in st.session_state.RECETAS:
        return 0.0
    receta = st.session_state.RECETAS[producto]
    precios = receta.get("precios") or {}
    if presentacion in precios:
        return numero(precios[presentacion]) * numero(cantidad, 1)
    return 0.0


def _segmento_historico(segmento, monto_segmento=None):
    """Interpreta un componente del detalle del Excel."""
    original = str(segmento or "").strip()
    n = clave_normalizada(original)
    if not n:
        return None

    # Cantidades explícitas de chipa. En este historial "chipa" sin aclaración
    # significa una bolsa de 6 unidades.
    if "chipa" in n:
        if "docena" in n:
            qty, pres = 1, "Docena (12u)"
        elif re.search(r"1\s*/\s*2\s*doc", n) or "media docena" in n:
            qty, pres = 1, "Media Docena (6u)"
        else:
            m = re.search(r"(\d+(?:[.,]\d+)?)\s*bolsas?", n)
            # "chipa 5 unidades" es una excepción: son 5 unidades, no 5 bolsas.
            mu = re.search(r"(\d+(?:[.,]\d+)?)\s*unidades?", n)
            if mu:
                qty, pres = int(float(mu.group(1).replace(",", "."))), "1 Unidad"
            else:
                if not m:
                    m = re.search(r"chipa\s*x?\s*(\d+(?:[.,]\d+)?)", n)
                if not m:
                    m = re.search(r"(\d+(?:[.,]\d+)?)\s*chipa", n)
                if m:
                    qty, pres = int(float(m.group(1).replace(",", "."))), "Media Docena (6u)"
                else:
                    qty, pres = 1, "Media Docena (6u)"
        return {"producto": "Chipa", "cantidad": qty, "presentacion": pres}

    # Una anotación como "porc", "2porc" o "por. budin" siempre significa
    # porciones de budín aunque la palabra "budin" no aparezca en ese segmento.
    if re.search(r"(?:^|\d)\s*porc(?:iones?)?\s*$", n) or n in {"por", "porcion", "porciones"}:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:porc(?:iones?)?|por|porcion|porciones)", n)
        qty = int(float(m.group(1).replace(",", "."))) if m else 1
        return {"producto": "__BUDIN_HISTORICO_SIN_GUSTO__", "cantidad": qty, "presentacion": "Porción"}

    # Budines: gusto no informado = producto histórico genérico.
    if "budin" in n:
        if "porcion" in n or "porciones" in n or "porc" in n or "por." in original.lower():
            m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:porciones?|porc|por\.)", n)
            qty = int(float(m.group(1).replace(",", "."))) if m else 1
            return {"producto": "__BUDIN_HISTORICO_SIN_GUSTO__", "cantidad": qty, "presentacion": "Porción"}
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*budines?", n)
        qty = int(float(m.group(1).replace(",", "."))) if m else 1
        # En el Excel "budin chico" y "budin grande" son enteros; el
        # importe real de la fila se usa luego para conservar el precio cobrado.
        return {"producto": "__BUDIN_HISTORICO_SIN_GUSTO__", "cantidad": qty, "presentacion": "Entero"}

    # Café.
    if "cafe chico" in n:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*cafe\s*chico", n)
        qty = int(float(m.group(1).replace(",", "."))) if m else 1
        return {"producto": "Cafe chico", "cantidad": qty, "presentacion": "Entero"}
    if "cafe grande" in n:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*cafe\s*grande", n)
        qty = int(float(m.group(1).replace(",", "."))) if m else 1
        return {"producto": "Cafe grande", "cantidad": qty, "presentacion": "Entero"}
    if re.search(r"\bcafe\b", n):
        return {"producto": "__CAFE_GENERICO__", "cantidad": 1, "presentacion": "Entero"}

    # Alfajores.
    if "alf" in n or "alfajor" in n:
        if "docena" in n or re.search(r"\bdoc\b", n):
            return {"producto": "Alfajores de maicena", "cantidad": 1, "presentacion": "Docena (12u)", "precio_historico_incierto": True}
        if "media docena" in n:
            return {"producto": "Alfajores de maicena", "cantidad": 1, "presentacion": "Media Docena (6u)", "precio_historico_incierto": True}
        return {"producto": "Alfajores de maicena", "cantidad": 1, "presentacion": "1 Unidad", "precio_historico_incierto": True}

    return None


def _resolver_cafe_generico(componentes, monto_total):
    """Resuelve 'café' usando la combinación cuyo precio coincide con el total."""
    for c in componentes:
        if c["producto"] != "__CAFE_GENERICO__":
            continue
        otros = sum(_precio_historico_producto(x["producto"], x["presentacion"], x["cantidad"])
                    for x in componentes if x is not c)
        restante = numero(monto_total) - otros
        if abs(restante - 2000) <= 1:
            c.update(producto="Cafe chico", precio_asignado=2000.0)
        elif abs(restante - 3000) <= 1:
            c.update(producto="Cafe grande", precio_asignado=3000.0)
        else:
            # Si el precio histórico no coincide exactamente, usamos la opción
            # más cercana y luego conservamos el total de la fila.
            c.update(producto="Cafe grande" if restante >= 2500 else "Cafe chico")


def interpretar_detalle_historico(texto, monto_total):
    """Convierte una fila como 'cafe+chipa' en uno o varios productos."""
    texto = str(texto or "").strip()
    if not texto:
        return []

    partes = [p.strip() for p in re.split(r"\s*\+\s*", texto) if p.strip()]
    componentes = []
    for parte in partes:
        c = _segmento_historico(parte, monto_total)
        if c:
            componentes.append(c)
        else:
            # Casos pegados como "chipa4bolsas" ya son tratados arriba. Si
            # aparece una parte nueva, la devolvemos como no reconocida.
            return [], parte

    if not componentes:
        return [], texto

    _resolver_cafe_generico(componentes, monto_total)

    # Para una fila compuesta, repartir el monto cobrado entre sus componentes.
    # Los productos conocidos conservan primero su precio de referencia; los
    # componentes históricos inciertos (principalmente budín sin gusto) absorben
    # el resto. Así también funcionan descuentos/promos sin rechazar la fila.
    precios = []
    inciertos = []
    for i, c in enumerate(componentes):
        if "precio_asignado" in c:
            base = c["precio_asignado"]
        elif c.get("precio_historico_incierto"):
            base = 0.0
            inciertos.append(i)
        else:
            base = _precio_historico_producto(c["producto"], c["presentacion"], c["cantidad"])
        precios.append(max(numero(base), 0.0))

    if len(componentes) == 1:
        if componentes[0]["producto"] == "__CAFE_GENERICO__":
            return [], texto
        return [(componentes[0], float(monto_total))], None

    total = numero(monto_total)
    resultado = []
    acumulado = 0.0

    # Si hay componentes inciertos, primero cobramos los conocidos y les damos
    # a los inciertos todo el remanente. Es especialmente útil para "cafe+porc"
    # y "budin+chipa".
    indices_conocidos = [i for i in range(len(componentes)) if i not in inciertos]
    suma_conocidos = sum(precios[i] for i in indices_conocidos)

    if inciertos:
        # Si los conocidos ya superan el total, aplicamos el descuento al último
        # conocido para no inventar una venta por encima del monto real.
        if suma_conocidos > total:
            diferencia = suma_conocidos - total
            ultimo = indices_conocidos[-1] if indices_conocidos else None
            for i in indices_conocidos:
                precio = precios[i]
                if i == ultimo:
                    precio = max(0.0, precio - diferencia)
                resultado.append((componentes[i], round(precio, 2)))
                acumulado += precio
            if acumulado > total + 0.01:
                return [], texto
            restante = max(0.0, total - acumulado)
        else:
            for i in indices_conocidos:
                precio = precios[i]
                resultado.append((componentes[i], round(precio, 2)))
                acumulado += precio
            restante = max(0.0, total - acumulado)

        por_incierto = restante / len(inciertos) if inciertos else 0.0
        for j, i in enumerate(inciertos):
            precio = por_incierto
            if j == len(inciertos) - 1:
                precio = total - sum(p for _, p in resultado)
            resultado.append((componentes[i], round(max(0.0, precio), 2)))
        return resultado, None

    # Sin componentes inciertos: usamos los precios de referencia y cualquier
    # diferencia (descuento o recargo) se aplica al último componente.
    if suma_conocidos <= 0:
        return [], texto

    diferencia = round(total - suma_conocidos, 2)
    if diferencia < 0:
        # Descuento: se aplica al último componente sin rechazar la venta.
        i = len(componentes) - 1
        precios[i] = max(0.0, precios[i] + diferencia)
    else:
        precios[-1] += diferencia

    for c, precio in zip(componentes, precios):
        resultado.append((c, round(precio, 2)))
    return resultado, None



def _armar_fila_historica(fecha, detalle, monto, nombre_archivo, nombre_hoja, nro_fila, presentacion_extra=""):
    """Genera las filas de ventas que corresponden a una fila del Excel."""
    interpretadas, no_reconocida = interpretar_detalle_historico(detalle, monto)
    if no_reconocida:
        return [], [
            f"{nombre_archivo} / {nombre_hoja} / fila {nro_fila + 2}: "
            f"no se pudo interpretar '{detalle}' (parte no reconocida: '{no_reconocida}')."
        ]

    filas, avisos = [], []
    for c, precio in interpretadas:
        producto = c["producto"]
        cantidad = int(c["cantidad"])
        presentacion = c["presentacion"]
        if presentacion_extra:
            presentacion = detectar_presentacion_historica(
                f"{detalle} {presentacion_extra}", producto, precio, cantidad
            )

        producto_guardado = _producto_historico_guardado(producto)
        costo, costo_ok = costo_venta_historica(producto, presentacion, cantidad)
        if not costo_ok:
            costo = 0.0
            avisos.append(
                f"{nombre_archivo} / {nombre_hoja} / fila {nro_fila + 2}: "
                f"no se pudo calcular costo para '{producto_guardado}'. Se importará con costo $0."
            )

        filas.append({
            "fecha": fecha.date(),
            "producto": producto_guardado,
            "cantidad": cantidad,
            "tipo_venta": presentacion,
            "monto_total": float(precio),
            "costo_total": float(costo),
            "ganancia_limpia": float(precio - costo),
            "_archivo": nombre_archivo,
            "_hoja": nombre_hoja,
            "_fila": int(nro_fila + 2),
        })
    return filas, avisos


def preparar_ventas_historicas_archivo(archivo):
    """Lee todas las hojas del Excel y convierte cada fila en una o más ventas."""
    nombre_archivo = getattr(archivo, "name", "archivo")
    try:
        # Los .xlsx/.xls necesitan un motor de lectura instalado.
        # Para .xlsx usamos openpyxl explícitamente para que el error sea claro.
        if nombre_archivo.lower().endswith(".xlsx"):
            hojas = pd.read_excel(archivo, sheet_name=None, engine="openpyxl")
        else:
            hojas = pd.read_excel(archivo, sheet_name=None)
    except ImportError as err:
        raise RuntimeError(
            "Falta la dependencia 'openpyxl' para leer archivos Excel (.xlsx). "
            "Instalala con: python -m pip install openpyxl y reiniciá Streamlit."
        ) from err
    filas, advertencias = [], []

    for nombre_hoja, df in hojas.items():
        if df is None or df.empty:
            continue
        df = df.dropna(axis=1, how="all").dropna(axis=0, how="all").copy()
        if df.empty:
            continue

        col_fecha = detectar_columna(df, "fecha")
        col_producto = detectar_columna(df, "producto")
        col_monto = detectar_columna(df, "monto")
        col_presentacion = detectar_columna(df, "presentacion")

        if not col_fecha or not col_producto or not col_monto:
            advertencias.append(
                f"{nombre_archivo} / hoja '{nombre_hoja}': no se pudieron detectar Fecha + Detalle + Monto. "
                f"Columnas encontradas: {', '.join(map(str, df.columns))}"
            )
            continue

        # En el formato histórico de Dulce Mar, solo importamos filas de Ingreso.
        col_tipo = detectar_columna(df, "tipo")
        for nro_fila, fila in df.iterrows():
            if col_tipo:
                tipo_fila = clave_normalizada(fila.get(col_tipo, ""))
                if tipo_fila and tipo_fila not in {"ingreso", "venta", "ventas"}:
                    continue
            fecha = pd.to_datetime(fila.get(col_fecha), errors="coerce", dayfirst=True)
            if pd.isna(fecha):
                # Las filas vacías o de separación no se consideran error; si tienen
                # contenido, sí avisamos para que el usuario pueda revisarlas.
                valores = [str(v).strip() for v in fila.tolist() if str(v).strip() not in {"", "nan", "NaT"}]
                if valores:
                    advertencias.append(
                        f"{nombre_archivo} / hoja '{nombre_hoja}' / fila {nro_fila + 2}: fecha no reconocida."
                    )
                continue
            detalle = str(fila.get(col_producto, "")).strip()
            if not detalle or detalle.lower() == "nan":
                advertencias.append(
                    f"{nombre_archivo} / hoja '{nombre_hoja}' / fila {nro_fila + 2}: falta el Detalle de la venta."
                )
                continue
            monto = numero(fila.get(col_monto), 0.0)
            if monto <= 0:
                advertencias.append(
                    f"{nombre_archivo} / hoja '{nombre_hoja}' / fila {nro_fila + 2}: monto vacío o no válido para '{detalle}'."
                )
                continue

            nuevas, avisos = _armar_fila_historica(
                fecha, detalle, monto, nombre_archivo, nombre_hoja, nro_fila,
                str(fila.get(col_presentacion, "")) if col_presentacion else "",
            )
            filas.extend(nuevas)
            advertencias.extend(avisos)

    return filas, advertencias


def firma_venta_historica(row):
    fecha = pd.to_datetime(row.get("fecha"), errors="coerce")
    fecha_txt = fecha.strftime("%Y-%m-%d") if pd.notna(fecha) else ""
    return "|".join([
        fecha_txt,
        clave_normalizada(row.get("producto", "")),
        str(int(numero(row.get("cantidad"), 0))),
        clave_normalizada(row.get("tipo_venta", "")),
        f"{numero(row.get('monto_total'), 0):.2f}",
    ])

# ============================================================
# ============================================================
# MODAL
# ============================================================

@st.dialog("✅ Producto guardado")
def modal_producto_guardado(nombre):
    st.success(f"**{nombre}** fue guardado correctamente.")
    if modo_invitado:
        st.info(
            "👀 Este producto pertenece únicamente a la demostración "
            "y no se guardó en la base real."
        )
    else:
        st.write("Ya está disponible para ventas y cálculos.")
    if st.button("Entendido", use_container_width=True):
        st.rerun()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧁 Dulce Mar")

if modo_invitado:
    st.sidebar.caption("👀 Modo demostración")
    st.sidebar.info(
        "Datos ficticios. Los cambios se guardan solo en esta sesión "
        "y no modifican la base real."
    )

    if st.sidebar.button("↩️ Restablecer demostración", use_container_width=True):
        limpiar_datos_sesion_app()
        st.session_state.modo_invitado = True
        st.rerun()

    if st.sidebar.button("🔐 Volver al modo privado", use_container_width=True):
        salir_modo_invitado()

    opciones_menu = [
        "🏷️ Productos y Recetas",
        "🛒 Insumos y Costos",
        "⚙️ Calculadora de Costos",
    ]
else:
    st.sidebar.caption("🔒 Sistema privado")

    if st.sidebar.button("🔄 Recargar datos", use_container_width=True):
        refrescar_datos()

    if st.sidebar.button("👀 Ver demostración", use_container_width=True):
        entrar_modo_invitado()

    opciones_menu = [
        "📊 Cargar Venta Diaria",
        "📥 Importar Ventas Históricas",
        "📈 Dashboard",
        "🏷️ Productos y Recetas",
        "🛒 Insumos y Costos",
        "🧾 Gastos Operativos",
        "🗑️ Mermas",
        "⚙️ Calculadora de Costos",
    ]

opcion_menu = st.sidebar.radio("Navegación:", opciones_menu)

if modo_invitado:
    st.info(
        "👀 **Modo demostración:** los productos, recetas e insumos son ficticios. "
        "Nada de lo que hagas acá modifica la información real de Dulce Mar."
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
        prod_sel = selector_producto_agrupado("Producto", "venta_producto")
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

    faltantes_venta = list(faltantes)
    faltantes_budin = []

    if cant_budin_promo > 0 and budin_sel_promo:
        _, costo_u_budin, faltantes_budin = calcular_costo_receta(
            budin_sel_promo
        )

        if faltantes_budin:
            faltantes_venta.extend(
                [f"{budin_sel_promo}: {x}" for x in faltantes_budin]
            )
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
            if faltantes_venta:
                st.error(
                    "Corregí los insumos faltantes antes de guardar: "
                    + ", ".join(faltantes_venta)
                )
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
    st.caption("Se muestran 50 ventas por página. El resto permanece guardado en Supabase.")

    # ---------------- PAGINACIÓN ----------------
    VENTAS_POR_PAGINA = 50

    try:
        total_respuesta = (
            supabase.table("ventas")
            .select("id", count="exact", head=True)
            .execute()
        )
        total_ventas = int(total_respuesta.count or 0)
    except Exception as err:
        st.error(f"No se pudo contar el historial: {err}")
        total_ventas = 0

    if total_ventas == 0:
        st.info("Todavía no hay ventas registradas.")
    else:
        total_paginas = (total_ventas + VENTAS_POR_PAGINA - 1) // VENTAS_POR_PAGINA

        if "pagina_historial_ventas" not in st.session_state:
            st.session_state.pagina_historial_ventas = 1

        pagina_actual = min(
            max(int(st.session_state.pagina_historial_ventas), 1),
            total_paginas,
        )

        offset = (pagina_actual - 1) * VENTAS_POR_PAGINA

        try:
            respuesta = (
                supabase.table("ventas")
                .select("*")
                .order("fecha", desc=True)
                .order("id", desc=True)
                .range(offset, offset + VENTAS_POR_PAGINA - 1)
                .execute()
            )
            datos_ventas = respuesta.data or []
        except Exception as err:
            st.error(f"No se pudo cargar el historial: {err}")
            datos_ventas = []

        # Controles de navegación: anterior, números de página y siguiente.
        if total_paginas > 1:
            # Mostramos anterior + hasta 5 números + siguiente.
            inicio_pag = max(1, pagina_actual - 2)
            fin_pag = min(total_paginas, inicio_pag + 4)
            inicio_pag = max(1, fin_pag - 4)
            paginas_mostrar = list(range(inicio_pag, fin_pag + 1))
            nav_cols = st.columns(len(paginas_mostrar) + 2)

            with nav_cols[0]:
                if st.button(
                    "⬅️",
                    disabled=pagina_actual <= 1,
                    use_container_width=True,
                    key="hist_prev",
                    help="Página anterior",
                ):
                    st.session_state.pagina_historial_ventas = pagina_actual - 1
                    st.rerun()

            for i, numero_pag in enumerate(paginas_mostrar, start=1):
                with nav_cols[i]:
                    if st.button(
                        f"{'🔵 ' if numero_pag == pagina_actual else ''}{numero_pag}",
                        disabled=numero_pag == pagina_actual,
                        use_container_width=True,
                        key=f"hist_page_{numero_pag}",
                    ):
                        st.session_state.pagina_historial_ventas = numero_pag
                        st.rerun()

            with nav_cols[-1]:
                if st.button(
                    "➡️",
                    disabled=pagina_actual >= total_paginas,
                    use_container_width=True,
                    key="hist_next",
                    help="Página siguiente",
                ):
                    st.session_state.pagina_historial_ventas = pagina_actual + 1
                    st.rerun()

            st.caption(
                f"Página {pagina_actual} de {total_paginas} · "
                f"{total_ventas} ventas registradas · "
                f"Mostrando {offset + 1}-{min(offset + VENTAS_POR_PAGINA, total_ventas)}"
            )

        if not datos_ventas:
            st.info("No hay ventas para esta página.")
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
# 2. IMPORTAR VENTAS HISTÓRICAS
# ============================================================

elif opcion_menu == "📥 Importar Ventas Históricas":

    st.header("📥 Importar ventas históricas")
    st.caption(
        "Subí uno o varios Excel/CSV y el sistema intentará detectar automáticamente "
        "fecha, producto, cantidad y precio. No modifica insumos, recetas ni ventas existentes."
    )

    st.info(
        "💡 Reglas históricas: **2 porc**, **2 porciones** o **por. budín** se interpreta como porciones de budín. "
        "Si el budín no tiene gusto indicado, se guarda como **Budines (gusto no registrado)**. "
        "En el caso de **chipa**, si no se aclara presentación, se interpreta como **1 bolsa de media docena (6u)**; "
        "por ejemplo, **2 chipa = 2 bolsas de 6**. Así mantenemos la ganancia histórica completa sin inventar gustos."
    )

    archivos = st.file_uploader(
        "Seleccioná los archivos históricos",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="Podés seleccionar varios archivos de abril, mayo, junio y julio a la vez.",
    )

    if archivos:
        todas_las_filas = []
        todas_las_advertencias = []

        for archivo in archivos:
            try:
                if archivo.name.lower().endswith(".csv"):
                    # Para CSV se intenta primero UTF-8 y luego latin-1.
                    try:
                        df_csv = pd.read_csv(archivo)
                    except UnicodeDecodeError:
                        archivo.seek(0)
                        df_csv = pd.read_csv(archivo, encoding="latin-1")
                    hojas_csv = {"CSV": df_csv}

                    # Reutilizamos la misma lógica de Excel mediante un pequeño wrapper.
                    # Pandas Excel necesita un archivo, así que procesamos directamente la hoja.
                    for nombre_hoja, df in hojas_csv.items():
                        col_fecha = detectar_columna(df, "fecha")
                        col_producto = detectar_columna(df, "producto")
                        col_cantidad = detectar_columna(df, "cantidad")
                        col_monto = detectar_columna(df, "monto")
                        col_presentacion = detectar_columna(df, "presentacion")

                        if not col_fecha or not col_producto or not col_monto:
                            todas_las_advertencias.append(
                                f"{archivo.name}: no se detectaron Fecha + Producto + Monto."
                            )
                            continue

                        for nro_fila, fila in df.dropna(axis=0, how="all").iterrows():
                            fecha = pd.to_datetime(fila.get(col_fecha), errors="coerce", dayfirst=True)
                            if pd.isna(fecha):
                                continue
                            texto_producto = str(fila.get(col_producto, "")).strip()
                            producto = encontrar_producto_historico(texto_producto)
                            if not producto:
                                if texto_producto and texto_producto.lower() != "nan":
                                    todas_las_advertencias.append(
                                        f"{archivo.name} / fila {nro_fila + 2}: producto no reconocido: '{texto_producto}'."
                                    )
                                continue
                            monto = numero(fila.get(col_monto), 0.0)
                            if monto <= 0:
                                continue
                            cantidad = numero(fila.get(col_cantidad), 0.0) if col_cantidad else 0.0
                            if cantidad <= 0:
                                cantidad = extraer_cantidad_desde_texto(texto_producto) or 1.0
                            presentacion_texto = str(fila.get(col_presentacion, "")) if col_presentacion else ""
                            presentacion = detectar_presentacion_historica(
                                f"{texto_producto} {presentacion_texto}", producto, monto, cantidad
                            )
                            costo, costo_ok = costo_venta_historica(producto, presentacion, cantidad)
                            producto_guardado = (
                                "Budines (gusto no registrado)"
                                if producto == "__BUDIN_HISTORICO_SIN_GUSTO__"
                                else producto
                            )
                            if not costo_ok:
                                costo = 0.0
                                todas_las_advertencias.append(
                                    f"{archivo.name} / fila {nro_fila + 2}: costo no calculable para '{producto_guardado}'."
                                )
                            todas_las_filas.append({
                                "fecha": fecha.date(),
                                "producto": producto_guardado,
                                "cantidad": int(round(cantidad)),
                                "tipo_venta": presentacion,
                                "monto_total": float(monto),
                                "costo_total": float(costo),
                                "ganancia_limpia": float(monto - costo),
                                "_archivo": archivo.name,
                                "_hoja": "CSV",
                                "_fila": int(nro_fila + 2),
                            })
                else:
                    filas, advertencias = preparar_ventas_historicas_archivo(archivo)
                    todas_las_filas.extend(filas)
                    todas_las_advertencias.extend(advertencias)
            except Exception as err:
                todas_las_advertencias.append(
                    f"{archivo.name}: no se pudo procesar ({err})."
                )

        if todas_las_filas:
            df_importacion = pd.DataFrame(todas_las_filas)

            # Una misma combinación de fecha/producto/cantidad/precio puede ser una
            # venta perfectamente válida más de una vez el mismo día. Por eso NO
            # eliminamos duplicados por contenido. En cambio, comparamos cantidades
            # (ocurrencias) contra Supabase: si ya existe 1 venta idéntica y el Excel
            # trae 2, se conserva 1 como nueva. Esto también evita volver a cargar
            # indefinidamente el mismo Excel sin borrar ventas legítimas.
            df_importacion["_firma"] = df_importacion.apply(firma_venta_historica, axis=1)

            try:
                existentes = (
                    supabase.table("ventas")
                    .select("fecha, producto, cantidad, tipo_venta, monto_total")
                    .execute()
                    .data
                    or []
                )
                conteo_existentes = Counter(firma_venta_historica(x) for x in existentes)
            except Exception as err:
                conteo_existentes = Counter()
                st.warning(
                    "No se pudo verificar coincidencias contra Supabase. "
                    f"Revisá antes de confirmar. Detalle: {err}"
                )

            # Marca solamente tantas ocurrencias como ya existan en Supabase.
            # Ejemplo: si el Excel trae 2 ventas idénticas y Supabase tiene 1,
            # una queda como 'ya cargada' y la otra como nueva.
            ocurrencias_vistas = Counter()
            estados_existencia = []
            for firma in df_importacion["_firma"]:
                ocurrencias_vistas[firma] += 1
                ya_existia = ocurrencias_vistas[firma] <= conteo_existentes.get(firma, 0)
                estados_existencia.append(ya_existia)

            df_importacion["_existente"] = estados_existencia
            nuevas = df_importacion[~df_importacion["_existente"]].copy()
            repetidas = int(df_importacion["_existente"].sum())

            st.markdown("---")
            st.subheader("🔎 Vista previa")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Filas detectadas", len(df_importacion))
            c2.metric("Nuevas para cargar", len(nuevas))
            c3.metric("Ya cargadas", repetidas)
            c4.metric("Facturación nueva", dinero(nuevas["monto_total"].sum() if not nuevas.empty else 0))

            # Resumen especialmente útil para revisar los budines históricos.
            resumen_productos = (
                df_importacion.groupby("producto")
                .agg(
                    Ventas=("monto_total", "sum"),
                    Cantidad=("cantidad", "sum"),
                    Operaciones=("producto", "count"),
                )
                .reset_index()
                .sort_values("Ventas", ascending=False)
            )

            st.dataframe(
                resumen_productos.style.format({"Ventas": "${:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Las ventas con la misma fecha, producto, cantidad, presentación y monto pueden aparecer varias veces: se conservan porque pueden ser operaciones distintas. Solo se omite una ocurrencia cuando esa misma cantidad de coincidencias ya existe en Supabase. Los costos y márgenes de la importación se reconstruyen con las recetas/insumos "
                "actualmente cargados. En budines sin gusto se usa el costo promedio de los budines conocidos."
            )

            with st.expander("Ver ventas detectadas antes de importar"):
                columnas_mostrar = [
                    "fecha", "producto", "cantidad", "tipo_venta",
                    "monto_total", "costo_total", "ganancia_limpia",
                    "_archivo", "_hoja", "_fila", "_existente",
                ]
                st.dataframe(
                    df_importacion[columnas_mostrar].style.format({
                        "monto_total": "${:,.2f}",
                        "costo_total": "${:,.2f}",
                        "ganancia_limpia": "${:,.2f}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

            if todas_las_advertencias:
                with st.expander(f"⚠️ Avisos ({len(todas_las_advertencias)})"):
                    for aviso in todas_las_advertencias[:100]:
                        st.write("• " + aviso)
                    if len(todas_las_advertencias) > 100:
                        st.caption("Se muestran los primeros 100 avisos.")

            if nuevas.empty:
                st.success("No hay ventas nuevas para importar: todas las coincidencias detectadas ya están cargadas en Supabase.")
            else:
                if st.button(
                    f"💾 Importar {len(nuevas)} ventas nuevas",
                    type="primary",
                    use_container_width=True,
                ):
                    registros = nuevas[[
                        "fecha", "producto", "cantidad", "tipo_venta",
                        "monto_total", "costo_total", "ganancia_limpia",
                    ]].copy()
                    registros["fecha"] = registros["fecha"].astype(str)
                    registros = registros.to_dict(orient="records")

                    try:
                        # Insertamos por lotes para que una importación grande sea más estable.
                        lote = 200
                        total_insertadas = 0
                        for inicio in range(0, len(registros), lote):
                            bloque = registros[inicio:inicio + lote]
                            supabase.table("ventas").insert(bloque).execute()
                            total_insertadas += len(bloque)

                        st.success(
                            f"✅ Se importaron {total_insertadas} ventas históricas correctamente. "
                            f"Se omitieron {repetidas} repetidas/ya existentes."
                        )
                        st.rerun()
                    except Exception as err:
                        st.error(
                            "No se pudo completar la importación. "
                            "Las ventas ya existentes no se modifican. "
                            f"Detalle: {err}"
                        )
        else:
            st.warning(
                "No se detectaron ventas importables todavía. "
                "Revisá los avisos de abajo: ahí se indica exactamente qué archivo, hoja y fila no se pudo interpretar."
            )

        # Mostrar los avisos también cuando no se detectó ninguna venta. Antes
        # quedaban ocultos dentro del bloque de vista previa y parecía que el
        # Excel simplemente "no funcionaba".
        if todas_las_advertencias:
            with st.expander(f"⚠️ Revisar {len(todas_las_advertencias)} aviso(s) del importador", expanded=not todas_las_filas):
                for aviso in todas_las_advertencias[:200]:
                    st.write("• " + aviso)
                if len(todas_las_advertencias) > 200:
                    st.caption("Se muestran los primeros 200 avisos.")

        if not todas_las_advertencias and not todas_las_filas:
            st.caption(
                "Consejo: si tus Excel tienen encabezados diferentes a Fecha / Producto / Cantidad / Monto, "
                "subilos igual; si no se detectan automáticamente te mostramos qué columna faltó."
            )

# ============================================================
# 3. DASHBOARD
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

        # Unidades equivalentes: usamos la receta real para que
        # "Entero" represente el rendimiento completo y no simplemente 1.
        def unidades_equivalentes(row):
            producto = row.get("producto")
            pres = row.get("tipo_venta", "")
            cant = numero(row.get("cantidad"), 0)
            receta = st.session_state.RECETAS.get(producto, {})
            factor = multiplicador_presentacion(pres, receta)
            return cant * factor

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
                y="Margen",
                title="Margen bruto por día",
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
                y="Margen",
                title="Margen bruto por mes",
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
                prod_mod = selector_producto_agrupado(
                    "Producto",
                    "prod_mod_precio",
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

                            if modo_invitado:
                                st.session_state.RECETAS[prod_mod]["precios"] = nuevos_precios
                                st.success(
                                    "Precio actualizado en modo demostración. "
                                    "No se modificó la base real."
                                )
                            else:
                                supabase.table("productos").update({
                                    "precios": nuevos_precios
                                }).eq("nombre", prod_mod).execute()

                                st.session_state.RECETAS[prod_mod]["precios"] = nuevos_precios
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
                datos_producto = {
                    "rinde": int(rinde_prod),
                    "tipo": tipo_rinde,
                    "precios": precios,
                    "ingredientes": dict_ingredientes_nuevo,
                }

                if modo_invitado:
                    st.session_state.RECETAS[nombre_limpio] = copy.deepcopy(datos_producto)
                else:
                    supabase.table("productos").insert(registro).execute()
                    st.session_state.RECETAS[nombre_limpio] = copy.deepcopy(datos_producto)

                modal_producto_guardado(nombre_limpio)

            except Exception as err:
                st.error(f"No se pudo guardar el producto: {err}")

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
                    if modo_invitado:
                        del st.session_state.RECETAS[prod_eliminar]
                        st.success("Producto eliminado de la demostración.")
                    else:
                        supabase.table("productos").delete().eq(
                            "nombre", prod_eliminar,
                        ).execute()
                        del st.session_state.RECETAS[prod_eliminar]
                        st.success("Producto eliminado.")
                    st.rerun()
                except Exception as err:
                    st.error(f"No se pudo eliminar: {err}")

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
                        if modo_invitado:
                            st.session_state.INSUMOS[insumo_editar] = float(nuevo_precio)
                            st.success(
                                "Costo actualizado en modo demostración. "
                                "No se modificó la base real."
                            )
                        else:
                            supabase.table("insumos").update({
                                "precio": float(nuevo_precio)
                            }).eq(
                                "nombre", insumo_editar,
                            ).execute()
                            st.session_state.INSUMOS[insumo_editar] = float(nuevo_precio)
                            st.success("Costo actualizado.")
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

                    clave_a_eliminar = clave_normalizada(insumo_editar)

                    for nombre, receta in (
                        st.session_state.RECETAS.items()
                    ):
                        usados = receta.get("ingredientes", {})
                        if any(
                            clave_normalizada(ing) == clave_a_eliminar
                            for ing in usados
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
                            if modo_invitado:
                                del st.session_state.INSUMOS[insumo_editar]
                                st.success("Insumo eliminado de la demostración.")
                            else:
                                supabase.table("insumos").delete().eq(
                                    "nombre", insumo_editar,
                                ).execute()
                                del st.session_state.INSUMOS[insumo_editar]
                                st.success("Insumo eliminado.")
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

            if buscar_insumo(nombre) is not None:
                st.warning(
                    "Ese insumo ya existe (también se detectan diferencias de tildes/mayúsculas)."
                )
                st.stop()

            try:
                if modo_invitado:
                    st.session_state.INSUMOS[nombre] = float(nuevo_precio)
                    st.success(
                        "Insumo creado en modo demostración. "
                        "No se modificó la base real."
                    )
                else:
                    supabase.table("insumos").insert({
                        "nombre": nombre,
                        "precio": float(nuevo_precio),
                    }).execute()
                    st.session_state.INSUMOS[nombre] = float(nuevo_precio)
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

    receta_seleccionada = selector_producto_agrupado(
        "Producto",
        "calc_producto",
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
    st.caption(
        "Podés corregir la cantidad de un ingrediente, cambiar su precio, "
        "agregarlo o eliminarlo de esta receta. Los cambios se guardan en la receta real "
        "cuando estás en modo privado."
    )

    ingredientes_actuales = receta.get("ingredientes", {}) or {}

    # --------------------------------------------------------
    # TABLA DE DESGLOSE
    # --------------------------------------------------------
    desglose = []

    for ing, cant in ingredientes_actuales.items():
        nombre_real = buscar_insumo(ing)
        precio_ing = (
            st.session_state.INSUMOS.get(nombre_real)
            if nombre_real is not None
            else None
        )

        if precio_ing is None:
            costo_ing = 0.0
            precio_mostrar = "FALTANTE"
        else:
            precio_ing = numero(precio_ing)
            costo_ing = numero(cant) * precio_ing
            precio_mostrar = dinero(precio_ing)

        if "(unidad)" in ing.lower():
            cantidad_mostrar = f"{numero(cant):.4f}"
        else:
            cantidad_mostrar = f"{numero(cant):.3f}"

        desglose.append({
            "Insumo": ing,
            "Cantidad": cantidad_mostrar,
            "Precio actual": precio_mostrar,
            "Costo en receta": costo_ing,
        })

    df_desglose = pd.DataFrame(desglose)

    if df_desglose.empty:
        st.info("Esta receta todavía no tiene insumos.")
    else:
        st.dataframe(
            df_desglose.style.format({
                "Costo en receta": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # EDITAR INSUMO EXISTENTE
    # --------------------------------------------------------
    with st.expander("✏️ Editar un insumo de esta receta", expanded=False):
        if not ingredientes_actuales:
            st.info("No hay ingredientes para editar.")
        else:
            ing_editar = st.selectbox(
                "Insumo",
                list(ingredientes_actuales.keys()),
                key=f"calc_editar_ing_{receta_seleccionada}",
            )

            cantidad_actual = numero(ingredientes_actuales.get(ing_editar), 0.0)
            precio_actual = numero(
                st.session_state.INSUMOS.get(buscar_insumo(ing_editar), 0.0),
                0.0,
            )

            col1, col2 = st.columns(2)

            with col1:
                if "(unidad)" in ing_editar.lower():
                    nueva_cantidad = st.number_input(
                        "Cantidad utilizada",
                        min_value=0.0001,
                        value=max(cantidad_actual, 0.0001),
                        step=0.1,
                        format="%.4f",
                        key=f"calc_cantidad_{receta_seleccionada}_{ing_editar}",
                    )
                else:
                    nueva_cantidad = st.number_input(
                        "Cantidad utilizada",
                        min_value=0.0001,
                        value=max(cantidad_actual, 0.0001),
                        step=0.010,
                        format="%.4f",
                        key=f"calc_cantidad_{receta_seleccionada}_{ing_editar}",
                    )

            with col2:
                if clave_normalizada(ing_editar) == clave_normalizada("Naranja (unidad)"):
                    nuevo_precio = precio_actual
                    st.number_input(
                        "Precio por naranja ($)",
                        min_value=0.0,
                        value=precio_actual,
                        step=100.0,
                        disabled=True,
                        key=f"calc_precio_{receta_seleccionada}_{ing_editar}",
                    )
                    st.caption("Se calcula automáticamente: precio de Naranja (kg) × 0,150.")
                else:
                    nuevo_precio = st.number_input(
                        "Precio actual del insumo ($)",
                        min_value=0.0,
                        value=precio_actual,
                        step=100.0,
                        key=f"calc_precio_{receta_seleccionada}_{ing_editar}",
                    )

            if clave_normalizada(ing_editar) != clave_normalizada("Naranja (unidad)"):
                st.caption(
                    "El precio del insumo es global: si lo cambiás acá, también cambia "
                    "el costo de ese insumo en las demás recetas."
                )

            if st.button(
                "💾 Guardar cambios",
                type="primary",
                use_container_width=True,
                key=f"calc_guardar_ing_{receta_seleccionada}",
            ):
                try:
                    nombre_real = buscar_insumo(ing_editar)
                    ingredientes_nuevos = dict(ingredientes_actuales)
                    ingredientes_nuevos[ing_editar] = float(nueva_cantidad)
                    st.session_state.RECETAS[receta_seleccionada]["ingredientes"] = ingredientes_nuevos

                    if nombre_real is not None:
                        guardar_insumo_en_base(nombre_real, nuevo_precio)
                    guardar_receta_en_base(receta_seleccionada)

                    st.success("Ingrediente y precio actualizados.")
                    st.rerun()
                except Exception as err:
                    st.error(f"No se pudieron guardar los cambios: {err}")

    # --------------------------------------------------------
    # AGREGAR INSUMO A LA RECETA
    # --------------------------------------------------------
    with st.expander("➕ Agregar insumo a esta receta", expanded=False):
        disponibles = [
            nombre for nombre in st.session_state.INSUMOS
            if nombre not in ingredientes_actuales
        ]

        if disponibles:
            nuevo_ing = st.selectbox(
                "Elegí el insumo",
                disponibles,
                key=f"calc_nuevo_ing_{receta_seleccionada}",
            )

            if "(unidad)" in nuevo_ing.lower():
                cantidad_nuevo = st.number_input(
                    "Cantidad utilizada",
                    min_value=0.0001,
                    value=1.0,
                    step=0.1,
                    format="%.4f",
                    key=f"calc_nueva_cantidad_{receta_seleccionada}",
                )
            else:
                cantidad_nuevo = st.number_input(
                    "Cantidad utilizada",
                    min_value=0.0001,
                    value=0.100,
                    step=0.010,
                    format="%.4f",
                    key=f"calc_nueva_cantidad_{receta_seleccionada}",
                )

            if st.button(
                "➕ Agregar a la receta",
                type="primary",
                use_container_width=True,
                key=f"calc_agregar_ing_{receta_seleccionada}",
            ):
                try:
                    ingredientes_nuevos = dict(ingredientes_actuales)
                    ingredientes_nuevos[nuevo_ing] = float(cantidad_nuevo)
                    st.session_state.RECETAS[receta_seleccionada]["ingredientes"] = ingredientes_nuevos
                    guardar_receta_en_base(receta_seleccionada)
                    st.success(f"{nuevo_ing} agregado a la receta.")
                    st.rerun()
                except Exception as err:
                    st.error(f"No se pudo agregar el insumo: {err}")
        else:
            st.info("Todos los insumos disponibles ya están incluidos en esta receta.")

        st.markdown("#### 🆕 Crear un insumo nuevo")
        col1, col2 = st.columns(2)
        with col1:
            nombre_insumo_nuevo = st.text_input(
                "Nombre del nuevo insumo",
                placeholder="Ej: Nueces (kg)",
                key=f"calc_nombre_insumo_nuevo_{receta_seleccionada}",
            )
        with col2:
            precio_insumo_nuevo = st.number_input(
                "Precio del insumo ($)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key=f"calc_precio_insumo_nuevo_{receta_seleccionada}",
            )

        if st.button(
            "🆕 Crear insumo y agregarlo",
            use_container_width=True,
            key=f"calc_crear_ing_{receta_seleccionada}",
        ):
            nombre_nuevo = limpiar_texto(nombre_insumo_nuevo)

            if not nombre_nuevo:
                st.warning("Escribí un nombre para el insumo.")
                st.stop()

            if buscar_insumo(nombre_nuevo) is not None:
                st.warning("Ya existe un insumo con ese nombre. Usá 'Agregar insumo a esta receta'.")
                st.stop()

            try:
                crear_insumo_en_base(nombre_nuevo, precio_insumo_nuevo)
                ingredientes_nuevos = dict(ingredientes_actuales)
                ingredientes_nuevos[nombre_nuevo] = 1.0
                st.session_state.RECETAS[receta_seleccionada]["ingredientes"] = ingredientes_nuevos
                guardar_receta_en_base(receta_seleccionada)
                st.success(f"{nombre_nuevo} fue creado y agregado a la receta.")
                st.rerun()
            except Exception as err:
                st.error(f"No se pudo crear el insumo: {err}")

    # --------------------------------------------------------
    # ELIMINAR INSUMO DE LA RECETA
    # --------------------------------------------------------
    with st.expander("🗑️ Eliminar un insumo de esta receta", expanded=False):
        if not ingredientes_actuales:
            st.info("No hay ingredientes para eliminar.")
        else:
            ing_eliminar = st.selectbox(
                "Insumo a quitar",
                list(ingredientes_actuales.keys()),
                key=f"calc_eliminar_ing_{receta_seleccionada}",
            )

            st.warning(
                "Esto lo elimina solamente de esta receta. El insumo seguirá existiendo "
                "en 'Insumos y Costos' y podrá usarse en otros productos."
            )

            if st.button(
                "🗑️ Eliminar de esta receta",
                use_container_width=True,
                key=f"calc_eliminar_btn_{receta_seleccionada}",
            ):
                try:
                    ingredientes_nuevos = dict(ingredientes_actuales)
                    del ingredientes_nuevos[ing_eliminar]
                    st.session_state.RECETAS[receta_seleccionada]["ingredientes"] = ingredientes_nuevos
                    guardar_receta_en_base(receta_seleccionada)
                    st.success(f"{ing_eliminar} fue eliminado de la receta.")
                    st.rerun()
                except Exception as err:
                    st.error(f"No se pudo eliminar el insumo: {err}")

# ============================================================
# FIN
# ============================================================
