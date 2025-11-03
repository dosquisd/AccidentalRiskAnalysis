import warnings
from datetime import date
from typing import TypedDict

import pandas as pd
import streamlit as st

from dashboard.custom_utils import (
    FREQUENCY_OPTIONS,
    filter_data_by_date_range,
    select_dates,
)
from utils.load_data import load_processed_original_data, resample_data

warnings.filterwarnings("ignore")


class LoadDataResult(TypedDict):
    processed_data: pd.DataFrame
    resampled_data: pd.DataFrame
    start_date: date
    end_date: date
    freq: str


def plot_all_historic_data(
    resampled_data: pd.DataFrame,
    accidents_col: str = "TOTAL_ACCIDENTES",
    *,
    ewm_alpha: float = 0.0,
    resample_freq_units: str = "weekly",
) -> None:
    resample_freq_units = resample_freq_units.capitalize()

    tmp_df = resampled_data.reset_index()
    y_axis = [accidents_col]
    color_axis = None

    if ewm_alpha > 0.0:
        if (
            st.session_state.lineplots_last_ewm_alpha_slider != ewm_alpha
            or st.session_state.lineplots_ewm_alpha_calcs is None
        ):
            tmp_df["ewm"] = tmp_df[y_axis].ewm(alpha=ewm_alpha).mean()
            st.session_state.lineplots_last_ewm_alpha_slider = ewm_alpha
            st.session_state.lineplots_ewm_alpha_calcs = tmp_df["ewm"].copy()
            print(f"Calculating EWM with alpha={ewm_alpha}")
        else:
            tmp_df["ewm"] = st.session_state.lineplots_ewm_alpha_calcs
            print(f"Using cached EWM with alpha={ewm_alpha}")

        y_axis = [accidents_col, "ewm"]
        color_axis = ["#00b7ffff", "#ff000089"]

    st.subheader(f"All Historic Data {resample_freq_units}")
    st.line_chart(
        tmp_df,
        x=resampled_data.index.name,
        y=y_axis,
        x_label="Date",
        y_label="Total Accidents",
        color=color_axis,
    )


def plot_locality_data(
    resampled_data: pd.DataFrame,
    localities: list[str],
    *,
    ewm_alpha: float = 0.0,
    resample_freq_units: str = "weekly",
    separate_charts: bool = False,
) -> None:
    """Shows data for selected localities."""
    resample_freq_units = resample_freq_units.capitalize()

    if separate_charts:
        # Show each locality in a separate chart
        for locality in localities:
            locality_col = f"LOCALIDAD-{locality.replace(' ', '_')}"
            if locality_col not in resampled_data.columns:
                st.warning(f"⚠️ No data found for locality: {locality}")
                continue

            tmp_df = resampled_data.reset_index()
            y_axis = [locality_col]
            color_axis = None

            if ewm_alpha > 0.0:
                ewm_key = f"ewm_{locality}"
                tmp_df[ewm_key] = (
                    tmp_df[locality_col].ewm(alpha=ewm_alpha).mean()
                )
                y_axis = [locality_col, ewm_key]
                color_axis = ["#00b7ffff", "#ff000089"]

            st.subheader(f"📍 {locality} - {resample_freq_units}")
            st.line_chart(
                tmp_df,
                x=resampled_data.index.name,
                y=y_axis,
                x_label="Date",
                y_label="Total Accidents",
                color=color_axis,
            )
    else:
        # Show all localities in a single chart
        tmp_df = resampled_data.reset_index()
        y_axis = []

        for locality in localities:
            locality_col = f"LOCALIDAD-{locality.replace(' ', '_')}"
            if locality_col in resampled_data.columns:
                y_axis.append(locality_col)
            else:
                st.warning(f"⚠️ No data found for locality: {locality}")

        if not y_axis:
            st.error("❌ No valid localities selected.")
            return

        st.subheader(
            f"📍 Selected Localities Comparison - {resample_freq_units}"
        )
        st.line_chart(
            tmp_df,
            x=resampled_data.index.name,
            y=y_axis,
            x_label="Date",
            y_label="Total Accidents",
        )


def show_all_historic_data(
    df: pd.DataFrame,
    resample_freq_units: str = "week",
) -> float:
    ewm_alpha = st.slider(
        label=r"EWM Alpha ($\alpha=0 \Rightarrow$ No EWM; $\alpha>0 \Rightarrow$ EWM Smoothing)",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.01,
        key="ewm_alpha_slider",
        on_change=lambda: st.session_state.update(
            {"lineplots_ewm_alpha_calcs": None}
        ),
    )

    # Total accidents chart
    st.markdown("## 📊 Total Accidents Overview")
    total_accidents_col = "TOTAL_ACCIDENTES"
    total_accidents_df = df[[total_accidents_col]]
    plot_all_historic_data(
        total_accidents_df,
        accidents_col=total_accidents_col,
        ewm_alpha=ewm_alpha,
        resample_freq_units=resample_freq_units,
    )

    return ewm_alpha


def show_locality_data(
    df: pd.DataFrame,
    resample_freq_units: str = "week",
    ewm_alpha: float = 0.0,
) -> None:
    # Localities section
    st.markdown("## 🏙️ Localities Analysis")

    # Get all available localities from column names
    locality_columns = [
        col for col in df.columns if col.startswith("LOCALIDAD-")
    ]
    available_localities = sorted(
        [
            col.replace("LOCALIDAD-", "").replace("_", " ")
            for col in locality_columns
        ]
    )

    if not available_localities:
        st.warning("⚠️ No locality data available in the resampled dataset.")
        return

    # Locality selection
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_localities = st.multiselect(
            label="Select Localities to Display:",
            options=available_localities,
            default=available_localities[:3]
            if len(available_localities) >= 3
            else available_localities,
            key="localities_multiselect",
        )

    with col2:
        separate_charts = st.checkbox(
            label="Separate Charts",
            value=False,
            key="separate_charts_checkbox",
            help="Show each locality in its own chart",
        )

    if not selected_localities:
        st.info("ℹ️ Please select at least one locality to display the chart.")
        return

    # Show selected localities
    plot_locality_data(
        df,
        selected_localities,
        ewm_alpha=ewm_alpha,
        resample_freq_units=resample_freq_units,
        separate_charts=separate_charts,
    )


def load_data() -> LoadDataResult | None:
    if (
        st.session_state.lineplots_processed_data_needs_update
        or st.session_state.lineplots_cached_processed_data is None
    ):
        processed_data = load_processed_original_data(
            as_geopandas=False,
            date_as_index=True,
            parse_dates=True,
        )
        st.session_state.lineplots_cached_processed_data = processed_data
        st.session_state.lineplots_processed_data_needs_update = False

        # Force EWM recalculation
        st.session_state.lineplots_last_ewm_alpha_slider = 0.0
        st.session_state.lineplots_ewm_alpha_calcs = None
        print("Recalculating processed data")
    else:
        processed_data = st.session_state.lineplots_cached_processed_data
        print("Using cached processed data")

    start_date, end_date = select_dates(
        processed_data,
        key_prefix="lineplots",
        show_total_days=True,
    ) or (None, None)

    if start_date is None or end_date is None:
        return None

    selected_frequency = st.selectbox(
        label="Select Resampling Frequency:",
        options=list(FREQUENCY_OPTIONS.keys()),
        index=1,
        key="resample_frequency_selectbox",
        on_change=lambda: st.session_state.update(
            {"lineplots_resampled_data_needs_update": True}
        ),
    )

    # Use cached data to avoid unnecessary recomputation
    if (
        st.session_state.lineplots_resampled_data_needs_update
        or st.session_state.lineplots_date_filter_changed
        or st.session_state.lineplots_cached_resampled_data is None
    ):
        # First filter by dates
        filtered_data = filter_data_by_date_range(
            processed_data, start_date, end_date
        )

        # Then resample the filtered data
        resampled_data = resample_data(
            df=filtered_data,
            freq=FREQUENCY_OPTIONS[selected_frequency],
            multi_index=False,
        )

        st.session_state.lineplots_cached_resampled_data = resampled_data
        st.session_state.lineplots_resampled_data_needs_update = False
        st.session_state.lineplots_date_filter_changed = False

        print(
            f"Recalculating data: {selected_frequency}, {start_date} to {end_date}"
        )
    else:
        resampled_data = st.session_state.lineplots_cached_resampled_data
        print(f"Using cached data: {selected_frequency}")

    # Check if there is data in the selected range
    if resampled_data.empty:
        st.warning(
            f"⚠️ No data available in the selected date range ({start_date} to {end_date})."
        )
        return None

    return {
        "processed_data": processed_data,
        "resampled_data": resampled_data,
        "start_date": start_date,
        "end_date": end_date,
        "freq": selected_frequency,
    }


def index(title: str = "LinePlots") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write an introduction text about what the users can find in this section.]
    """)

    # Initialize session state
    if "lineplots_processed_data_needs_update" not in st.session_state:
        st.session_state.lineplots_processed_data_needs_update = True
    if "lineplots_cached_processed_data" not in st.session_state:
        st.session_state.lineplots_cached_processed_data = None
    if "lineplots_resampled_data_needs_update" not in st.session_state:
        st.session_state.lineplots_resampled_data_needs_update = True
    if "lineplots_cached_resampled_data" not in st.session_state:
        st.session_state.lineplots_cached_resampled_data = None
    if "lineplots_date_filter_changed" not in st.session_state:
        st.session_state.lineplots_date_filter_changed = True
    if "lineplots_last_ewm_alpha_slider" not in st.session_state:
        st.session_state.lineplots_last_ewm_alpha_slider = 0.0
    if "lineplots_ewm_alpha_calcs" not in st.session_state:
        st.session_state.lineplots_ewm_alpha_calcs = None

    data_result = load_data()
    if data_result is None:
        return

    resampled_data = data_result["resampled_data"]
    freq = data_result["freq"]

    ewm_alpha = show_all_historic_data(resampled_data, freq)

    st.markdown(""" 
        ### ¿Cómo ha evolucionado la accidentalidad en Bogotá alrededor de los años 2007 y 2017?

        El análisis de las series temporales permite identificar patrones, picos y comportamientos estructurales en la accidentalidad de Bogotá durante el periodo 2007–2017. Los principales hallazgos son los siguientes:

        * Se observan picos y caídas recurrentes en los datos, especialmente:
            * Entre diciembre y enero, donde suele haber disminuciones marcadas (la más notable de diciembre 2008 a enero 2009).
            * Caídas adicionales ocurren entre los meses de marzo y mayo.

        * Después de cada caída, la serie muestra un aumento progresivo, lo que sugiere ciclos estacionales de descenso y recuperación.

        * A partir de 2010, la tendencia general muestra un incremento sostenido en el número de accidentes.

        * Entre 2007 y 2009, los niveles de accidentalidad mensual fueron altos.

        * En la vista trimestral, se observa:
            * Un salto inicial en 2007, pasando de 2.633 a 9.187 accidentes por trimestre.
            * Un descenso sostenido entre 2008 y 2010.

        * Entre 2011 y 2015 se presenta un periodo relativamente estable, con un aumento entre 2010 y 2013 y una disminución en la accidentalidad semanal entre 2013 y 2015.

        * A partir de 2015, se evidencia un incremento en la cantidad de accidentes.

        La caída observada al final de 2017 en todos los gráficos no refleja una disminución real, sino que se debe a que los datos disponibles llegan únicamente hasta el 29 de septiembre.
    """)

    st.markdown("---")

    show_locality_data(
        resampled_data,
        resample_freq_units=freq,
        ewm_alpha=ewm_alpha,
    )

    st.markdown("""
        ### ¿Cómo se compara la evolución entre localidades?

        * Varias localidades presentan un comportamiento muy similar al patrón global de Bogotá, entre estas se encuentran; Engativá, Suba, Fontibón, Usme, Ciudad Bolívar, Kennedy y Tunjuelito, sin embargo, algunas son en menor medida y ninguna es exactamente igual a la tendencia global.
        * Algunas presentan variaciones propias, aunque mantienen los hitos principales:
        * Teusaquillo: comparte la caída de 2009, pero después se mantiene relativamente constante.
        * Puente Aranda: muestra la caída, aunque menos pronunciada; presenta un aumento moderado hacia 2016.

        Entre las cuatro localidades con más accidentes (Engativá, Suba, Usaquén y Kennedy), al comparar sus series anuales, se observan similitudes, pero también diferencias:

        * Kennedy: inicia 2007 con niveles anormalmente altos; en vez de subir entre 2010 y 2013 (como Bogotá en general), presenta una disminución y luego un aumento después de 2013.
        * Usaquén: destaca por picos en 2008 y 2009 (también se observa la baja del 2009, pero afecta menos que en otras localidades). Presenta una baja después de 2015, a diferencia del aumento global.
        * Engativá y Suba: siguen más de cerca la tendencia global, con caídas en 2009 y un aumento progresivo hacia 2015–2016.

    """)

    st.markdown("---")

    st.markdown("""
        ### Conclusiones

        Aunque la accidentalidad en Bogotá no presenta una tendencia lineal clara, es posible dividir el periodo en varias etapas:  

        * La accidentalidad se mantiene elevada y relativamente constante durante el 2007 y 2008.  
        * Caída del año 2008 hacia el 2009.  
        * Subida desde el 2010 hasta el 2013.  
        * Disminución en la cantidad de accidentes del 2013 hasta el 2015.
        * Incremento en la cantidad de accidentes semanales desde el 2015 en adelante, que se interrumpe por el límite de datos en septiembre de 2017.

        Respecto a las localidades, aunque existe un patrón global compartido, cada localidad muestra dinámicas propias.
    """)


if __name__ == "__main__":
    title = "Temporal Evolution of Accidents"
    st.set_page_config(page_title=title, layout="wide")
    index(title)
