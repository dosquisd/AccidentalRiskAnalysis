from typing import Dict, Optional, TypedDict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from dashboard.custom_utils import (
    DAY_OF_WEEK_MAP,
    FREQUENCY_OPTIONS,
    transform_resample_data_for_boxplot,
)
from utils.load_data import load_processed_original_data, resample_data


class LoadDataResult(TypedDict):
    processed_data: pd.DataFrame
    resampled_data: pd.DataFrame
    freq: str


def load_data() -> LoadDataResult | None:
    if (
        st.session_state.boxplots_processed_data_needs_update
        or st.session_state.boxplots_cached_processed_data is None
    ):
        processed_data = load_processed_original_data(
            as_geopandas=False,
            date_as_index=True,
            parse_dates=True,
        )

        processed_data["DIA_SEMANA_OCURRENCIA"] = processed_data[
            "DIA_SEMANA_OCURRENCIA"
        ].map(DAY_OF_WEEK_MAP)

        processed_data["HORA"] = processed_data.index.hour

        st.session_state.boxplots_cached_processed_data = processed_data
        st.session_state.boxplots_processed_data_needs_update = False
    else:
        processed_data = st.session_state.boxplots_cached_processed_data

    selected_frequency = st.selectbox(
        label="Select Resampling Frequency:",
        options=list(FREQUENCY_OPTIONS.keys()),
        index=1,
        key="resample_frequency_selectbox",
        on_change=lambda: st.session_state.update(
            {"boxplots_resample_data_needs_update": True}
        ),
    )

    if (
        st.session_state.boxplots_resample_data_needs_update
        or st.session_state.boxplots_cached_resampled_data is None
    ):
        resampled_data = resample_data(
            freq=FREQUENCY_OPTIONS[selected_frequency],
            multi_index=True,
            day_of_week_map=DAY_OF_WEEK_MAP,
        )

        st.session_state.boxplots_cached_resampled_data = resampled_data
        st.session_state.boxplots_resample_data_needs_update = False
        st.session_state.boxplots_transformed_data_needs_update = True
        st.session_state.boxplots_cached_transformed_data = None
    else:
        resampled_data = st.session_state.boxplots_cached_resampled_data

    if resampled_data.empty:
        st.info("No data available for the selected date range and frequency.")
        return None

    return {
        "processed_data": processed_data,
        "resampled_data": resampled_data,
        "freq": selected_frequency,
    }


def show_boxplot(
    df: pd.DataFrame,
    metric: Optional[str] = None,
    labels_kwargs: Dict[str, str] = None,
    y: Optional[str] = None,
    palette: Optional[str] = None,
    show_violin: bool = False,
    show_points: bool = False,
    parse_metric: bool = True,
    sort_metrics: bool = False,
    ascending_order: bool = True,
) -> None:
    if not y:
        y = "value"

    if labels_kwargs is None:
        labels_kwargs = {}

    if not palette:
        palette = "Set2"

    if parse_metric and metric:
        df[metric] = df[metric].apply(
            lambda x: x.strip().replace("_", " ").title()
        )

    metric_order = None
    if sort_metrics and metric:
        metric_order = (
            df.groupby(metric)[y]
            .median()
            .sort_values(ascending=ascending_order)
            .index.tolist()
        )

    palette = sns.color_palette(palette)
    fig, ax = plt.subplots(figsize=(10, 6))

    if show_violin:
        sns.violinplot(
            data=df,
            x=metric,
            y=y,
            ax=ax,
            inner=None,
            palette=palette,
            linewidth=0.5,
            alpha=0.3,
            order=metric_order,
        )

    if show_points:
        sns.stripplot(
            data=df,
            x=metric,
            y=y,
            color="black",
            alpha=0.4,
            jitter=True,
            ax=ax,
            order=metric_order,
        )

    sns.boxplot(
        data=df,
        x=metric,
        y=y,
        ax=ax,
        width=0.3,
        palette=palette,
        order=metric_order,
    )
    ax.set(**labels_kwargs)
    ax.grid(True, linestyle="--", alpha=0.6)

    xticks_labels = ax.get_xticklabels()
    n_labels = len(xticks_labels)
    rotation = 15
    ha = "center"
    if n_labels < 4:
        rotation = 0
    elif n_labels < 10:
        if all(len(label.get_text()) < 10 for label in xticks_labels):
            rotation = 0
    else:
        rotation = 45
        ha = "right"

    ax.set_xticklabels(xticks_labels, rotation=rotation, ha=ha)

    st.pyplot(fig)

    fig.clf()
    plt.close(fig)


def show_distrubution_over_time(
    df: pd.DataFrame,
    selected_frequency: str,
    columns_options: list[str],
) -> None:
    st.markdown("## Distribution of Accidents Over Time")

    selected_metric = st.selectbox(
        label="Select Metric for Box Plot:",
        options=columns_options,
        index=0,
        key="boxplots_metric_selectbox",
        on_change=lambda: st.session_state.update(
            {"boxplots_transformed_data_needs_update": True}
        ),
    )

    if (
        st.session_state.boxplots_transformed_data_needs_update
        or st.session_state.boxplots_cached_transformed_data is None
    ):
        transformed_data = transform_resample_data_for_boxplot(
            df=df,
            col=selected_metric,
            multi_index=True,
        )

        st.session_state.boxplots_transformed_data_needs_update = False
        st.session_state.boxplots_cached_transformed_data = transformed_data
    else:
        transformed_data = st.session_state.boxplots_cached_transformed_data

    col1, col2 = st.columns([2, 2])
    with col1:
        show_violin = st.checkbox(
            label="Show Violin Plot",
            value=False,
            key="distribution_boxplots_show_violin_checkbox",
        )

        sort_metrics = st.checkbox(
            label="Sort Categories by Median",
            value=False,
            key="distribution_boxplots_sort_metrics_checkbox",
        )

    with col2:
        show_points = st.checkbox(
            label="Show Data Points",
            value=False,
            key="distribution_boxplots_show_points_checkbox",
        )

        ascending_order = st.checkbox(
            label="Ascending Order (only if sorting)",
            value=False,
            disabled=not sort_metrics,
            key="distribution_boxplots_ascending_order_checkbox",
        )

    show_boxplot(
        df=transformed_data,
        metric=selected_metric,
        labels_kwargs={
            "title": f"Box Plot of {selected_metric} ({selected_frequency})",
            "xlabel": "",
            "ylabel": "",
        },
        y="value",
        palette="Set2",
        show_violin=show_violin,
        show_points=show_points,
        parse_metric=True,
        sort_metrics=sort_metrics,
        ascending_order=ascending_order,
    )

    st.markdown("""
        ### 🔎 Interpretación de la Distribución

        El análisis estadístico revela patrones estructurales dependiendo de la métrica seleccionada:

        * **Por CLASE:** La categoría **"Choque"** domina de manera clara y consistente, con una mediana y rango mucho mayores al resto. Esto indica que es la problemática estructural principal. "Atropello" ocupa un segundo lugar distante. La distribución es altamente asimétrica: unas pocas clases explican la mayor parte de la accidentalidad.
        * **Por DÍA DE SEMANA:** Se observa un patrón cíclico claro. Los accidentes aumentan progresivamente desde el lunes, alcanzando su pico máximo entre **viernes y sábado**. El domingo presenta una caída marcada, asociada a la disminución de la movilidad laboral.
        * **Por GRAVEDAD:** Predominan los eventos de "Solo Daños". Sin embargo, los accidentes con **heridos y muertos** muestran alta persistencia y aumentan proporcionalmente los fines de semana, evidenciando que menor tráfico (domingos) no implica menor riesgo de severidad.
        * **Por LOCALIDAD:** La distribución es estructuralmente desigual. Localidades como **Kennedy, Engativá y Suba** concentran consistentemente la mayor cantidad de eventos (medianas altas), mientras que zonas como La Candelaria se mantienen en niveles bajos.
    """)


def compare_boxplots_between_hours(
    df: pd.DataFrame,
    columns_options: list[str],
) -> None:
    st.markdown("## Variable vs Hour of Day")

    selected_metric = st.selectbox(
        label="Select Metric for Box Plot:",
        options=columns_options,
        index=0,
    )

    if selected_metric == "TOTAL_ACCIDENTES":
        selected_metric = None

    col1, col2 = st.columns([2, 2])

    with col1:
        show_violin = st.checkbox(
            label="Show Violin Plot",
            value=False,
            key="hours_boxplots_show_violin_checkbox",
        )

    with col2:
        sort_metrics = st.checkbox(
            label="Sort Categories by Median",
            value=False,
            key="hours_boxplots_sort_metrics_checkbox",
        )

        ascending_order = st.checkbox(
            label="Ascending Order (only if sorting)",
            value=False,
            disabled=not sort_metrics,
            key="hours_boxplots_ascending_order_checkbox",
        )

    show_boxplot(
        df=df,
        metric=selected_metric,
        labels_kwargs={
            "title": "Box Plot of Variables vs Hour of Day",
            "ylabel": "Hour of Day",
            "xlabel": "",
            "yticks": range(0, 24 + 1, 3),
        },
        y="HORA",
        palette="Set2",
        show_violin=show_violin,
        show_points=False,
        parse_metric=True,
        sort_metrics=sort_metrics,
        ascending_order=ascending_order,
    )

    st.markdown("""
        ### ⏰ Análisis Horario

        Al cruzar las variables con la hora del día, surgen patrones de comportamiento vinculados a la actividad ciudadana:

        * **Concentración Diurna:** La mayoría de las clases de accidentes (especialmente choques y atropellos) se concentran entre las **9:00 a.m. y las 6:00 p.m.**, coincidiendo con los flujos de movilidad laboral y escolar.
        * **Riesgo Nocturno (Fatalidad):** Existe una excepción crítica en la gravedad. Mientras que los heridos tienen un comportamiento bimodal (picos mañana/tarde), los **accidentes fatales** tienden a concentrarse en horarios nocturnos (**10:00 p.m. a 3:00 a.m.**), lo que sugiere factores de riesgo distintos como velocidad o conducción bajo efectos del alcohol.
    """)


def index(title: str = "Distribution over time") -> None:
    st.markdown(f"# {title}")
    st.markdown("""
        ## 📊 Análisis de Distribución y Variabilidad

        ### ¿Qué nos dicen los diagramas de caja?

        Esta sección profundiza en la **estadística descriptiva** de los accidentes. A diferencia de los gráficos de línea que muestran tendencias, los **Boxplots (Diagramas de Caja)** nos permiten entender:
        
        1.  **Centralidad:** ¿Cuál es el número mediano de accidentes?
        2.  **Dispersión:** ¿Qué tanta variabilidad existe (días tranquilos vs. días caóticos)?
        3.  **Valores Atípicos (Outliers):** Detección de eventos extremos que se salen de la norma estadística.
    """)

    # Initialize session state
    if "boxplots_processed_data_needs_update" not in st.session_state:
        st.session_state.boxplots_processed_data_needs_update = True
    if "boxplots_cached_processed_data" not in st.session_state:
        st.session_state.boxplots_cached_processed_data = None
    if "boxplots_resample_data_needs_update" not in st.session_state:
        st.session_state.boxplots_resample_data_needs_update = True
    if "boxplots_cached_resampled_data" not in st.session_state:
        st.session_state.boxplots_cached_resampled_data = None
    if "boxplots_date_filter_changed" not in st.session_state:
        st.session_state.boxplots_date_filter_changed = True
    if "boxplots_transformed_data_needs_update" not in st.session_state:
        st.session_state.boxplots_transformed_data_needs_update = True
    if "boxplots_cached_transformed_data" not in st.session_state:
        st.session_state.boxplots_cached_transformed_data = None

    load_data_result = load_data()
    if load_data_result is None:
        return None

    processed_data = load_data_result["processed_data"]
    resampled_data = load_data_result["resampled_data"]
    selected_frequency = load_data_result["freq"]

    columns_options = list(
        set(map(lambda item: item[0], resampled_data.columns.tolist()))
    )

    show_distrubution_over_time(
        resampled_data,
        selected_frequency,
        columns_options,
    )

    st.markdown("---")

    compare_boxplots_between_hours(processed_data, columns_options)


if __name__ == "__main__":
    title = "Distribution over time"
    st.set_page_config(page_title=title, layout="centered")
    index(title=title)
