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

# Estilo visual
st.markdown("""
    <style>
    .main { background-color: #f4f9f9; }
    h1, h2, h3 { color: #5c9ead !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { background-color: #a8dadc; color: #1d3557; border-radius: 10px; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #457b9d; color: white; }
    </style>
""", unsafe_allow_html=True)

# 1. BASE DE DATOS DE INSUMOS
INSUMOS = {
    "Harina Leudante (kg)": 1700, "Manteca (kg)": 19500, "Azúcar (kg)": 1400,
    "Dulce de Leche (kg)": 7000, "Huevo (unidad)": 150, "Aceite (litro)": 4000,
    "Leche (litro)": 2290, "Toddy cacao polvo (kg)": 12600, "Azucar impalpable (kg)": 4000,
    "Maicena (kg)": 4100, "Crema de Leche (litro)": 3800, "Caja (unidad)": 2000,
    "Frutos rojos (kg)": 16000, "Bandeja torta (unidad)": 800, "Naranja (kg)": 2000,
    "Limon (kg)": 1500, "Queso crema (kg)": 12000, "Esencia de vainilla (litro)": 22600,
    "Coco rallado (kg)": 43400, "Bolsa (unidad)": 32, "Bandeja (unidad)": 40,
    "Preparado para Chipa (kg)": 14975, "Banana (kg)": 3500, "Galletitas vainilla (kg)": 12000
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
    costo_lote = sum(cant * INSUMOS.get(ing, 0) for ing, cant in receta["ingredientes"].items())
    costo_unitario = costo_lote / receta["rinde"]
    return costo_lote, costo_unitario

# NAVEGACIÓN
st.sidebar.title("🧁 Dulce Mar")
opcion_menu = st.sidebar.radio("Navegación:", ["📊 Cargar Venta Diaria", "📈 Métricas y Gráficos", "⚙️ Calculadora de Costos"])

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

    if st.button("💾 Guardar Venta en la Nube"):
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
        st.success("¡Venta registrada con éxito y guardada en la nube!")

elif opcion_menu == "📈 Métricas y Gráficos":
    st.header("📈 Desempeño del Negocio")
    
    respuesta = supabase.table("ventas").select("*").execute()
    datos_ventas = respuesta.data

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
            st.subheader("💰 Productos Más Rentables")
            rent_ranking = df.groupby('producto')['ganancia_limpia'].sum().reset_index().sort_values(by='ganancia_limpia', ascending=False)
            fig_rent = px.bar(rent_ranking, x='producto', y='ganancia_limpia', title="Ganancia Aportada por Producto ($)", color_discrete_sequence=['#a8dadc'])
            st.plotly_chart(fig_rent, use_container_width=True)

    else:
        st.info("Todavía no hay ventas cargadas en la base de datos.")

else:
    st.header("⚙️ Calculadora de Costos")
    receta_seleccionada = st.selectbox("Elegí un producto:", list(RECETAS.keys()))
    costo_lote, costo_u = calcular_costo_receta(receta_seleccionada)
    st.write(f"• Costo total del lote: **${costo_lote:,.2f}**")
    st.write(f"• Costo por unidad/porción: **${costo_u:,.2f}**")
