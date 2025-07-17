import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import pygwalker as pyg
import streamlit.components.v1 as components
from io import BytesIO

st.set_page_config(page_title="Dashboard Proyecto Final", layout="wide")
st.title("¿Dónde van los recursos?: Análisis de compras municipales 2018 - 2019")

@st.cache_data
def cargar_datos(archivo):
    return pd.read_csv(archivo)

df = cargar_datos("df_total_muestra.csv")
st.write("Vista previa de los datos:")
st.dataframe(df.head())

st.sidebar.header("Filtros del Panel")

regiones_opciones = ["Todos"] + sorted(df["RegionUnidadCompra"].dropna().unique())
region_seleccionada = st.sidebar.selectbox("Región", regiones_opciones)
municipalidades_opciones = ["Todos"] + sorted(df["Institucion"].dropna().unique())
municipalidad_seleccionada = st.sidebar.selectbox("Municipalidades", municipalidades_opciones)
df["MontoNetoItem"] = pd.to_numeric(df["MontoNetoItem"], errors="coerce")
df = df.dropna(subset=["MontoNetoItem"])
min_monto = int(df["MontoNetoItem"].min())
max_monto = int(df["MontoNetoItem"].max())
rango_monto = st.sidebar.slider(
    "Rango de Monto Neto Item",
    min_monto,
    max_monto,
    (min_monto, max_monto)
)

df_filtrado = df.copy()

if region_seleccionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado["RegionUnidadCompra"] == region_seleccionada]
if municipalidad_seleccionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Institucion"] == municipalidad_seleccionada]
df_filtrado = df_filtrado[
    df_filtrado["MontoNetoItem"].between(rango_monto[0], rango_monto[1])
]


menu = st.selectbox("Selecciona una sección", ["Elige un Menú","Análisis General", "Exploración con PyGWalker"])

if menu == "Análisis General":
    col1, col2, col3 = st.columns(3)
    
    total_oc = df_filtrado["codigoOC"].nunique()
    total_proveedores = df_filtrado["Proveedor"].nunique()
    monto_total = df_filtrado["MontoNetoItem"].sum()
    
    col1.metric("Órdenes de Compra", total_oc)
    col2.metric("Proveedores", total_proveedores)
    col3.metric("Monto Neto Total", f"${monto_total:,.0f}")

    st.subheader("🏛️ Instituciones con Mayor Gasto (Monto Neto Item)")
    top_instituciones = (
      df_filtrado.groupby("Institucion")["MontoNetoItem"]
      .sum()
      .sort_values(ascending=False)
      .head(10)  # Las 10 con mayor gasto
      .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_instituciones, x="MontoNetoItem", y="Institucion", palette="viridis", ax=ax)
    ax.set_title("Top 10 Instituciones por Monto Neto Gastado")
    ax.set_xlabel("Monto Neto Total")
    ax.set_ylabel("Institución")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

    st.subheader("Órdenes por Región y Tamaño de Proveedor")

    fig2 = px.histogram(
      df_filtrado,
      x="RegionUnidadCompra",
      color="TamanoProveedor",
      barmode="group",
      histfunc="count",
      facet_col="MonedaItem",
      labels={"RegionUnidadCompra": "Región", "TamanoProveedor": "Tamaño Proveedor"}
    )

    st.plotly_chart(fig2, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["📋 Tabla", "📊 Gráficos", "📈 Estadísticas"])

    with tab1:
      st.dataframe(df_filtrado)

    with tab2:
      fig3 = px.violin(
         df_filtrado,
         y="MontoNetoItem",
         x="TamanoProveedor",
         color="MonedaItem",
         box=True,
         points="all")
      
      st.plotly_chart(fig3, use_container_width=True)

    with tab3:
      st.write("📊 Estadísticas descriptivas:")
      st.dataframe(df_filtrado.describe())

    with st.expander("ℹ️ ¿Qué significa cada columna?"):
      st.markdown("""
      - `codigoOC`: Código de la orden de compra.
      - `RegionUnidadCompra`: Región de la unidad compradora.
      - `Institucion`: Municipalidad u organismo comprador.
      - `Proveedor`: Nombre del proveedor adjudicado.
      - `TamanoProveedor`: Clasificación de tamaño del proveedor.
      - `MontoNetoItem`: Monto neto del ítem sin impuestos.
      - `MonedaItem`: Moneda utilizada en la compra.
      - `CantidadItem`: Cantidad adquirida del ítem.
      """)

    with st.form("formulario_feedback"):
      st.subheader("🗣️ Feedback del usuario")

      nombre = st.text_input("Tu nombre")
      comentario = st.text_area("¿Qué te pareció el dashboard?")
      puntaje = st.slider("Puntaje de satisfacción:", 1, 10, 5)

      enviar = st.form_submit_button("Enviar")

      if enviar:
        st.success(f"¡Gracias {nombre}! Calificaste el dashboard con un {puntaje}/10.")  
    
    def convertir_a_excel(df):
      output = BytesIO()
      with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="OrdenesCompra")
      return output.getvalue()

    st.download_button(
      label="📥 Descargar datos filtrados (Excel)",
      data=convertir_a_excel(df_filtrado),
      file_name="ordenes_compra_filtradas.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )    

elif menu == "Exploración con PyGWalker":
    st.subheader("🧭 PyGWalker - Exploración Visual")

    tab_pyg1, tab_pyg2 = st.tabs(["⚙️ PyGWalker dinámico", "📁 Cargar JSON de PyGWalker"])

    with tab_pyg1:
        try:
            generated_html = pyg.to_html(df_filtrado, return_html=True, dark='light')
            st.subheader("⚙️ Exploración Dinámica con PyGWalker")
            components.html(generated_html, height=800, scrolling=True)
        except Exception as e:
            st.error(f"Error al cargar PyGWalker dinámico: {e}")

    with tab_pyg2:
        st.subheader("📁 Subir archivo JSON de PyGWalker")
        uploaded_file = st.file_uploader("Selecciona un archivo .json exportado desde PyGWalker", type="json")

        if uploaded_file is not None:
            try:
                json_content = uploaded_file.read().decode("utf-8")
                generated_html_json = pyg.to_html(df_filtrado, return_html=True, dark='light', spec=json_content)
                st.subheader("⚙️ Carga gráfica a PyGWalker desde JSON")
                components.html(generated_html_json, height=800, scrolling=True)
            except Exception as e:
                st.error(f"Error al cargar el archivo JSON: {e}")

else:
    st.write("Selecciona una sección del menú para comenzar.")

st.sidebar.markdown("---")
st.sidebar.markdown("Creado por: **Katherine Morales; Claudia Vargas ; Paulina Vergara**")
st.sidebar.markdown("Ingeniería en Información y Control de Gestión - Business Intelligence")
st.sidebar.markdown("📧 contacto: contacto@alumnos.santotomas.cl")

