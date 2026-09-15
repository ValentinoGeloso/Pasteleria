import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(
    page_title="Dulce Mar - App Pasteleria", 
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
    except Exception:
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
    except Exception:
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

# Estilos CSS táctiles optimizados + Script de desactivación de teclado móvil
st.markdown("""
    <style>
    .stApp {
        background-color: #12181f;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    .brand-header {
        background: linear-gradient(135deg, #e8a598 0%, #72b3c2 100%);
        padding: 12px 15px;
        border-radius: 12px;
        color: #12181f;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .brand-header h1 {
        margin: 0;
        font-size: 22px;
        font-weight: 800;
        color: #12181f !important;
    }
    .brand-header p {
        margin: 2px 0 0 0;
        font-size: 12px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a232e;
        border-radius: 8px;
        color: #a0aec0;
        padding: 8px 12px;
        font-weight: 600;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #72b3c2 !important;
        color: #12181f !important;
    }
    
    /* BLOQUEO DEL TECLADO VIRTUAL EN SELECTBOX */
    div[data-baseweb="select"] input {
        inputmode: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }
    </style>

    <script>
    // Inhabilitar entrada de texto al enfocar selectores en celulares
    document.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' && e.target.closest('div[data-baseweb="select"]')) {
            e.target.setAttribute('readonly', 'readonly');
            e.target.setAttribute('inputmode', 'none');
        }
    });
    </script>
""", unsafe_allow_html=True)

# BANNER SUPERIOR DE LA APP
st.markdown("""
    <div class="brand-header">
        <h1>🧁 DULCE MAR</h1>
        <p>Sistema POS de Gestión y Ventas</p>
    </div>
""", unsafe_allow_html=True)

# NAVEGACIÓN PRINCIPAL
tab_ventas, tab_metricas, tab_productos, tab_insumos = st.tabs([
    "🛒 Registrar Venta", 
    "📈 Métricas y Progreso", 
    "🏷️ Productos",
    "🛒 Insumos"
])

# -------------------------------------------------------------------
# 1. PESTAÑA: REGISTRAR VENTA (DESPLEGABLE TÁCTIL SIN TECLADO)
# -------------------------------------------------------------------
with tab_ventas:
    st.subheader("🛒 Registro de Venta")
    fecha_venta = st.date_input("Fecha:", datetime.now(), key="trad_fecha")
    
    lista_productos = list(st.session_state.RECETAS.keys())
    
    # Selector de productos en 1 sola fila táctil limpia
    prod_sel = st.selectbox("Seleccionar Producto:", lista_productos, key="select_prod_tactil")
    
    datos_prod = st.session_state.RECETAS[prod_sel]
    
    tipo_presentacion = st.selectbox("Presentación:", list(datos_prod["precios"].keys()), key="select_pres_tactil")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1, key="trad_cant")
        
    cant_budin_promo = 0
    budin_sel_promo = None
    precio_extra_budin = 0.0
    
    if "Cafe" in prod_sel:
        st.markdown("---")
        agregar_promo = st.checkbox("☕ Promo: ¡Agregar porción de Budín a $750!", key="trad_promo")
        if agregar_promo:
            budines_disponibles = [p for p in st.session_state.RECETAS.keys() if "Budin" in p]
            budin_sel_promo = st.selectbox("Sabor Budín Promo:", budines_disponibles, key="trad_budin_select")
            cant_budin_promo = st.number_input("Cantidad porciones promo:", min_value=1, value=1, step=1, key="trad_budin_cant")
            precio_extra_budin = cant_budin_promo * 750.0

    precio_base = float(datos_prod["precios"][tipo_presentacion] * cantidad)
    precio_total_sugerido = precio_base + precio_extra_budin
    
    with col_c2:
        precio_cobrado = st.number_input("Precio Cobrado ($):", value=precio_total_sugerido, step=100.0, key="trad_precio")

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
        <div style="background-color: #1a232e; padding: 12px; border-radius: 10px; margin: 12px 0; border: 1px solid #2d3b4e;">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <div style="font-size: 11px; color: #a0aec0;">COSTO INSUMOS</div>
                    <div style="font-size: 18px; font-weight: bold; color: #f87171;">${costo_total_venta:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #a0aec0;">GANANCIA LIMPIA</div>
                    <div style="font-size: 18px; font-weight: bold; color: #4ade80;">${ganancia_limpia:,.2f}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 REGISTRAR VENTA AHORA", use_container_width=True, type="primary", key="trad_save"):
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
    st.subheader("📋 Historial de Ventas")

    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception:
        datos_ventas = []

    if datos_ventas:
        df_ventas = pd.DataFrame(datos_ventas).sort_values(by="fecha", ascending=False)
        for idx, row in df_ventas.iterrows():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div style="background-color: #1a232a; padding: 10px; border-radius: 8px; border-left: 4px solid #72b3c2; margin-bottom: 8px; font-size: 13px;">
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
        st.info("✨ No hay ventas registradas aún.")

# -------------------------------------------------------------------
# 2. PESTAÑA: MÉTRICAS (AUTOESCALA FIJA + DESGLOSE DÍA A DÍA)
# -------------------------------------------------------------------
with tab_metricas:
    st.header("📈 Progreso y Métricas de Ventas")
    
    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception:
        datos_ventas = []

    if datos_ventas:
        df = pd.DataFrame(datos_ventas)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['Fecha_Dia'] = df['fecha'].dt.strftime('%Y-%m-%d')
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
        
        modo_progreso = st.radio("Ver Progreso por:", ["Día a Día 📅", "Mes a Mes 🗓️"], horizontal=True, key="modo_progreso")

        if "Día a Día" in modo_progreso:
            st.subheader("📅 Ganancia Limpia Día a Día")
            ventas_diarias = df.groupby('Fecha_Dia')['ganancia_limpia'].sum().reset_index()
            fig_dia = px.line(ventas_diarias, x='Fecha_Dia', y='ganancia_limpia', markers=True, title="Ganancia Diaria ($)", color_discrete_sequence=['#4ade80'])
            fig_dia.update_xaxes(fixedrange=True)
            fig_dia.update_yaxes(fixedrange=True)
            st.plotly_chart(fig_dia, use_container_width=True, config={'displayModeBar': False})

        else:
            st.subheader("🗓️ Ganancia Limpia Mes a Mes")
            ventas_mensuales = df.groupby('Mes_Año')['ganancia_limpia'].sum().reset_index()
            fig_mes = px.bar(ventas_mensuales, x='Mes_Año', y='ganancia_limpia', title="Ganancia Mensual ($)", color_discrete_sequence=['#72b3c2'])
            fig_mes.update_xaxes(fixedrange=True)
            fig_mes.update_yaxes(fixedrange=True)
            st.plotly_chart(fig_mes, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🏆 Productos Más Vendidos")
            prod_ranking = df.groupby('producto')['cantidad'].sum().reset_index().sort_values(by='cantidad', ascending=False)
            fig_prod = px.pie(prod_ranking, values='cantidad', names='producto', title="Distribución de Ventas", hole=0.4)
            st.plotly_chart(fig_prod, use_container_width=True, config={'displayModeBar': False})

        with col_g2:
            st.subheader("💰 Productos Más Rentables")
            rent_ranking = df.groupby('producto')['ganancia_limpia'].sum().reset_index().sort_values(by='ganancia_limpia', ascending=False)
            fig_rent = px.bar(rent_ranking, x='producto', y='ganancia_limpia', title="Ganancia Neta ($)", color_discrete_sequence=['#e8a598'])
            fig_rent.update_xaxes(fixedrange=True)
            fig_rent.update_yaxes(fixedrange=True)
            st.plotly_chart(fig_rent, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Todavía no hay ventas cargadas para mostrar métricas.")

# -------------------------------------------------------------------
# 3. PESTAÑA: PRODUCTOS Y RECETAS
# -------------------------------------------------------------------
with tab_productos:
    st.header("🏷️ Gestor de Productos y Recetas")
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["✏️ Precios", "➕ Crear Producto", "🗑️ Eliminar Producto"])

    with sub_tab1:
        if st.session_state.RECETAS:
            prod_mod = st.selectbox("Producto a modificar:", list(st.session_state.RECETAS.keys()), key="select_prod_mod")
            pres_dict = st.session_state.RECETAS[prod_mod]["precios"]
            
            pres_mod = st.selectbox("Presentación a modificar:", list(pres_dict.keys()), key="select_pres_mod")
            
            precio_actual_vta = pres_dict[pres_mod]
            nuevo_precio_vta = st.number_input(f"Nuevo precio para '{prod_mod}' ({pres_mod}) ($):", value=float(precio_actual_vta), step=100.0)

            if st.button("💾 Guardar Nuevo Precio", use_container_width=True):
                st.session_state.RECETAS[prod_mod]["precios"][pres_mod] = nuevo_precio_vta
                supabase.table("productos").update({"precios": st.session_state.RECETAS[prod_mod]["precios"]}).eq("nombre", prod_mod).execute()
                st.success(f"¡Precio actualizado! **{prod_mod}** ({pres_mod}) -> **${nuevo_precio_vta:,.2f}**")
                st.rerun()

    with sub_tab2:
        st.subheader("➕ Agregar Producto Nuevo")
        nuevo_nombre_prod = st.text_input("Nombre del producto:")
        rinde_prod = st.number_input("Rendimiento total:", min_value=1, value=8, step=1)
        tipo_rinde = st.selectbox("Unidad del rendimiento:", ["porciones", "unidades", "entero"])

        st.markdown("**Precios de Venta ($):**")
        p_enteros = st.number_input("Precio Entero ($):", min_value=0.0, value=0.0, step=100.0)
        p_porcion = st.number_input("Precio por Porción / Unidad ($):", min_value=0.0, value=0.0, step=50.0)
        p_media_docena = st.number_input("Precio Media Docena (6u) ($):", min_value=0.0, value=0.0, step=100.0)
        p_docena = st.number_input("Precio Docena (12u) ($):", min_value=0.0, value=0.0, step=100.0)

        st.markdown("---")
        st.subheader("🥣 Ingredientes de la Receta")
        insumos_disponibles = list(st.session_state.INSUMOS.keys())
        ingredientes_seleccionados = st.multiselect("Seleccionar insumos:", insumos_disponibles)
        
        dict_ingredientes_nuevo = {}
        if ingredientes_seleccionados:
            for ing in ingredientes_seleccionados:
                if "(unidad)" in ing.lower():
                    cant = st.number_input(f"Cantidad de '{ing}':", min_value=1, value=1, step=1, key=f"ing_new_{ing}")
                else:
                    cant = st.number_input(f"Cantidad de '{ing}':", min_value=0.001, value=0.100, step=0.010, format="%.3f", key=f"ing_new_{ing}")
                dict_ingredientes_nuevo[ing] = cant

        if st.button("✨ Guardar Nuevo Producto", use_container_width=True):
            if not nuevo_nombre_prod.strip():
                st.warning("Escribí un nombre válido.")
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
                    st.success(f"¡Producto **{nombre_limpio}** guardado exitosamente!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error al guardar producto: {err}")

    with sub_tab3:
        if st.session_state.RECETAS:
            prod_eliminar = st.selectbox("Producto a eliminar:", list(st.session_state.RECETAS.keys()), key="select_del_prod")
            if st.button("🗑️ Eliminar Producto Definitivamente", use_container_width=True):
                supabase.table("productos").delete().eq("nombre", prod_eliminar).execute()
                del st.session_state.RECETAS[prod_eliminar]
                st.success(f"Producto **'{prod_eliminar}'** eliminado.")
                st.rerun()

# -------------------------------------------------------------------
# 4. PESTAÑA: GESTOR DE INSUMOS
# -------------------------------------------------------------------
with tab_insumos:
    st.header("🛒 Gestor de Insumos")
    if st.session_state.INSUMOS:
        insumo_editar = st.selectbox("Seleccioná un insumo a editar:", list(st.session_state.INSUMOS.keys()), key="select_ins_edit")
        precio_actual = st.session_state.INSUMOS[insumo_editar]
        nuevo_precio = st.number_input(f"Nuevo costo de '{insumo_editar}' ($):", value=float(precio_actual), step=50.0)
        
        if st.button("🔄 Actualizar Costo Insumo", use_container_width=True):
            supabase.table("insumos").update({"precio": nuevo_precio}).eq("nombre", insumo_editar).execute()
            st.session_state.INSUMOS[insumo_editar] = nuevo_precio
            st.success(f"Costo de **{insumo_editar}** actualizado a **${nuevo_precio:,.2f}**")
            st.rerun()
