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

# Estilo visual adaptado al modo oscuro
st.markdown("""
    <style>
    /* Títulos en Celeste Pastel */
    h1, h2, h3 { 
        color: #72b3c2 !important; 
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    
    /* Botón Principal */
    .stButton>button { 
        background-color: #5c9ead; 
        color: white; 
        border-radius: 8px; 
        border: none; 
        font-weight: 600;
        font-size: 16px;
        padding: 0.6rem 1rem;
    }
    .stButton>button:hover { 
        background-color: #4a8b9a; 
        color: white; 
    }

    /* Tarjeta resumen */
    .card-resumen {
        background-color: #1e2d38;
        border-radius: 12px;
        padding: 22px;
        border: 1px solid #3a5366;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 14px;
        color: #93c5fd;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .card-value-costo {
        font-size: 26px;
        font-weight: bold;
        color: #f87171;
    }
    .card-value-ganancia {
        font-size: 26px;
        font-weight: bold;
        color: #4ade80;
    }

    /* Estilo para las filas e historial de ventas */
    .venta-item {
        background-color: #1a232a;
        padding: 14px 18px;
        border-radius: 8px;
        border-left: 4px solid #72b3c2;
        margin-bottom: 10px;
        color: #e0f2fe;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. INSUMOS EN SESSION_STATE
if "INSUMOS" not in st.session_state:
    st.session_state.INSUMOS = {
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

# 2. RECETAS Y PRECIOS DE VENTA EN SESSION_STATE
if "RECETAS" not in st.session_state:
    st.session_state.RECETAS = {
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

def calcular_costo_receta(nombre_receta):
    receta = st.session_state.RECETAS[nombre_receta]
    costo_lote = sum(cant * st.session_state.INSUMOS.get(ing, 0) for ing, cant in receta["ingredientes"].items())
    costo_unitario = costo_lote / receta["rinde"]
    return costo_lote, costo_unitario

# NAVEGACIÓN
st.sidebar.title("🧁 Dulce Mar")
opcion_menu = st.sidebar.radio("Navegación:", [
    "📊 Cargar Venta Diaria", 
    "📈 Métricas y Gráficos", 
    "🏷️ Modificar Precios de Productos",
    "🛒 Gestor de Precios de Insumos",
    "⚙️ Calculadora y Costo de Insumos"
])

if opcion_menu == "📊 Cargar Venta Diaria":
    st.header("🛒 Registrar Nueva Venta")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_venta = st.date_input("Fecha:", datetime.now())
        prod_sel = st.selectbox("Producto:", list(st.session_state.RECETAS.keys()))
        datos_prod = st.session_state.RECETAS[prod_sel]
        
    with col2:
        tipo_presentacion = st.selectbox("Presentación:", list(datos_prod["precios"].keys()))
        cantidad = st.number_input("Cantidad vendida:", min_value=1, value=1, step=1)
        
        # PROMO CAFÉ + BUDÍN
        cant_budin_promo = 0
        budin_sel_promo = None
        precio_extra_budin = 0.0
        
        if "Cafe" in prod_sel:
            st.markdown("---")
            agregar_promo = st.checkbox("☕ Promo: ¡Agregar porción de Budín a $750!")
            if agregar_promo:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    budines_disponibles = [p for p in st.session_state.RECETAS.keys() if "Budin" in p]
                    budin_sel_promo = st.selectbox("Gusto del budín:", budines_disponibles)
                with col_b2:
                    cant_budin_promo = st.number_input("Porciones de budín promo:", min_value=1, value=1, step=1)
                
                precio_extra_budin = cant_budin_promo * 750.0

        precio_base = float(datos_prod["precios"][tipo_presentacion] * cantidad)
        precio_total_sugerido = precio_base + precio_extra_budin
        precio_cobrado = st.number_input("Precio Total Cobrado ($):", value=precio_total_sugerido)

    # CÁLCULO DE COSTOS
    costo_lote, costo_u = calcular_costo_receta(prod_sel)
    
    if "Docena (12u)" in tipo_presentacion:
        costo_total_venta = costo_u * 12 * cantidad
    elif "Media Docena (6u)" in tipo_presentacion:
        costo_total_venta = costo_u * 6 * cantidad
    elif "Porción" in tipo_presentacion or "1 Unidad" in tipo_presentacion:
        costo_total_venta = costo_u * cantidad
    else:
        costo_total_venta = costo_lote * cantidad

    # Si agregó budín en promo, sumamos su costo de insumos real
    if cant_budin_promo > 0 and budin_sel_promo:
        _, costo_u_budin = calcular_costo_receta(budin_sel_promo)
        costo_total_venta += (costo_u_budin * cant_budin_promo)

    ganancia_limpia = precio_cobrado - costo_total_venta

    st.markdown(f"""
        <div class="card-resumen">
            <div style="display: flex; justify-content: space-around; text-align: center; align-items: center;">
                <div>
                    <div class="card-title">📦 COSTO ESTIMADO INSUMOS</div>
                    <div class="card-value-costo">${costo_total_venta:,.2f}</div>
                </div>
                <div style="border-left: 2px solid #3a5366; height: 45px;"></div>
                <div>
                    <div class="card-title">💵 GANANCIA LIMPIA ESTIMADA</div>
                    <div class="card-value-ganancia">${ganancia_limpia:,.2f}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("💾 Guardar Venta en la Nube", use_container_width=True):
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
                <div class="venta-item">
                    📅 <b>{row.get('fecha')}</b> | <b>{row.get('producto')}</b> ({row.get('tipo_venta')}) x{row.get('cantidad')}<br>
                    <span style="color: #93c5fd;">Total: <b>${row.get('monto_total'):,.2f}</b></span> | 
                    <span style="color: #4ade80;">Ganancia: <b>${row.get('ganancia_limpia'):,.2f}</b></span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("🗑️ Borrar", key=f"del_{row.get('id')}"):
                    supabase.table("ventas").delete().eq("id", row.get("id")).execute()
                    st.success("Venta eliminada.")
                    st.rerun()
    else:
        st.markdown("<p style='color: #e0f2fe; font-size: 18px;'>✨ Aún no hay ventas registradas.</p>", unsafe_allow_html=True)

elif opcion_menu == "📈 Métricas y Gráficos":
    st.header("📈 Desempeño del Negocio")
    
    try:
        respuesta = supabase.table("ventas").select("*").execute()
        datos_ventas = respuesta.data
    except Exception as err:
        st.error(f"No se pudieron cargar los datos: {err}")
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
            fig_rent = px.bar(rent_ranking, x='producto', y='ganancia_limpia', title="Ganancia Neta Limpia ($)", color_discrete_sequence=['#5c9ead'])
            st.plotly_chart(fig_rent, use_container_width=True)

    else:
        st.markdown("<p style='color: #e0f2fe;'>Todavía no hay ventas cargadas.</p>", unsafe_allow_html=True)

elif opcion_menu == "🏷️ Modificar Precios de Productos":
    st.header("🏷️ Cambiar Precio de Venta al Público")
    st.write("Acá podés actualizar fácilmente cuánto cobrás cada producto o presentación cuando hay un aumento.")

    col_p1, col_p2 = st.columns([2, 1])

    with col_p1:
        prod_mod = st.selectbox("Seleccioná un Producto:", list(st.session_state.RECETAS.keys()))
        pres_dict = st.session_state.RECETAS[prod_mod]["precios"]
        pres_mod = st.selectbox("Seleccioná la Presentación:", list(pres_dict.keys()))
        
        precio_actual_vta = pres_dict[pres_mod]
        nuevo_precio_vta = st.number_input(f"Nuevo precio para '{prod_mod}' ({pres_mod}) ($):", value=float(precio_actual_vta), step=100.0)

        if st.button("💾 Guardar Nuevo Precio de Venta"):
            st.session_state.RECETAS[prod_mod]["precios"][pres_mod] = nuevo_precio_vta
            st.success(f"¡Precio actualizado! **{prod_mod}** ({pres_mod}) ahora vale **${nuevo_precio_vta:,.2f}**.")

    with col_p2:
        st.subheader("📋 Precios Actuales de Venta")
        lista_precios_resumen = []
        for p_name, p_data in st.session_state.RECETAS.items():
            for pres_name, p_val in p_data["precios"].items():
                lista_precios_resumen.append({"Producto": p_name, "Presentación": pres_name, "Precio ($)": f"${p_val:,.2f}"})
        st.dataframe(pd.DataFrame(lista_precios_resumen), height=450, use_container_width=True)

elif opcion_menu == "🛒 Gestor de Precios de Insumos":
    st.header("🛒 Gestor de Insumos y Materias Primas")
    st.write("Modificá los costos cuando compres más caro o agregá nuevos insumos a la lista.")

    col_i1, col_i2 = st.columns([2, 1])
    
    with col_i1:
        st.subheader("✏️ Editar Precio Existente")
        insumo_editar = st.selectbox("Seleccioná un insumo:", list(st.session_state.INSUMOS.keys()))
        precio_actual = st.session_state.INSUMOS[insumo_editar]
        nuevo_precio = st.number_input(f"Nuevo costo de '{insumo_editar}' ($):", value=float(precio_actual), step=50.0)
        
        if st.button("🔄 Actualizar Costo Insumo"):
            st.session_state.INSUMOS[insumo_editar] = nuevo_precio
            st.success(f"¡Costo de **{insumo_editar}** actualizado a **${nuevo_precio:,.2f}**!")

        st.markdown("---")
        st.subheader("➕ Agregar Nuevo Insumo")
        nuevo_nombre_insumo = st.text_input("Nombre del insumo (ej: Durazno en lata):")
        nuevo_precio_insumo = st.number_input("Costo del insumo ($):", value=0.0, step=50.0)
        if st.button("➕ Crear Insumo"):
            if nuevo_nombre_insumo.strip() != "":
                st.session_state.INSUMOS[nuevo_nombre_insumo.strip()] = nuevo_precio_insumo
                st.success(f"¡Insumo **'{nuevo_nombre_insumo}'** creado con éxito!")
                st.rerun()
            else:
                st.warning("Escribí un nombre válido para el insumo.")

    with col_i2:
        st.subheader("📋 Lista de Insumos")
        df_ins = pd.DataFrame(list(st.session_state.INSUMOS.items()), columns=["Insumo", "Costo ($)"])
        st.dataframe(df_ins, height=450, use_container_width=True)

elif opcion_menu == "⚙️ Calculadora y Costo de Insumos":
    st.header("⚙️ Calculadora y Márgenes por Producto")
    
    receta_seleccionada = st.selectbox("Elegí un producto:", list(st.session_state.RECETAS.keys()))
    receta = st.session_state.RECETAS[receta_seleccionada]
    
    costo_lote, costo_u = calcular_costo_receta(receta_seleccionada)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.subheader("📋 Resumen de Costos")
        st.write(f"• **Costo total del lote/receta:** ${costo_lote:,.2f}")
        st.write(f"• **Rendimiento:** {receta['rinde']} {receta['tipo']}")
        st.write(f"• **Costo unitario:** ${costo_u:,.2f}")

    with col_c2:
        st.subheader("💵 Margen de Ganancia por Presentación")
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
                "Ganancia Limpia": f"${gan_limpia:,.2f}",
                "Margen (%)": f"{m_porcentaje:.1f}%"
            })
        st.table(pd.DataFrame(tabla_margenes))

    st.subheader("🛒 Desglose de Insumos")
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
