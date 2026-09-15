import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(
    page_title="Dulce Mar - App Pos", 
    page_icon="🧁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Conexión con Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("Error al conectar con Supabase. Verificá los Secrets de Streamlit.")

# --- DATOS POR DEFECTO PARA PRIMERA CARGA ---
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

# --- FUNCIONES SUPABASE ---
def obtener_insumos():
    try:
        res = supabase.table("insumos").select("*").execute()
        if not res.data:
            datos_insertar = [{"nombre": k, "precio": float(v)} for k, v in INSUMOS_DEFAULT.items()]
            supabase.table("insumos").insert(datos_insertar).execute()
            return {k: float(v) for k, v in INSUMOS_DEFAULT.items()}
        return {item["nombre"]: float(item["precio"]) for item in res.data}
    except Exception as e:
        return INSUMOS_DEFAULT

def obtener_recetas():
    try:
        res = supabase.table("productos").select("*").execute()
        if not res.data:
            datos_insertar = []
            for k, v in RECETAS_DEFAULT.items():
                datos_insertar.append({
                    "nombre": k,
                    "rinde": v["rinde"],
                    "tipo": v["tipo"],
                    "precios": v["precios"],
                    "ingredientes": v["ingredientes"]
                })
            supabase.table("productos").insert(datos_insertar).execute()
            return RECETAS_DEFAULT
        
        recetas_dict = {}
        for item in res.data:
            recetas_dict[item["nombre"]] = {
                "rinde": item["rinde"],
                "tipo": item["tipo"],
                "precios": item["precios"],
                "ingredientes": item["ingredientes"]
            }
        return recetas_dict
    except Exception as e:
        return RECETAS_DEFAULT

if "INSUMOS" not in st.session_state:
    st.session_state.INSUMOS = obtener_insumos()

if "RECETAS" not in st.session_state:
    st.session_state.RECETAS = obtener_recetas()

def calcular_costo_receta(nombre_receta):
    receta = st.session_state.RECETAS[nombre_receta]
    costo_lote = sum(cant * st.session_state.INSUMOS.get(ing, 0) for ing, cant in receta["ingredientes"].items())
    costo_unitario = costo_lote / receta["rinde"]
    return costo_lote, costo_unitario

@st.dialog("✅ ¡Venta Guardada con Éxito!")
def modal_venta_exitosa(detalle, total, ganancia):
    st.balloons()
    st.markdown(f"### 🧁 Dulce Mar")
    st.write(f"**Detalle:** {detalle}")
    st.write(f"**Monto Cobrado:** ${total:,.2f}")
    st.write(f"**Ganancia Limpia:** ${ganancia:,.2f}")
    if st.button("Continuar Vendiendo 🛒", use_container_width=True):
        st.rerun()

@st.dialog("✅ Producto Guardado Exitosamente")
def modal_producto_guardado(nombre):
    st.success(f"¡El producto **'{nombre}'** se ha guardado correctamente!")
    if st.button("Entendido 👍", use_container_width=True):
        st.rerun()

# --- ESTILOS CSS CREATIVOS OPTIMIZADOS PARA CELULAR ---
st.markdown("""
    <style>
    /* Estilos generales */
    .stApp {
        background-color: #12181f;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header Principal Dulce Mar */
    .brand-header {
        background: linear-gradient(135deg, #e8a598 0%, #72b3c2 100%);
        padding: 16px 20px;
        border-radius: 16px;
        color: #12181f;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .brand-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 1px;
        color: #12181f !important;
    }
    .brand-header p {
        margin: 2px 0 0 0;
        font-size: 14px;
        font-weight: 600;
        opacity: 0.9;
    }

    /* Tarjetas de Producto estilo Celular */
    .product-card {
        background-color: #1a232e;
        border-radius: 14px;
        padding: 14px;
        border: 1px solid #2d3b4e;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .product-title {
        font-size: 18px;
        font-weight: 700;
        color: #f3d5b5;
        margin-bottom: 4px;
    }
    .product-price {
        font-size: 16px;
        font-weight: 600;
        color: #72b3c2;
    }

    /* Resumen interactivo táctil */
    .cart-box {
        background: linear-gradient(180deg, #1e2a38 0%, #16202c 100%);
        border: 2px solid #72b3c2;
        border-radius: 16px;
        padding: 18px;
        margin-top: 15px;
        box-shadow: 0 4px 20px rgba(114, 179, 194, 0.15);
    }
    .cart-title {
        font-size: 15px;
        color: #e8a598;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .val-costo {
        font-size: 22px;
        font-weight: bold;
        color: #f87171;
    }
    .val-ganancia {
        font-size: 26px;
        font-weight: bold;
        color: #4ade80;
    }

    /* Ajustes visuales para pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a232e;
        border-radius: 10px;
        color: #a0aec0;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #72b3c2 !important;
        color: #12181f !important;
    }

    /* Botones primarios */
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.2s;
    }
    </style>
""", unsafe_allow_html=True)

# BANNER SUPERIOR DE LA APP
st.markdown("""
    <div class="brand-header">
        <h1>🧁 DULCE MAR</h1>
        <p>Sistema Integral de Gestión & Caja Rápida</p>
    </div>
""", unsafe_allow_html=True)

# NAVEGACIÓN SUPERIOR POR PESTAÑAS (Ideal para pantallas táctiles)
tab_pos, tab_clasica, tab_metricas, tab_productos, tab_insumos, tab_calc = st.tabs([
    "📱 Caja Rápida", 
    "📊 Venta Tradicional", 
    "📈 Métricas", 
    "🏷️ Productos",
    "🛒 Insumos",
    "⚙️ Calculadora"
])

# -------------------------------------------------------------------
# 1. PESTAÑA: CAJA RÁPIDA (OPTIMIZADA PARA CELULAR Y MÓVIL)
# -------------------------------------------------------------------
with tab_pos:
    st.subheader("⚡ Cobro Rápido en Caja")
    fecha_pos = st.date_input("Fecha de Venta:", datetime.now(), key="pos_date")
    
    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        st.write("👉 **Seleccioná el producto:**")
        prod_pos = st.selectbox("Buscar Producto:", list(st.session_state.RECETAS.keys()), key="pos_prod_sel")
        datos_prod = st.session_state.RECETAS[prod_pos]

        st.write("👉 **Seleccioná la presentación:**")
        pres_pos = st.radio("Presentación disponible:", list(datos_prod["precios"].keys()), horizontal=True, key="pos_pres_radio")
        
        cant_pos = st.number_input("Cantidad a vender:", min_value=1, value=1, step=1, key="pos_cant_num")

        # PROMO CAFÉ INTELIGENTE
        promo_activa = False
        cant_budin_promo = 0
        budin_sel_promo = None
        precio_extra_budin = 0.0

        if "Cafe" in prod_pos:
            st.markdown("---")
            st.markdown("☕ **¡Promoción Disponible!**")
            promo_activa = st.toggle("Agregar porción de Budín a $750", value=False)
            if promo_activa:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    budines_disponibles = [p for p in st.session_state.RECETAS.keys() if "Budin" in p]
                    budin_sel_promo = st.selectbox("Sabor Budín:", budines_disponibles, key="pos_budin_sel")
                with col_b2:
                    cant_budin_promo = st.number_input("Cantidad Budines:", min_value=1, value=1, step=1, key="pos_budin_cant")
                precio_extra_budin = cant_budin_promo * 750.0

    with col_der:
        # CÁLCULOS EN TIEMPO REAL
        precio_base = float(datos_prod["precios"][pres_pos] * cant_pos)
        precio_total_sugerido = precio_base + precio_extra_budin
        
        costo_lote, costo_u = calcular_costo_receta(prod_pos)
        if "Docena (12u)" in pres_pos:
            costo_total_venta = costo_u * 12 * cant_pos
        elif "Media Docena (6u)" in pres_pos:
            costo_total_venta = costo_u * 6 * cant_pos
        elif "Porción" in pres_pos or "1 Unidad" in pres_pos:
            costo_total_venta = costo_u * cant_pos
        else:
            costo_total_venta = costo_lote * cant_pos

        if cant_budin_promo > 0 and budin_sel_promo:
            _, costo_u_budin = calcular_costo_receta(budin_sel_promo)
            costo_total_venta += (costo_u_budin * cant_budin_promo)

        precio_final_cobrado = st.number_input("Monto Cobrado Final ($):", value=precio_total_sugerido, step=100.0, key="pos_monto_final")
        ganancia_limpia = precio_final_cobrado - costo_total_venta

        # TARGETA DE RESUMEN VISUAL
        st.markdown(f"""
            <div class="cart-box">
                <div class="cart-title">🛍️ Resumen del Carrito</div>
                <div style="margin-top: 10px; font-size: 16px;">
                    <b>{prod_pos}</b><br>
                    <span style="color: #a0aec0;">{pres_pos} x{cant_pos}</span>
                </div>
                {"<div style='color: #e8a598; font-size: 14px; margin-top: 4px;'>+ Promo Budín (" + str(cant_budin_promo) + "x)</div>" if promo_activa else ""}
                <hr style="border-color: #2d3b4e; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 12px; color: #a0aec0;">COSTO INSUMOS</div>
                        <div class="val-costo">${costo_total_venta:,.2f}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: #a0aec0;">GANANCIA NETO</div>
                        <div class="val-ganancia">${ganancia_limpia:,.2f}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 REGISTRAR VENTA AHORA", use_container_width=True, type="primary"):
            try:
                presentacion_final = pres_pos
                if cant_budin_promo > 0 and budin_sel_promo:
                    gusto_corto = budin_sel_promo.replace("Budin de ", "").replace("Budin ", "")
                    presentacion_final += f" + {cant_budin_promo}x Budín {gusto_corto} (Promo $750)"

                registro = {
                    "fecha": str(fecha_pos),
                    "producto": prod_pos,
                    "cantidad": int(cant_pos),
                    "tipo_venta": presentacion_final,
                    "monto_total": float(precio_final_cobrado),
                    "costo_total": float(costo_total_venta),
                    "ganancia_limpia": float(ganancia_limpia)
                }
                supabase.table("ventas").insert(registro).execute()
                modal_venta_exitosa(f"{prod_pos} ({presentacion_final}) x{cant_pos}", precio_final_cobrado, ganancia_limpia)
            except Exception as err:
                st.error(f"Error al registrar venta: {err}")

# -------------------------------------------------------------------
# 2. PESTAÑA: VENTA TRADICIONAL & HISTORIAL
# -------------------------------------------------------------------
with tab_clasica:
    st.header("🛒 Registro y Historial Detallado")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_venta = st.date_input("Fecha:", datetime.now(), key="trad_fecha")
        prod_sel = st.selectbox("Producto:", list(st.session_state.RECETAS.keys()), key="trad_prod")
        datos_prod = st.session_state.RECETAS[prod_sel]
        
    with col2:
        tipo_presentacion = st.selectbox("Presentación:", list(datos_prod["precios"].keys()), key="trad_pres")
        cantidad = st.number_input("Cantidad vendida:", min_value=1, value=1, step=1, key="trad_cant")
        
        cant_budin_promo = 0
        budin_sel_promo = None
        precio_extra_budin = 0.0
        
        if "Cafe" in prod_sel:
            st.markdown("---")
            agregar_promo = st.checkbox("☕ Promo: ¡Agregar porción de Budín a $750!", key="trad_promo")
            if agregar_promo:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    budines_disponibles = [p for p in st.session_state.RECETAS.keys() if "Budin" in p]
                    budin_sel_promo = st.selectbox("Gusto del budín:", budines_disponibles, key="trad_budin_sel")
                with col_b2:
                    cant_budin_promo = st.number_input("Porciones de budín promo:", min_value=1, value=1, step=1, key="trad_budin_cant")
                
                precio_extra_budin = cant_budin_promo * 750.0

        precio_base = float(datos_prod["precios"][tipo_presentacion] * cantidad)
        precio_total_sugerido = precio_base + precio_extra_budin
        precio_cobrado = st.number_input("Precio Total Cobrado ($):", value=precio_total_sugerido, key="trad_precio")

    costo_lote, costo_u = calcular_costo_receta(prod_sel)
    
    if "Docena (12u)" in tipo_presentacion:
        costo_total_venta = costo_u * 12 * cantidad
    elif "Media Docena (6u)" in tipo_presentacion:
        costo_total_venta = costo_u * 6 * cantidad
    elif "Porción" in tipo_presentacion or "1 Unidad" in tipo_presentacion:
        costo_total_venta = costo_u * cantidad
    else:
        costo_total_venta = costo_lote * cantidad

    if cant_budin_promo > 0 and budin_sel_promo:
        _, costo_u_budin = calcular_costo_receta(budin_sel_promo)
        costo_total_venta += (costo_u_budin * cant_budin_promo)

    ganancia_limpia = precio_cobrado - costo_total_venta

    st.markdown(f"""
        <div style="background-color: #1a232e; padding: 15px; border-radius: 12px; margin: 15px 0; border: 1px solid #2d3b4e;">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <div style="font-size: 13px; color: #a0aec0;">COSTO INSUMOS</div>
                    <div style="font-size: 22px; font-weight: bold; color: #f87171;">${costo_total_venta:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 13px; color: #a0aec0;">GANANCIA LIMPIA</div>
                    <div style="font-size: 22px; font-weight: bold; color: #4ade80;">${ganancia_limpia:,.2f}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("💾 Guardar Venta en la Nube", use_container_width=True, key="trad_save"):
        try:
            presentacion_final = tipo_presentacion
            if cant_budin_promo > 0 and budin_sel_promo:
                gusto_corto = budin_sel_promo.replace("Budin de ", "").replace("Budin ", "")
                presentacion_final += f" + {cant_budin_promo}x Budín {gusto_corto} (Promo $750)"

            registro = {
                "fecha": str(fecha_venta),
                "producto": prod_sel,
                "cantidad": int(cantidad),
                "tipo_venta": presentacion_final,
                "monto_total": float(precio_cobrado),
                "costo_total": float(costo_total_venta),
                "ganancia_limpia": float(ganancia_limpia)
            }
            supabase.table("ventas").insert(registro).execute()
            st.success("¡Venta registrada con éxito!")
            st.rerun()
        except Exception as err:
            st.error(f"Error al guardar la venta: {err}")

    st.markdown("---")
    st.subheader("📋 Historial de Ventas Registradas")

    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception as err:
        datos_ventas = []

    if datos_ventas:
        df_ventas = pd.DataFrame(datos_ventas)
        df_ventas = df_ventas.sort_values(by="fecha", ascending=False)
        
        for idx, row in df_ventas.iterrows():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div style="background-color: #1a232a; padding: 12px; border-radius: 8px; border-left: 4px solid #72b3c2; margin-bottom: 8px; font-size: 15px;">
                    📅 <b>{row.get('fecha')}</b> | <b>{row.get('producto')}</b> ({row.get('tipo_venta')}) x{row.get('cantidad')}<br>
                    <span style="color: #93c5fd;">Total: <b>${row.get('monto_total'):,.2f}</b></span> | 
                    <span style="color: #4ade80;">Ganancia: <b>${row.get('ganancia_limpia'):,.2f}</b></span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("🗑️", key=f"del_{row.get('id')}"):
                    supabase.table("ventas").delete().eq("id", row.get("id")).execute()
                    st.success("Venta eliminada.")
                    st.rerun()
    else:
        st.info("✨ Aún no hay ventas registradas.")

# -------------------------------------------------------------------
# 3. PESTAÑA: MÉTRICAS Y GRÁFICOS
# -------------------------------------------------------------------
with tab_metricas:
    st.header("📈 Desempeño del Negocio")
    
    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception as err:
        datos_ventas = []

    if datos_ventas:
        df = pd.DataFrame(datos_ventas)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['Mes_Año'] = df['fecha'].dt.to_period('M').astype(str)
        df['Año'] = df['fecha'].dt.year

        hoy = pd.Timestamp.now().date()
        mes_actual = hoy.strftime('%Y-%m')
        año_actual = hoy.year

        ganancia_hoy = df[df['fecha'].dt.date == hoy]['ganancia_limpia'].sum()
        ganancia_mes = df[df['Mes_Año'] == mes_actual]['ganancia_limpia'].sum()
        ganancia_año = df[df['Año'] == año_actual]['ganancia_limpia'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Ganancia Hoy", f"${ganancia_hoy:,.2f}")
        m2.metric("Ganancia Mes Actual", f"${ganancia_mes:,.2f}")
        m3.metric("Ganancia Año Actual", f"${ganancia_año:,.2f}")

        st.markdown("---")
        st.subheader("🗓️ Comparación de Ganancias Mes a Mes")
        ventas_mensuales = df.groupby('Mes_Año')['ganancia_limpia'].sum().reset_index()
        fig_mes = px.bar(ventas_mensuales, x='Mes_Año', y='ganancia_limpia', title="Ganancia Limpia por Mes ($)", color_discrete_sequence=['#72b3c2'])
        st.plotly_chart(fig_mes, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🏆 Productos Más Vendidos")
            prod_ranking = df.groupby('producto')['cantidad'].sum().reset_index().sort_values(by='cantidad', ascending=False)
            fig_prod = px.pie(prod_ranking, values='cantidad', names='producto', title="Distribución de Ventas", hole=0.4)
            st.plotly_chart(fig_prod, use_container_width=True)

        with col_g2:
            st.subheader("💰 Productos Más Rentables")
            rent_ranking = df.groupby('producto')['ganancia_limpia'].sum().reset_index().sort_values(by='ganancia_limpia', ascending=False)
            fig_rent = px.bar(rent_ranking, x='producto', y='ganancia_limpia', title="Ganancia Neta Limpia ($)", color_discrete_sequence=['#e8a598'])
            st.plotly_chart(fig_rent, use_container_width=True)
    else:
        st.info("Todavía no hay ventas cargadas para mostrar métricas.")

# -------------------------------------------------------------------
# 4. PESTAÑA: PRODUCTOS Y RECETAS
# -------------------------------------------------------------------
with tab_productos:
    st.header("🏷️ Gestor de Productos y Recetas")
    
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["✏️ Modificar Precios", "➕ Crear Producto", "🗑️ Eliminar Producto"])

    with sub_tab1:
        if st.session_state.RECETAS:
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                prod_mod = st.selectbox("Seleccioná un Producto:", list(st.session_state.RECETAS.keys()), key="prod_mod_sel")
                pres_dict = st.session_state.RECETAS[prod_mod]["precios"]
                pres_mod = st.selectbox("Seleccioná la Presentación:", list(pres_dict.keys()), key="pres_mod_sel")
                
                precio_actual_vta = pres_dict[pres_mod]
                nuevo_precio_vta = st.number_input(f"Nuevo precio para '{prod_mod}' ({pres_mod}) ($):", value=float(precio_actual_vta), step=100.0)

                if st.button("💾 Guardar Nuevo Precio de Venta"):
                    st.session_state.RECETAS[prod_mod]["precios"][pres_mod] = nuevo_precio_vta
                    supabase.table("productos").update({"precios": st.session_state.RECETAS[prod_mod]["precios"]}).eq("nombre", prod_mod).execute()
                    st.success(f"¡Precio actualizado! **{prod_mod}** ({pres_mod}) -> **${nuevo_precio_vta:,.2f}**")
                    st.rerun()

            with col_p2:
                st.subheader("📋 Precios Actuales")
                lista_precios_resumen = []
                for p_name, p_data in st.session_state.RECETAS.items():
                    for pres_name, p_val in p_data["precios"].items():
                        lista_precios_resumen.append({"Producto": p_name, "Presentación": pres_name, "Precio ($)": f"${p_val:,.2f}"})
                st.dataframe(pd.DataFrame(lista_precios_resumen), height=400, use_container_width=True)

    with sub_tab2:
        st.subheader("➕ Agregar Producto Nuevo con Receta")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            nuevo_nombre_prod = st.text_input("Nombre del producto:")
            rinde_prod = st.number_input("Rendimiento total por receta:", min_value=1, value=8, step=1)
            tipo_rinde = st.selectbox("Unidad del rendimiento:", ["porciones", "unidades", "entero"])

        with col_n2:
            st.markdown("**Precios de Venta al Público ($):**")
            p_enteros = st.number_input("Precio Entero / Tanda Completa ($):", min_value=0.0, value=0.0, step=100.0)
            p_porcion = st.number_input("Precio por Porción / Unidad ($):", min_value=0.0, value=0.0, step=50.0)
            p_media_docena = st.number_input("Precio por Media Docena (6u) ($):", min_value=0.0, value=0.0, step=100.0)
            p_docena = st.number_input("Precio por Docena (12u) ($):", min_value=0.0, value=0.0, step=100.0)

        st.markdown("---")
        st.subheader("🥣 Ingredientes de la Receta")
        insumos_disponibles = list(st.session_state.INSUMOS.keys())
        ingredientes_seleccionados = st.multiselect("Seleccionar insumos:", insumos_disponibles)
        
        dict_ingredientes_nuevo = {}
        if ingredientes_seleccionados:
            cols_ing = st.columns(2)
            for idx, ing in enumerate(ingredientes_seleccionados):
                col_curr = cols_ing[idx % 2]
                if "(unidad)" in ing.lower():
                    cant = col_curr.number_input(f"Cantidad de '{ing}':", min_value=1, value=1, step=1, key=f"ing_new_{ing}")
                else:
                    cant = col_curr.number_input(f"Cantidad de '{ing}':", min_value=0.001, value=0.100, step=0.010, format="%.3f", key=f"ing_new_{ing}")
                dict_ingredientes_nuevo[ing] = cant

        if st.button("✨ Guardar Nuevo Producto Completo", use_container_width=True):
            if not nuevo_nombre_prod.strip():
                st.warning("Por favor, escribí un nombre válido.")
            elif not dict_ingredientes_nuevo:
                st.warning("Elegí al menos un ingrediente.")
            else:
                try:
                    dict_precios = {}
                    if p_enteros > 0: dict_precios["Entero"] = float(p_enteros)
                    if p_porcion > 0: 
                        label_p = "1 Unidad" if tipo_rinde == "unidades" else "Porción"
                        dict_precios[label_p] = float(p_porcion)
                    if p_media_docena > 0: dict_precios["Media Docena (6u)"] = float(p_media_docena)
                    if p_docena > 0: dict_precios["Docena (12u)"] = float(p_docena)

                    if not dict_precios: dict_precios["Entero"] = 0.0
                    nombre_limpio = nuevo_nombre_prod.strip()

                    nuevo_registro = {
                        "nombre": nombre_limpio,
                        "rinde": int(rinde_prod),
                        "tipo": tipo_rinde,
                        "precios": dict_precios,
                        "ingredientes": dict_ingredientes_nuevo
                    }
                    
                    supabase.table("productos").insert(nuevo_registro).execute()
                    st.session_state.RECETAS[nombre_limpio] = {
                        "rinde": int(rinde_prod),
                        "tipo": tipo_rinde,
                        "precios": dict_precios,
                        "ingredientes": dict_ingredientes_nuevo
                    }

                    modal_producto_guardado(nombre_limpio)
                except Exception as err:
                    st.error(f"Error al guardar producto: {err}")

    with sub_tab3:
        if st.session_state.RECETAS:
            prod_eliminar = st.selectbox("Producto a eliminar:", list(st.session_state.RECETAS.keys()), key="del_prod_sel")
            if st.button("🗑️ Eliminar Producto Definitivamente"):
                supabase.table("productos").delete().eq("nombre", prod_eliminar).execute()
                del st.session_state.RECETAS[prod_eliminar]
                st.success(f"Producto **'{prod_eliminar}'** eliminado.")
                st.rerun()

# -------------------------------------------------------------------
# 5. PESTAÑA: GESTOR DE INSUMOS
# -------------------------------------------------------------------
with tab_insumos:
    st.header("🛒 Gestor de Insumos y Materias Primas")
    
    col_i1, col_i2 = st.columns([2, 1])
    
    with col_i1:
        st.subheader("✏️ Editar Precio Existente")
        if st.session_state.INSUMOS:
            insumo_editar = st.selectbox("Seleccioná un insumo:", list(st.session_state.INSUMOS.keys()), key="ins_edit_sel")
            precio_actual = st.session_state.INSUMOS[insumo_editar]
            nuevo_precio = st.number_input(f"Nuevo costo de '{insumo_editar}' ($):", value=float(precio_actual), step=50.0, key="ins_edit_val")
            
            if st.button("🔄 Actualizar Costo", use_container_width=True):
                try:
                    supabase.table("insumos").update({"precio": nuevo_precio}).eq("nombre", insumo_editar).execute()
                    st.session_state.INSUMOS[insumo_editar] = nuevo_precio
                    st.success(f"Costo de **{insumo_editar}** actualizado a **${nuevo_precio:,.2f}**")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error al actualizar insumo: {err}")

        st.markdown("---")
        st.subheader("➕ Agregar Nuevo Insumo")
        nuevo_insumo_nombre = st.text_input("Nombre del nuevo insumo (ej: Esencia de Coco (litro)):", key="ins_new_name")
        nuevo_insumo_precio = st.number_input("Costo unitario / paquete ($):", min_value=0.0, value=1000.0, step=50.0, key="ins_new_val")
        
        if st.button("✨ Guardar Nuevo Insumo", use_container_width=True):
            if nuevo_insumo_nombre.strip():
                nombre_ins_limpio = nuevo_insumo_nombre.strip()
                try:
                    supabase.table("insumos").insert({"nombre": nombre_ins_limpio, "precio": float(nuevo_insumo_precio)}).execute()
                    st.session_state.INSUMOS[nombre_ins_limpio] = float(nuevo_insumo_precio)
                    st.success(f"Insumo **'{nombre_ins_limpio}'** guardado correctamente.")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error al guardar nuevo insumo: {err}")
            else:
                st.warning("Escribí un nombre válido para el insumo.")

        st.markdown("---")
        st.subheader("🗑️ Eliminar Insumo")
        if st.session_state.INSUMOS:
            insumo_eliminar = st.selectbox("Seleccioná un insumo para eliminar:", list(st.session_state.INSUMOS.keys()), key="ins_del_sel")
            if st.button("🗑️ Eliminar Insumo Definitivamente"):
                try:
                    supabase.table("insumos").delete().eq("nombre", insumo_eliminar).execute()
                    del st.session_state.INSUMOS[insumo_eliminar]
                    st.success(f"Insumo **'{insumo_eliminar}'** eliminado.")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error al eliminar insumo: {err}")

    with col_i2:
        st.subheader("📋 Lista de Insumos")
        df_insumos = pd.DataFrame([
            {"Insumo": k, "Costo ($)": f"${v:,.2f}"} 
            for k, v in st.session_state.INSUMOS.items()
        ])
        st.dataframe(df_insumos, height=600, use_container_width=True)

# -------------------------------------------------------------------
# 6. PESTAÑA: CALCULADORA RÁPIDA DE MARGENES
# -------------------------------------------------------------------
with tab_calc:
    st.header("⚙️ Calculadora Rápida de Costos y Márgenes")
    st.write("Analizá de forma rápida el costo unitario, de lote y los márgenes de ganancia proyectados para cualquier receta registrada.")

    receta_calc = st.selectbox("Seleccionar Producto / Receta a analizar:", list(st.session_state.RECETAS.keys()), key="calc_receta_sel")

    if receta_calc:
        datos_receta = st.session_state.RECETAS[receta_calc]
        costo_lote, costo_unitario = calcular_costo_receta(receta_calc)

        # Muestrario de datos clave
        c1, c2, c3 = st.columns(3)
        c1.metric("Costo Total Receta (Lote)", f"${costo_lote:,.2f}")
        c2.metric("Rendimiento Receta", f"{datos_receta['rinde']} {datos_receta['tipo']}")
        c3.metric("Costo Unitario / Porción", f"${costo_unitario:,.2f}")

        st.markdown("---")
        st.subheader("📊 Análisis por Presentación de Venta")

        lista_analisis = []
        for pres, precio_vta in datos_receta["precios"].items():
            if "Docena (12u)" in pres:
                costo_pres = costo_unitario * 12
            elif "Media Docena (6u)" in pres:
                costo_pres = costo_unitario * 6
            elif "Porción" in pres or "1 Unidad" in pres:
                costo_pres = costo_unitario
            else:
                costo_pres = costo_lote

            ganancia_pres = precio_vta - costo_pres
            margen_porcentaje = (ganancia_pres / precio_vta * 100) if precio_vta > 0 else 0.0

            lista_analisis.append({
                "Presentación": pres,
                "Precio Venta ($)": f"${precio_vta:,.2f}",
                "Costo Insumos ($)": f"${costo_pres:,.2f}",
                "Ganancia Limpia ($)": f"${ganancia_pres:,.2f}",
                "Margen Neta (%)": f"{margen_porcentaje:.1f}%"
            })

        st.dataframe(pd.DataFrame(lista_analisis), use_container_width=True)

        st.markdown("---")
        st.subheader("🥣 Detalle de Ingredientes y Costos Proporcionales")
        
        detalle_ing = []
        for ing_n, cant in datos_receta["ingredientes"].items():
            precio_unit_insumo = st.session_state.INSUMOS.get(ing_n, 0.0)
            costo_parcial = cant * precio_unit_insumo
            porcentaje_impacto = (costo_parcial / costo_lote * 100) if costo_lote > 0 else 0.0

            detalle_ing.append({
                "Ingrediente": ing_n,
                "Cantidad": cant,
                "Precio Insumo Base ($)": f"${precio_unit_insumo:,.2f}",
                "Costo en Receta ($)": f"${costo_parcial:,.2f}",
                "Impacto en Costo (%)": f"{porcentaje_impacto:.1f}%"
            })

        st.dataframe(pd.DataFrame(detalle_ing), use_container_width=True)
