import streamlit as st

from dashboard.data import download_button_data, load_data_preview
from utils import configure_scienceplots

# This raise an exception if LaTeX is not installed
try:
    configure_scienceplots()
except Exception:
    pass


def index(title: str = "Context and Data") -> None:
    st.markdown(f"# {title}")

    st.markdown("""
        ## Propósito del Proyecto

        Este Dashboard interactivo ha sido creado como parte del proyecto de **Análisis Exploratorio de Patrones de Accidentalidad Vial en Bogotá**, enfocado en la aplicación de técnicas de Ciencia de Datos para un problema de impacto urbano.

        Nuestro objetivo principal es:
        1.  **Comprender** cómo se distribuyen los accidentes de tránsito espacial y temporalmente en las 20 localidades de Bogotá.
        2.  **Identificar** patrones, ciclos y correlaciones que permitan determinar dónde, cuándo y por qué ocurren los siniestros más graves.
        3.  **Aportar** evidencia clara y visual para la planificación de estrategias de seguridad vial más focalizadas y eficientes.

        A lo largo de las siguientes páginas, usted podrá navegar por los resultados clave del análisis, incluyendo la evolución temporal, la distribución por gravedad y las matrices de correlación entre localidades.

        ---

        ## 💾 Origen de la Información

        La solidez de este análisis se basa en datos públicos y abiertos.

        La fuente de información corresponde al conjunto de datos abiertos **Movilidata Bogotá**, disponible en el portal **Datos Abiertos Opendatasoft**.

        [Accidente de Tráfico en Bogotá entre 2007 y 2017 (Geopoint)](https://transport.opendatasoft.com/explore/dataset/accidente-de-trafico-en-bogota-entre-2007-y-2017-geopoint/table/)

        ### 📝 Características del Dataset

        El análisis se basa en el periodo comprendido entre **2007 y 2017**, procesando un volumen inicial de **más de 330.000 registros** de siniestros viales.

        Las variables clave utilizadas para la exploración y visualización son:
        * `FECHA_OCURRENCIA`: Fecha y hora exacta del evento, esencial para el análisis de ciclos.
        * `LOCALIDAD` y Coordenadas: Permiten el análisis de distribución espacial.
        * `CLASE`: Tipología del accidente (**Choque, Atropello, Volcamiento**, etc.).
        * `GRAVEDAD`: Clasificación del impacto (**Solo Daños, Heridos, Muertos**), crucial para priorizar zonas de riesgo.

        ---
                
        ## ⚙️ Proceso Metodológico
                
        El proceso metodológico se centró en la limpieza y estandarización del dataset para obtener la versión "Processed Data" que alimenta este Dashboard.

        Las etapas clave de procesamiento fueron:
        1.  **Limpieza de Datos:** Eliminación de registros nulos o inconsistentes.
        2.  **Ingeniería de Características Geográficas y Temporales:** Descomposición de variables geográficas y temporales, y generación de variables derivadas (hora del día, fin de semana, temporada).
        3.  **Codificación:** Codificación numérica de variables categóricas (`CLASE_code`, `GRAVEDAD_code`) para facilitar análisis cuantitativos.
        4.  **Agrupamiento y Correlación:** Preparación de los datos para el análisis de correlación entre localidades mediante matrices de Pearson.

        ---

        ## 🔍 Previsualización de los Datos
        Para garantizar la transparencia, a continuación se presentan muestras del dataset en su estado original (Crudo) y después del proceso de limpieza y transformación (Procesado). El proceso incluyó la eliminación de nulos, la codificación de variables categóricas y la creación de características temporales.
    """)

    col1, col2 = st.columns([2, 2])

    with col1:
        # Show raw data preview
        st.subheader("Raw Data Preview")
        raw_df = load_data_preview(raw=True)
        st.dataframe(raw_df)
        download_button_data(
            raw_df,
            label="Download Raw Data as CSV",
            filename="raw_accident_data.csv",
        )

    with col2:
        # Show processed data preview
        st.subheader("Processed Data Preview")
        processed_df = load_data_preview(raw=False)
        st.dataframe(processed_df)
        download_button_data(
            processed_df,
            label="Download Processed Data as CSV",
            filename="processed_accident_data.csv",
        )


if __name__ == "__main__":
    title = "📊 Contexto y Fuente de Datos"
    st.set_page_config(page_title=title, layout="wide")
    index(title)
