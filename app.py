import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Sistema de Pastelería", page_icon="🍰")
st.title("🍰 Sistema de Costos y Recetas")

# 1. BASE DE DATOS DE INSUMOS (Precios por kg / litro / unidad)
INSUMOS = {
    "Harina Leudante (kg)": 1700,
    "Manteca (kg)": 19500,
    "Azúcar (kg)": 1400,
    "Dulce de Leche (kg)": 7000,
    "Huevo (unidad)": 150,
    "Aceite (litro)": 4000,
    "Leche (litro)": 2290,
    "Toddy cacao polvo (kg)": 12600,
    "Azucar impalpable (kg)": 4000,
    "Maicena (kg)": 4100,
    "Crema de Leche (litro)": 3800,
    "Caja (unidad)": 2000,
    "Frutos rojos (kg)": 16000,
    "Bandeja torta (unidad)": 800,
    "Naranja (kg)": 2000,
    "Queso crema (kg)": 12000,
    "Esencia de vainilla (litro)": 22600,
    "Coco rallado (kg)": 43400,
    "Bolsa (unidad)": 32,
    "Bandeja (unidad)": 40,
    "Preparado para Chipa (kg)": 14975,
    "Galletitas vainilla (kg)": 12000
}

# 2. BASE DE DATOS DE RECETAS (Cantidades por receta)
RECETAS = {
    "Budin de chocolate/marmolado": {
        "Harina Leudante (kg)": 0.300,
        "Toddy cacao polvo (kg)": 0.050,
        "Azúcar (kg)": 0.200,
        "Aceite (litro)": 0.100,
        "Huevo (unidad)": 2,
        "Leche (litro)": 0.175,
        "Bolsa (unidad)": 1,
        "Bandeja (unidad)": 2
    },
    "Chessecake": {
        "Frutos rojos (kg)": 0.500,
        "Manteca (kg)": 0.080,
        "Azúcar (kg)": 0.200,
        "Queso crema (kg)": 0.340,
        "Galletitas vainilla (kg)": 0.300,
        "Naranja (kg)": 0.130,
        "Crema de Leche (litro)": 0.110,
        "Huevo (unidad)": 3,
        "Bandeja (unidad)": 1,
        "Caja (unidad)": 1
    },
    "Alfajores de maicena (30 unidades)": {
        "Harina Leudante (kg)": 0.200,
        "Manteca (kg)": 0.100,
        "Azúcar impalpable (kg)": 0.100,
        "Maicena (kg)": 0.300,
        "Dulce de Leche (kg)": 0.250,
        "Huevo (unidad)": 2,
        "Esencia de vainilla (litro)": 0.005,
        "Coco rallado (kg)": 0.010,
        "Bolsa (unidad)": 30
    },
    "Budin de vainilla": {
            "Harina Leudante (kg)": 0.300,
            "Esencia de vainilla (litro)": 0.005,
            "Azúcar (kg)": 0.200,
            "Aceite (litro)": 0.100,
            "Huevo (unidad)": 2,
            "Leche (litro)": 0.175,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        },
    "Chipa": {
        "Huevo (unidad)": 3,
        "Preparado para Chipa (kg)": 0.400
    }
}

# --- INTERFAZ WEB ---

# Panel lateral: Permite actualizar precios si sube la inflación
st.sidebar.header("⚙️ Lista de Insumos")
precios_actuales = {}
for ingrediente, precio_base in INSUMOS.items():
    precios_actuales[ingrediente] = st.sidebar.number_input(
        f"Precio {ingrediente} ($):", 
        value=float(precio_base),
        step=100.0
    )

# Panel principal: Selección de producto
st.header("📋 Seleccionar Receta para Calcular")

receta_seleccionada = st.selectbox(
    "Elegí un producto del menú:", 
    list(RECETAS.keys())
)

precio_venta = st.number_input(
    f"Precio de venta al público para '{receta_seleccionada}' ($):", 
    value=15000, 
    step=500
)

# Botón para ejecutar los cálculos
if st.button("🚀 Calcular Costo y Ganancia"):
    ingredientes_receta = RECETAS[receta_seleccionada]
    costo_total = 0.0

    st.subheader("Desglose de Costos de la Receta:")
    
    # Bucle que calcula ingrediente por ingrediente
    for ingrediente, cantidad in ingredientes_receta.items():
        precio_unitario = precios_actuales[ingrediente]
        costo_ingrediente = cantidad * precio_unitario
        costo_total += costo_ingrediente
        st.write(f"• **{ingrediente}**: {cantidad} x ${precio_unitario:.2f} = **${costo_ingrediente:.2f}**")

    ganancia = precio_venta - costo_total
    margen = (ganancia / precio_venta) * 100 if precio_venta > 0 else 0

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Costo de Producción", f"${costo_total:.2f}")
    col2.metric("Ganancia Limpia", f"${ganancia:.2f}")
    col3.metric("Margen de Ganancia", f"{margen:.1f}%")
