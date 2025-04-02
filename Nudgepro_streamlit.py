
# ============================================
# NudgePro - Fase 1 y 2: Carga, inspección y clasificación de perfiles optimizada
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="NudgePro", layout="wide")

# ====== Variables y configuraciones ======
CLASSIFICATION_LABELS = ["Novato", "Con experiencia", "Experto"]
REQUIRED_COLUMNS = {'edad', 'numero_de_creditos'}

COLUMN_MAPPING = {
    'nivel_expertis': 'nivel_expertis',
    'numero_de_credito': 'numero_de_creditos'
}

# ====== Estilo oscuro personalizado ======
st.markdown("""
<style>
    .main {
        background-color: #111;
        color: #EEE;
        padding: 1rem;
    }
    .stButton>button {
        border-radius: 12px;
        border: 1px solid #00FF7F;
        color: white;
        background: black;
    }
    .stRadio>div {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ====== Funciones ======
def clean_columns(df):
    df.columns = (
        df.columns.str.normalize('NFKD')
        .str.encode('ascii', 'ignore')
        .str.decode('utf-8')
        .str.strip()
        .str.replace(r'[^\w\s]', '', regex=True)
        .str.replace(r'\s+', '_', regex=True)
        .str.lower()
    )
    df = df.rename(columns=COLUMN_MAPPING)
    return df

def load_data(file, tipo):
    try:
        if tipo == 'CSV':
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error al leer archivo: {e}")
        return None

def classify_profiles(df):
    if not REQUIRED_COLUMNS.issubset(df.columns):
        missing = REQUIRED_COLUMNS - set(df.columns)
        raise ValueError(f"Columnas faltantes: {', '.join(missing)}")

    df['perfil_nudgepro'] = np.select(
        [
            (df['edad'] < 35) | (df['numero_de_creditos'] <= 2),
            df['edad'].between(35, 50) & df['numero_de_creditos'].between(3, 4),
            (df['edad'] > 50) & (df['numero_de_creditos'] >= 5)
        ],
        CLASSIFICATION_LABELS,
        default="No definido"
    )
    return df

# ====== Interfaz principal ======
st.title("📊 NudgePro – Análisis de Perfiles Empresariales")

tab1, tab2 = st.tabs(["📁 Carga y Visualización", "📈 Visualización Avanzada"])

with tab1:
    st.subheader("📤 Carga de archivo")
    tipo_archivo = st.radio("Selecciona el tipo de archivo:", ["CSV", "Excel"])
    archivo = st.file_uploader("Carga tu archivo de datos", type=['csv', 'xlsx'])

    df = None
    if archivo:
        with st.spinner("Procesando datos..."):
            df = load_data(archivo, tipo_archivo)
            if df is None: st.stop()

            df = clean_columns(df)

            missing_cols = REQUIRED_COLUMNS - set(df.columns)
            if missing_cols:
                st.error(f"Error de compatibilidad de columnas: {', '.join(missing_cols)}. Columnas detectadas: {', '.join(df.columns)}")
                st.stop()

            st.success("✅ Archivo cargado correctamente")
            st.subheader("👁 Vista previa")
            st.dataframe(df.head())

            st.subheader("📊 Estadísticas descriptivas")
            st.write(df.describe(include='all'))

            st.subheader("🧩 Columnas disponibles")
            st.write(list(df.columns))

            try:
                df = classify_profiles(df)
                st.subheader("🧠 Clasificación de Perfiles NudgePro")
                st.dataframe(df[['nombre_cliente', 'edad', 'numero_de_creditos', 'perfil_nudgepro']])
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

with tab2:
    if df is not None:
        st.subheader("📊 Distribución de perfiles")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig = px.pie(
                df,
                names='perfil_nudgepro',
                title="Distribución de Perfiles",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            selected_profile = st.selectbox(
                "Filtra por perfil:",
                options=["Todos"] + df['perfil_nudgepro'].unique().tolist()
            )

        with st.container():
            st.subheader("📉 Distribución por Edad")
            st.markdown("##### Relación entre edad de clientes y su perfil")

            df_filtered = df if selected_profile == "Todos" else df[df['perfil_nudgepro'] == selected_profile]
            fig_edad = px.histogram(
                df_filtered,
                x='edad',
                color='perfil_nudgepro',
                nbins=20,
                barmode='group',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                labels={'edad': 'Edad del cliente', 'perfil_nudgepro': 'Perfil'}
            )
            fig_edad.update_layout(height=400)
            fig_edad.update_traces(hovertemplate="<b>Edad</b>: %{x}<br><b>Cantidad</b>: %{y}")
            st.plotly_chart(fig_edad, use_container_width=True)
