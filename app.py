import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Dulce Mar - Sistema de Costos", 
    page_icon="🧁",
    layout="wide"
)

# Estilo visual en celeste pastel
st.markdown("""
    <style>
    .main {
        background-color: #f4f9f9;
    }
    h1, h2, h3 {
        color: #5c9ead !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stButton>button {
        background-color: #a8dadc;
        color: #1d3557;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #457b9d;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧁 Dulce Mar - Sistema de Costos y Recetas")

# 1. BASE DE DATOS DE INSUMOS
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
    "Limon (kg)": 1500,
    "Queso crema (kg)": 12000,
    "Esencia de vainilla (litro)": 22600,
    "Coco rallado (kg)": 43400,
    "Bolsa (unidad)": 32,
    "Bandeja (unidad)": 40,
    "Preparado para Chipa (kg)": 14975,
    "Banana (kg)": 3500,
    "Galletitas vainilla (kg)": 12000
}

# 2. BASE DE DATOS DE RECETAS (Con rinde, tipo y precios base)
RECETAS = {
    "Alfajores de maicena": {
        "rinde": 30,
        "tipo": "unidades",
        "precio_1u": 1250.0,
        "precio_6u": 7500.0,
        "precio_12u": 15000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.200,
            "Manteca (kg)": 0.100,
            "Azúcar impalpable (kg)": 0.100,
            "Maicena (kg)": 0.300,
            "Dulce de Leche (kg)": 0.250,
            "Huevo (unidad)": 2,
            "Esencia de vainilla (litro)": 0.005,
            "Coco rallado (kg)": 0.010,
            "Bolsa (unidad)": 30
        }
    },
    "Budin de chocolate/marmolado": {
        "rinde": 14,  # 14 porciones
        "tipo": "porciones",
        "precio_porcion": 1000.0,
        "precio_entero": 12000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.300,
            "Toddy cacao polvo (kg)": 0.050,
            "Azúcar (kg)": 0.200,
            "Aceite (litro)": 0.100,
            "Huevo (unidad)": 2,
            "Leche (litro)": 0.175,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        }
    },
    "Budin de vainilla": {
        "rinde": 14,  # 14 porciones
        "tipo": "porciones",
        "precio_porcion": 1000.0,
        "precio_entero": 12000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.300,
            "Esencia de vainilla (litro)": 0.005,
            "Azúcar (kg)": 0.200,
            "Aceite (litro)": 0.100,
            "Huevo (unidad)": 2,
            "Leche (litro)": 0.175,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        }
    },
    "Budin de limón": {
        "rinde": 14,  # 14 porciones
        "tipo": "porciones",
        "precio_porcion": 1000.0,
        "precio_entero": 12000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.260,
            "Limon (kg)": 0.150,
            "Azúcar (kg)": 0.200,
            "Aceite (litro)": 0.120,
            "Huevo (unidad)": 3,
            "Leche (litro)": 0.175,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        } 
    },
    "Budin de Naranja": {
        "rinde": 14,  # 14 porciones
        "tipo": "porciones",
        "precio_porcion": 1000.0,
        "precio_entero": 12000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.260,
            "Naranja (kg)": 0.130,
            "Azúcar (kg)": 0.200,
            "Aceite (litro)": 0.120,
            "Huevo (unidad)": 3,
            "Leche (litro)": 0.175,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        }
    },
    "Budin de banana": {
        "rinde": 10,  # 10 porciones
        "tipo": "porciones",
        "precio_porcion": 1000.0,
        "precio_entero": 10000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.150,
            "Banana (kg)": 0.200,
            "Azúcar (kg)": 0.180,
            "Aceite (litro)": 0.060,
            "Huevo (unidad)": 2,
            "Esencia de vainilla (litro)": 0.005,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        }
    },
    "Lemonies": {
        "rinde": 4,  # 4 porciones
        "tipo": "porciones",
        "precio_porcion": 5000.0,
        "precio_entero": 20000.0,
        "ingredientes": {
            "Harina Leudante (kg)": 0.140,
            "Limon (kg)": 0.150,
            "Azúcar (kg)": 0.155,
            "Manteca (kg)": 0.100,
            "Huevo (unidad)": 3,
            "Azucar impalpable (kg)": 0.100,
            "Bolsa (unidad)": 1,
            "Bandeja (unidad)": 2
        }
    },
    "Chessecake": {
        "rinde": 1,
        "tipo": "entero",
        "precio_entero": 45000.0,
        "ingredientes": {
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
        }
    },
    "Chipa": {
        "rinde": 30, # 30 unidades
        "tipo": "unidades",
        "precio_6u": 5000.0,
        "precio_12u": 10000.0,
        "ingredientes": {
            "Huevo (unidad)": 3,
            "Preparado para Chipa (kg)": 0.400
        }
    }
}

# --- INTERFAZ WEB ---

# Panel lateral: Insumos
st.sidebar.header("🎨 Precios de Insumos")
precios_actuales = {}
for ingrediente, precio_base in INSUMOS.items():
    precios_actuales[ingrediente] = st.sidebar.number_input(
        f"Precio {ingrediente} ($):", 
        value=float(precio_base),
        step=100.0
    )

# Panel principal
st.header("📋 Selección de Producto y Análisis")

receta_seleccionada = st.selectbox(
    "Elegí un producto del menú:", 
    list(RECETAS.keys())
)

datos = RECETAS[receta_seleccionada]
rinde = datos["rinde"]
tipo = datos["tipo"]
ingredientes = datos["ingredientes"]

# Cálculo del costo total del lote y por unidad/porción
costo_lote = 0.0
for ing, cant in ingredientes.items():
    costo_lote += cant * precios_actuales.get(ing, 0.0)

costo_unidad = costo_lote / rinde

# Métricas rápidas
col_a, col_b = st.columns(2)
col_a.metric("Costo Total del Lote/Receta", f"${costo_lote:,.2f}")
if rinde > 1:
    col_b.metric(f"Costo por Porción/Unidad ({rinde} u. totales)", f"${costo_unidad:,.2f}")

st.markdown("---")

# Muestra inteligente según el tipo de producto
if tipo == "unidades":
    st.subheader("💡 Precios de Venta por Cantidad")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 1 Unidad")
        p1 = st.number_input("Precio 1u ($):", value=datos["precio_1u"], step=100.0, key="p1")
        g1 = p1 - costo_unidad
        m1 = (g1 / p1) * 100 if p1 > 0 else 0
        st.write(f"• Costo: **${costo_unidad:,.2f}**")
        st.write(f"• Ganancia: **${g1:,.2f}** ({m1:.1f}%)")
        
    with c2:
        st.markdown("### Media Docena (6 u.)")
        p6 = st.number_input("Precio 6u ($):", value=datos["precio_6u"], step=200.0, key="p6")
        c6 = costo_unidad * 6
        g6 = p6 - c6
        m6 = (g6 / p6) * 100 if p6 > 0 else 0
        st.write(f"• Costo: **${c6:,.2f}**")
        st.write(f"• Ganancia: **${g6:,.2f}** ({m6:.1f}%)")

    with c3:
        st.markdown("### Docena (12 u.)")
        p12 = st.number_input("Precio 12u ($):", value=datos["precio_12u"], step=500.0, key="p12")
        c12 = costo_unidad * 12
        g12 = p12 - c12
        m12 = (g12 / p12) * 100 if p12 > 0 else 0
        st.write(f"• Costo: **${c12:,.2f}**")
        st.write(f"• Ganancia: **${g12:,.2f}** ({m12:.1f}%)")

elif tipo == "porciones":
    st.subheader("💡 Precios de Venta (Porción vs Entero)")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Porción Individual")
        p_porc = st.number_input("Precio Porción ($):", value=datos["precio_porcion"], step=100.0, key="pporc")
        g_porc = p_porc - costo_unidad
        m_porc = (g_porc / p_porc) * 100 if p_porc > 0 else 0
        st.write(f"• Costo x Porción: **${costo_unidad:,.2f}**")
        st.write(f"• Ganancia: **${g_porc:,.2f}** ({m_porc:.1f}%)")

    with col2:
        st.markdown(f"### Entero ({rinde} porciones)")
        p_entero = st.number_input("Precio Entero ($):", value=datos["precio_entero"], step=500.0, key="pentero")
        g_entero = p_entero - costo_lote
        m_entero = (g_entero / p_entero) * 100 if p_entero > 0 else 0
        st.write(f"• Costo Lote: **${costo_lote:,.2f}**")
        st.write(f"• Ganancia: **${g_entero:,.2f}** ({m_entero:.1f}%)")

else:
    st.subheader("💡 Precio de Venta Producto Entero")
    p_entero = st.number_input("Precio Venta ($):", value=datos["precio_entero"], step=500.0, key="púnico")
    g_entero = p_entero - costo_lote
    m_entero = (g_entero / p_entero) * 100 if p_entero > 0 else 0
    
    st.write(f"• Costo Lote: **${costo_lote:,.2f}**")
    st.write(f"• Ganancia Limpia: **${g_entero:,.2f}** ({m_entero:.1f}%)")

# Desglose de ingredientes
with st.expander("🔍 Ver desglose de ingredientes de esta receta"):
    for ing, cant in ingredientes.items():
        p_unit = precios_actuales.get(ing, 0.0)
        st.write(f"• **{ing}**: {cant} x ${p_unit:,.2f} = **${cant * p_unit:,.2f}**")
