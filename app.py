import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# Configuración de la página
st.set_page_config(
    page_title="Dulce Mar - Sistema Integral", 
    page_icon="🧁",
    layout="wide"
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
    st.error("Error al conectar con la base de datos. Verificá los Secrets de Streamlit.")

# Estilo visual personalizado
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #2c3e50 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Botón general */
    .stButton>button { 
        background-color: #5c9ead; 
        color: white; 
        border-radius: 8px; 
        border: none; 
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { 
        background-color: #3b6e7a; 
        color: white; 
    }

    /* Targeta resumen de venta personalizada */
    .card-resumen {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 6px solid #5c9ead;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 14px;
        color: #7f8c8d;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .card-value-costo {
        font-size: 24px;
        font-weight: bold;
        color: #e74c3c;
    }
    .card-value-ganancia {
        font-size: 24px;
        font-weight: bold;
        color: #27ae60;
    }
    </style>
""", unsafe_allow_html=True)

# 1. INSUMOS Y PRECIOS INICIALES EN SESSION_STATE
if "INSUMOS" not in st.session_state:
    st.session_state.INSUMOS = {
        "Harina Leudante (kg)": 1700.0, "Manteca (kg)": 19500.0, "Azúcar (kg)": 1400.0,
        "Dulce de Leche (kg)": 7000.0, "Huevo (unidad)": 150.0, "Aceite (litro)": 4000.0,
        "Leche (litro)": 2290.0, "Toddy cacao polvo (kg)": 12600.0, "Azucar impalpable (kg)": 4000.0,
        "Maicena (kg)": 4100.0, "Crema de Leche (litro)": 3800.0, "Caja (unidad)": 2000.0,
        "Frutos rojos (kg)": 16000.0, "Bandeja torta (unidad)": 800.0, "Naranja (kg)": 2000.0,
        "Limon (kg)": 1500.0, "Queso crema (kg)": 12000.0, "Esencia de vainilla (litro)": 22600.0,
        "Coco rallado (kg)": 43400.0, "Bolsa (unidad)": 32.0, "Bandeja (unidad)": 40.0,
        "Preparado para Chipa (kg)": 14975.0, "Banana (kg)": 3500.0, "Galletitas vainilla (kg)": 12000.0
    }

# 2. BASE DE DATOS DE RECETAS
RECETAS = {
    "Alfajores de maicena": {
        "rinde": 30, "tipo": "unidades",
        "precios": {"1 Unidad": 1500.0, "Media Docena (6u)": 7000.0, "Docena (12u)": 13000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.200, "Manteca (kg)": 0.100, "Azúcar impalpable (kg)": 0.100, "Maicena (kg)": 0.300, "Dulce de Leche (kg)": 0.250, "Huevo (unidad)": 2, "Esencia de vainilla (litro)": 0.005, "Coco rallado (kg)": 0.010, "Bolsa (unidad)": 30}
    },
    "Budin de chocolate/marmolado": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1200.0, "Entero": 14000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.300, "Toddy cacao polvo (kg)": 0.050, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.100, "Huevo (unidad)": 2, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de vainilla": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1100.0, "Entero": 13000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.300, "Esencia de vainilla (litro)": 0.005, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.100, "Huevo (unidad)": 2, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de limón": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1200.0, "Entero": 14000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.260, "Limon (kg)": 0.150, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.120, "Huevo (unidad)": 3, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de Naranja": {
        "rinde": 14, "tipo": "porciones",
        "precios": {"Porción": 1200.0, "Entero": 14000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.260, "Naranja (kg)": 0.130, "Azúcar (kg)": 0.200, "Aceite (litro)": 0.120, "Huevo (unidad)": 3, "Leche (litro)": 0.175, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Budin de banana": {
        "rinde": 9, "tipo": "porciones",
        "precios": {"Porción": 1500.0, "Entero": 12000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.150, "Banana (kg)": 0.200, "Azúcar (kg)": 0.180, "Aceite (litro)": 0.060, "Huevo (unidad)": 2, "Esencia de vainilla (litro)": 0.005, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Lemonies": {
        "rinde": 4, "tipo": "porciones",
        "precios": {"Porción": 2500.0, "Entero": 9000.0},
        "ingredientes": {"Harina Leudante (kg)": 0.140, "Limon (kg)": 0.150, "Azúcar (kg)": 0.155, "Manteca (kg)": 0.100, "Huevo (unidad)": 3, "Azucar impalpable (kg)": 0.100, "Bolsa (unidad)": 1, "Bandeja (unidad)": 2}
    },
    "Chessecake": {
        "rinde": 1, "tipo": "entero",
        "precios": {"Entero": 18000.0},
        "ingredientes": {"Frutos rojos (kg)": 0.500, "Manteca (kg)": 0.080, "Azúcar (kg)": 0.200, "Queso crema (kg)": 0.340, "Galletitas vainilla (kg)": 0.300, "Naranja (kg)": 0.130, "Crema de Leche (litro)": 0.110, "Huevo (unidad)": 3, "Bandeja (unidad)": 1, "Caja (unidad)": 1}
    },
    "Chipa": {
        "rinde": 30, "tipo": "unidades",
        "precios": {"1 Unidad": 300.0, "Media Docena (6u)": 1600.0, "Docena (12u)": 3000.0},
        "ingredientes": {"Huevo (unidad)": 3, "Preparado para Chipa (kg)": 0.400}
    }
}

def calcular_costo_receta(nombre_receta):
    receta = RECETAS[nombre_receta]
    costo_lote = sum(cant * st.session_state.INSUMOS.get(ing, 0) for ing, cant in receta["ingredientes"].items())
    costo_unitario = costo_lote / receta["rinde"]
    return costo_lote, costo_unitario

# NAVEGACIÓN
st.sidebar.title("🧁 Dulce Mar")
opcion_menu = st.sidebar.radio("Navegación:", [
    "📊 Cargar Venta Diaria", 
    "📈 Métricas y Gráficos", 
    "⚙️ Calculadora y Costo de Insumos",
    "🛒 Gestor de Precios de Insumos"
])

if opcion_menu == "📊 Cargar Venta Diaria":
    st.header("🛒 Registrar Nueva Venta")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_venta = st.date_input("Fecha:", datetime.now())
        prod_sel = st.selectbox("Producto:", list(RECETAS.keys()))
        datos_prod = RECETAS[prod_sel]
        
    with col2:
        tipo_presentacion = st.selectbox("Presentación:", list(datos_prod["precios"].keys()))
        cantidad = st.number_input("Cantidad vendida:", min_value=1, value=1, step=1)
        precio_cobrado = st.number_input("Precio Total Cobrado ($):", value=float(datos_prod["precios"][tipo_presentacion] * cantidad))

    costo_lote, costo_u = calcular_costo_receta(prod_sel)
    
    if "Docena (12u)" in tipo_presentacion:
        costo_total_venta = costo_u * 12 * cantidad
    elif "Media Docena (6u)" in tipo_presentacion:
        costo_total_venta = costo_u * 6 * cantidad
    elif "Porción" in tipo_presentacion or "1 Unidad" in tipo_presentacion:
        costo_total_venta = costo_u * cantidad
    else:
        costo_total_venta = costo_lote * cantidad

    ganancia_limpia = precio_cobrado - costo_total_venta

    # --- NUEVO DISEÑO VISUAL PARA EL RESUMEN DE MARGEN ---
    st.markdown(f"""
        <div class="card-resumen">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <div class="card-title">📦 Costo Estimado Insumos</div>
                    <div class="card-value-costo">${costo_total_venta:,.2f}</div>
                </div>
                <div style="border-left: 1px solid #e0e0e0; height: 50px;"></div>
                <div>
                    <div class="card-title">💵 Ganancia Limpia Estimada</div>
                    <div class="card-value-ganancia">${ganancia_limpia:,.2f}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("💾 Guardar Venta en la Nube", use_container_width=True):
        try:
            registro = {
                "fecha": str(fecha_venta),
                "producto": prod_sel,
                "cantidad": int(cantidad),
                "tipo_venta": tipo_presentacion,
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

    # Búsqueda universal sin depender exclusivamente de created_at
    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception as err:
        datos_ventas = []

    if datos_ventas:
        # Ordenamos localmente por fecha (de más reciente a más vieja)
        df_ventas = pd.DataFrame(datos_ventas)
        df_ventas = df_ventas.sort_values(by="fecha", ascending=False)
        
        for idx, row in df_ventas.iterrows():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.write(f"📅 **{row.get('fecha')}** | **{row.get('producto')}** ({row.get('tipo_venta')}) x{row.get('cantidad')} — Total: **${row.get('monto_total'):,.2f}** | Ganancia: **${row.get('ganancia_limpia'):,.2f}**")
            with col_btn:
                if st.button("🗑️ Borrar", key=f"del_{row.get('id')}"):
                    supabase.table("ventas").delete().eq("id", row.get("id")).execute()
                    st.success("Venta eliminada.")
                    st.rerun()
            st.divider()
    else:
        st.info("Aún no hay ventas registradas en el historial.")

elif opcion_menu == "📈 Métricas y Gráficos":
    st.header("📈 Desempeño del Negocio")
    
    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception as err:
        st.error(f"No se pudieron cargar los datos de Supabase: {err}")
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
        fig_mes = px.bar(ventas_mensuales, x='Mes_Año', y='ganancia_limpia', 
                         title="Ganancia Limpia por Mes ($)",
                         labels={'Mes_Año': 'Mes', 'ganancia_limpia': 'Ganancia ($)'},
                         color_discrete_sequence=['#5c9ead'])
        st.plotly_chart(fig_mes, use_container_width=True)

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🏆 Productos Más Vendidos")
            prod_ranking = df.groupby('producto')['cantidad'].sum().reset_index().sort_values(by='cantidad', ascending=False)
            fig_prod = px.pie(prod_ranking, values='cantidad', names='producto', title="Distribución de Ventas por Producto", hole=0.4)
            st.plotly_chart(fig_prod, use_container_width=True)

        with col_g2:
            st.subheader("💰 Productos Más Rentables (Ganancia Neta Acumulada)")
            rent_ranking = df.groupby('producto')['ganancia_limpia'].sum().reset_index().sort_values(by='ganancia_limpia', ascending=False)
            fig_rent = px.bar(rent_ranking, x='producto', y='ganancia_limpia', title="Ganancia Neta Limpia Aportada ($)", color_discrete_sequence=['#a8dadc'])
            st.plotly_chart(fig_rent, use_container_width=True)

    else:
        st.info("Todavía no hay ventas cargadas en la base de datos o la tabla está vacía. ¡Cargá tu primera venta en la pestaña de la izquierda!")

elif opcion_menu == "⚙️ Calculadora y Costo de Insumos":
    st.header("⚙️ Calculadora de Costos y Margen por Producto")
    
    receta_seleccionada = st.selectbox("Elegí un producto:", list(RECETAS.keys()))
    receta = RECETAS[receta_seleccionada]
    
    costo_lote, costo_u = calcular_costo_receta(receta_seleccionada)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.subheader("📋 Resumen de Costos")
        st.write(f"• **Costo total del lote/receta:** ${costo_lote:,.2f}")
        st.write(f"• **Rendimiento:** {receta['rinde']} {receta['tipo']}")
        st.write(f"• **Costo unitario por {receta['tipo'][:-1] if receta['tipo'].endswith('s') else receta['tipo']}:** ${costo_u:,.2f}")

    with col_c2:
        st.subheader("💵 Margen de Ganancia Neta por Presentación")
        tabla_margenes = []
        for pres, precio_vta in receta["precios"].items():
            if "Docena (12u)" in pres:
                c_item = costo_u * 12
            elif "Media Docena (6u)" in pres:
                c_item = costo_u * 6
            elif "Porción" in pres or "1 Unidad" in pres:
                c_item = costo_u
            else:
                c_item = costo_lote
            
            gan_limpia = precio_vta - c_item
            m_porcentaje = (gan_limpia / precio_vta) * 100 if precio_vta > 0 else 0
            
            tabla_margenes.append({
                "Presentación": pres,
                "Precio Venta": f"${precio_vta:,.2f}",
                "Costo Insumos": f"${c_item:,.2f}",
                "Ganancia Neta Limpia": f"${gan_limpia:,.2f}",
                "Margen (%)": f"{m_porcentaje:.1f}%"
            })
        st.table(pd.DataFrame(tabla_margenes))

    st.subheader("🛒 Desglose de Insumos de la Receta")
    desglose = []
    for ing, cant in receta["ingredientes"].items():
        precio_u_ing = st.session_state.INSUMOS.get(ing, 0)
        costo_total_ing = cant * precio_u_ing
        desglose.append({
            "Insumo": ing,
            "Cantidad utilizada": cant,
            "Precio Insumo ($)": f"${precio_u_ing:,.2f}",
            "Costo en la receta ($)": f"${costo_total_ing:,.2f}"
        })
    st.table(pd.DataFrame(desglose))

elif opcion_menu == "🛒 Gestor de Precios de Insumos":
    st.header("🛒 Gestor y Modificador de Precios de Insumos")
    st.write("Modificá acá los valores cuando suban o bajen los precios de la materia prima. Se recalcularán los costos de las recetas en tiempo real.")

    col_i1, col_i2 = st.columns([2, 1])
    
    with col_i1:
        insumo_editar = st.selectbox("Seleccioná un insumo para modificar:", list(st.session_state.INSUMOS.keys()))
        precio_actual = st.session_state.INSUMOS[insumo_editar]
        nuevo_precio = st.number_input(f"Nuevo precio para '{insumo_editar}' ($):", value=float(precio_actual), step=100.0)
        
        if st.button("🔄 Actualizar Precio de Insumo"):
            st.session_state.INSUMOS[insumo_editar] = nuevo_precio
            st.success(f"¡Precio de **{insumo_editar}** actualizado a **${nuevo_precio:,.2f}**!")

    with col_i2:
        st.subheader("📋 Precios Actuales")
        df_ins = pd.DataFrame(list(st.session_state.INSUMOS.items()), columns=["Insumo", "Precio ($)"])
        st.dataframe(df_ins, height=400, use_container_width=True)
